"""端到端 + 单元验证脚本（配合 scripts/mock_llm.py）。

用法：python scripts/verify.py（WB_BASE 环境变量可改目标端口）
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

import httpx

BASE = os.getenv("WB_BASE", "http://127.0.0.1:4830")
ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "data" / "config.json"
# mock 网关（OpenAI 兼容）：verify 期间把 default provider 的 base_url 指过去，跑完还原
MOCK_ORIGIN = os.getenv("WB_MOCK_ORIGIN", "http://127.0.0.1:4831")
MOCK_GATEWAY = MOCK_ORIGIN + "/v1"

RESULTS: list[tuple[bool, str, str]] = []
# main() 切 mock 前写入；__main__ 的 finally 据此恢复（None = 未切换，恢复为 no-op）
_SNAPSHOT: dict | None = None
# main() 跑前抓取的既有记录 id 基线；finally 据此识别「本轮新增」的测试痕迹并清扫
_BASELINE: dict | None = None

# mock 按模型名分流角色（mock-planner/mock-executor/mock-evaluator/mock-memory）
MOCK_SETTINGS = {
    "base_url": MOCK_GATEWAY,
    "model": "mock-executor",
    "roles": {
        "planner": {"provider": "default", "model": "mock-planner"},
        "executor": {"provider": "default", "model": "mock-executor"},
        "evaluator": {"provider": "default", "model": "mock-evaluator"},
        "memory": {"provider": "default", "model": "mock-memory"},
    },
    "workflow_mode": "auto",
    "evaluator_enabled": True,
    "memory_enabled": True,
}
# 切 mock 只会改动这些角色；恢复时还原它们即可精确逆转（其余角色/字段未被动过）
_MOCK_ROLES = ("planner", "executor", "evaluator", "memory")


def snapshot_settings() -> dict | None:
    """快照当前生效配置：直接读 config.json，拿到未经解析的原始 llm/roles/workflow 等。

    GET /api/settings 返回的是解析后的角色（model 已回退、空值显示为「(未配置)」），
    无法据此精确还原，故以磁盘原文为准。
    """
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"WARN  快照 config.json 失败，本次将跳过自动恢复：{e}")
        return None


def restore_settings(snap: dict | None) -> None:
    """把切 mock 改动的字段精确还原。

    走 PUT 而非直接写文件：save_config 会同步刷新服务端进程内缓存，无需重启即生效。
    """
    if snap is None:
        return
    llm = snap.get("llm") or {}
    roles = snap.get("roles") or {}
    payload = {
        "base_url": llm.get("base_url", ""),
        "model": llm.get("model", ""),
        "roles": {
            r: {
                "provider": (roles.get(r) or {}).get("provider", "default"),
                "model": (roles.get(r) or {}).get("model", ""),
            }
            for r in _MOCK_ROLES
        },
        "workflow_mode": (snap.get("workflow") or {}).get("mode", "auto"),
        "evaluator_enabled": (snap.get("evaluator") or {}).get("enabled", True),
        "memory_enabled": (snap.get("memory") or {}).get("enabled", True),
    }
    try:
        r = httpx.put(f"{BASE}/api/settings", json=payload, timeout=10)
        r.raise_for_status()
        print("INFO  已恢复原 settings（base_url/model/roles/workflow/evaluator/memory）")
    except Exception as e:  # noqa: BLE001
        print(f"WARN  恢复 settings 失败，请手动核对 data/config.json：{e}")


# ── 测试残留自清扫 ─────────────────────────────────────────────
# verify 跑在 live 服务上，会在 data/ 留下：verify 会话、task_runner 派生的 [自动] 会话
# （S5 任务执行 / S12 自动化执行）、mock 页面、hello.txt 自动归档页、mock 提醒任务、mock 记忆。
# 收尾按「基线后新增」删除：会话/记忆全删新增（task_runner 派生会话与 auto-extract 文案不可枚举），
# 页面/任务额外要求 mock 标识，避免误删运行期间用户并发产生的真实页面/任务。
_MOCK_PAGE_TITLES = {"mock 页面"}
_MOCK_PAGE_SOURCES = {"workspace:hello.txt"}
_MOCK_JOB_TITLE_PREFIX = "mock"
_HELLO_TXT = ROOT / "data" / "workspace" / "hello.txt"


def _fetch_items(path: str) -> list[dict]:
    """GET 一个集合端点，统一成 list[dict]（兼容 {key:[...]} / {key:{...}} / 裸 list）。"""
    try:
        data = httpx.get(f"{BASE}{path}", timeout=10).json()
    except Exception:  # noqa: BLE001
        return []
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("sessions", "pages", "jobs", "memories"):
            if key in data:
                v = data[key]
                v = list(v.values()) if isinstance(v, dict) else v
                return [x for x in v if isinstance(x, dict)]
    return []


def _ids(path: str) -> set[str]:
    return {it["id"] for it in _fetch_items(path) if it.get("id")}


def capture_baseline() -> dict:
    """跑前抓取既有记录 id，供收尾区分「本轮新增」。"""
    return {
        "sessions": _ids("/api/sessions"),
        "pages": _ids("/api/pages"),
        "jobs": _ids("/api/jobs"),
        "memories": _ids("/api/memories"),
    }


def _delete(path: str, rid: str, removed: list[str]) -> None:
    try:
        if httpx.delete(f"{BASE}{path}/{rid}", timeout=10).status_code < 300:
            removed.append(f"{path}/{rid}")
    except Exception:  # noqa: BLE001
        pass


def cleanup_residue(base: dict | None) -> None:
    """删除本轮 verify 在 live data 留下的测试痕迹，并重建 RAG 索引清除 mock-embed。"""
    if base is None:
        return
    removed: list[str] = []

    for it in _fetch_items("/api/sessions"):
        if it.get("id") not in base["sessions"]:
            _delete("/api/sessions", it["id"], removed)

    for it in _fetch_items("/api/pages"):
        if it.get("id") in base["pages"]:
            continue
        if (
            it.get("title") in _MOCK_PAGE_TITLES
            or it.get("source") in _MOCK_PAGE_SOURCES
            or str(it.get("content", "")).startswith("hello from mock")
        ):
            _delete("/api/pages", it["id"], removed)

    for it in _fetch_items("/api/jobs"):
        if it.get("id") not in base["jobs"] and str(it.get("title", "")).startswith(_MOCK_JOB_TITLE_PREFIX):
            _delete("/api/jobs", it["id"], removed)

    # 记忆：auto-extract 文案不固定，按「基线后新增」删除（假设 verify 运行期间无并发真实对话）
    for it in _fetch_items("/api/memories"):
        if it.get("id") not in base["memories"]:
            _delete("/api/memories", it["id"], removed)

    try:
        if _HELLO_TXT.exists():
            _HELLO_TXT.unlink()
            removed.append("workspace/hello.txt")
    except OSError:
        pass

    if removed:
        print(f"INFO  已清扫测试残留 {len(removed)} 项：{removed}")

    # mock 页面删除后语料签名变化，重建索引并复位 embed 探测缓存（清除 mock-embed）
    try:
        st = httpx.post(f"{BASE}/api/rag/reindex", timeout=120).json()
        print(f"INFO  RAG 索引已重建：chunks={st.get('chunks')} embed={st.get('embed_model') or '(bm25)'}")
    except Exception as e:  # noqa: BLE001
        print(f"WARN  RAG 重建失败，请手动 POST /api/rag/reindex：{e}")


def record(ok: bool, name: str, detail: str = "") -> None:
    RESULTS.append((ok, name, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail and not ok else ""))


def create_session() -> str:
    r = httpx.post(f"{BASE}/api/sessions", json={"title": "verify"}, timeout=10)
    r.raise_for_status()
    return r.json()["id"]


def stream_chat(sid: str, text: str) -> list[dict]:
    events: list[dict] = []
    with httpx.stream(
        "POST", f"{BASE}/api/chat/stream",
        json={"session_id": sid, "content": text}, timeout=90,
    ) as r:
        buf = ""
        for chunk in r.iter_text():
            buf += chunk
            while "\n\n" in buf:
                raw, buf = buf.split("\n\n", 1)
                for line in raw.split("\n"):
                    if line.startswith("data: "):
                        try:
                            events.append(json.loads(line[6:]))
                        except json.JSONDecodeError:
                            pass
    return events


def ev_types(events: list[dict]) -> list[str]:
    return [e["type"] for e in events]


def main() -> int:
    # S0 健康 + pipeline 配置面
    try:
        h = httpx.get(f"{BASE}/api/health", timeout=5).json()
        pipe = httpx.get(f"{BASE}/api/pipeline", timeout=5).json()
        required = {"planner", "executor", "evaluator", "memory"}
        ok = h["status"] == "ok" and required <= set(pipe["roles"])
        record(ok, "S0 health+pipeline", json.dumps(pipe["roles"], ensure_ascii=False))
    except Exception as e:  # noqa: BLE001
        record(False, "S0 health+pipeline", str(e))
        return 1

    # 切到 mock 网关前先快照 settings + 抓取记录基线；恢复/清扫由 __main__ 的 finally 兜底
    global _SNAPSHOT, _BASELINE
    _SNAPSHOT = snapshot_settings()
    _BASELINE = capture_baseline()
    httpx.put(f"{BASE}/api/settings", json=MOCK_SETTINGS, timeout=10)

    httpx.post(f"{MOCK_ORIGIN}/_reset", timeout=5)
    sid = create_session()

    # S1 fast 层直答
    ev = stream_chat(sid, "你好")
    t = ev_types(ev)
    ok = (
        "workflow" in t and t.count("eval") == 0
        and any(e["type"] == "workflow" and e["tier"] == "fast" for e in ev)
        and any(e["type"] == "role_active" and e["role"] == "executor" for e in ev)
        and not any(e["type"] == "role_active" and e["role"] == "planner" for e in ev)
        and t[-1] == "done"
    )
    record(ok, "S1 fast 直答（无规划/无评估）", str(t))

    # S2 standard + workspace 工具 + 评估 PASS
    ev = stream_chat(sid, "请写一个 hello.txt 到工作区")
    t = ev_types(ev)
    tc = [e for e in ev if e["type"] == "tool_call"]
    tr = [e for e in ev if e["type"] == "tool_result"]
    evl = [e for e in ev if e["type"] == "eval"]
    ws_file = ROOT / "data" / "workspace" / "hello.txt"
    ok = (
        any(e["type"] == "workflow" and e["tier"] == "standard" for e in ev)
        and any(e["type"] == "role_active" and e["role"] == "planner" for e in ev)
        and any(e["type"] == "plan" for e in ev)
        and tc and tc[0]["tool"] == "workspace_write"
        and tr and not tr[0]["is_error"]
        and evl and evl[0]["passed"] is True
        and t[-1] == "done"
        and ws_file.exists() and "hello from mock" in ws_file.read_text(encoding="utf-8")
    )
    record(ok, "S2 standard：规划+工具+评估+落盘", str(t))

    # S3 deep 层 FAIL→返工→PASS
    ev = stream_chat(sid, "请深度分析这个主题并给出报告")
    evl = [e for e in ev if e["type"] == "eval"]
    execs = [e for e in ev if e["type"] == "role_active" and e["role"] == "executor"]
    ok = (
        any(e["type"] == "workflow" and e["tier"] == "deep" for e in ev)
        and len(evl) == 2 and evl[0]["passed"] is False and evl[1]["passed"] is True
        and len(execs) >= 2 and ev_types(ev)[-1] == "done"
    )
    record(ok, "S3 deep：FAIL 反馈返工后 PASS", f"evals={[(e['passed'], e['attempt']) for e in evl]}")

    # S4 技能工具
    ev = stream_chat(sid, "你有哪些技能？")
    tr = [e for e in ev if e["type"] == "tool_result"]
    ok = any(e["type"] == "tool_call" and e["tool"] == "skill_list" for e in ev) and tr and "translate" in tr[0]["content"]
    record(ok, "S4 skill_list 工具", "")

    # S5 定时任务：创建→到期→真实执行→结果回写
    ev = stream_chat(sid, "帮我设置一个定时提醒")
    ok = any(e["type"] == "tool_call" and e["tool"] == "job_create" for e in ev)
    time.sleep(4)
    jobs = httpx.get(f"{BASE}/api/jobs", timeout=5).json()["jobs"]
    target = next((j for j in jobs if j["title"] == "mock 提醒"), None)
    ok = ok and target is not None and target["status"] == "done" and bool(target.get("result"))
    record(ok, "S5 job_create 到期真实执行", str([(j["title"], j["status"], bool(j.get("result"))) for j in jobs]))

    # S6 记忆工具 + 自动抽取
    ev = stream_chat(sid, "请记住：我喜欢蓝色")
    ok = any(e["type"] == "tool_call" and e["tool"] == "memory_save" for e in ev)
    time.sleep(1.5)
    mems = httpx.get(f"{BASE}/api/memories", timeout=5).json()["memories"]
    ok = ok and any(m["content"] == "用户喜欢蓝色" for m in mems)
    ok = ok and any(m["content"] == "用户偏好简洁回答" and m["source"] == "auto" for m in mems)
    record(ok, "S6 memory_save + 自动抽取", str([m["content"] for m in mems]))

    # S7 页面工具 + REST 回读
    ev = stream_chat(sid, "创建一个页面")
    tr = [e for e in ev if e["type"] == "tool_result" and e["tool"] == "page_create"]
    ok = bool(tr)
    if ok:
        pid = tr[0]["content"].split("id=", 1)[1].split()[0]
        page = httpx.get(f"{BASE}/api/pages/{pid}", timeout=5).json()
        ok = page["title"] == "mock 页面"
    record(ok, "S7 page_create + REST 回读", "")

    # S8 meta 工具
    ev = stream_chat(sid, "用工具查看系统状态")
    tr = [e for e in ev if e["type"] == "tool_result" and e["tool"] == "meta_status"]
    ok = bool(tr) and '"roles"' in tr[0]["content"]
    record(ok, "S8 meta_status 工具", "")

    # S9 回归：sessions/mcp/settings/cancel
    try:
        ss = httpx.get(f"{BASE}/api/sessions", timeout=5).json()
        mc = httpx.get(f"{BASE}/api/mcp/servers", timeout=5).json()
        st = httpx.get(f"{BASE}/api/settings", timeout=5).json()
        cc = httpx.post(f"{BASE}/api/chat/cancel", json={"session_id": "nope"}, timeout=5).json()
        ok = any(s["id"] == sid for s in ss) and "servers" in mc and "llm" in st and cc["ok"] is False
        record(ok, "S9 回归 sessions/mcp/settings/cancel", "")
    except Exception as e:  # noqa: BLE001
        record(False, "S9 回归 sessions/mcp/settings/cancel", str(e))

    # S10 单元级边界：路径遍历/未知工具/job 参数校验/记忆去重
    sys.path.insert(0, str(ROOT))

    async def unit_checks() -> list[bool]:
        from app.tool_registry import tool_registry
        from app.job_scheduler import JobScheduler
        from app.memory_manager import memory_manager
        from app import unified_tools as ut

        try:
            r1 = await ut.ws_write({"path": "../../evil.txt", "content": "x"})
            ok1 = r1.startswith("Error")
        except ValueError:
            ok1 = True  # 护栏以异常形式拦截同样算通过
        r2 = await tool_registry.call("no_such_tool", {})
        _, e1 = JobScheduler().create("t", delay_seconds=1, interval_seconds=1)
        _, e2 = JobScheduler().create("", delay_seconds=1)
        m1 = memory_manager.add("去重测试条目")
        m2 = memory_manager.add("去重测试条目")
        return [
            ok1,
            r2.startswith("Error"),
            e1 is not None,
            e2 is not None,
            m1["id"] == m2["id"],
            not (ROOT / "evil.txt").exists(),
        ]

    checks = asyncio.run(unit_checks())
    record(all(checks), "S10 单元边界（遍历/未知工具/参数/去重）", str(checks))

    # S11 RAG 知识库：索引重建 / 混合检索 / 拒答阈值
    # 拒答探针用中文无关查询：英文探针会与 S2/S7 注入的英文 mock 页（hello from mock…）
    # 共享 bigram，短文档 BM25 顶过 refuse_threshold 致漏拒（实测）；中文探针与英文 mock 页
    # 零重叠、与中文财报语料 cos≈0.25<0.35，拒答稳定。
    try:
        st = httpx.post(f"{BASE}/api/rag/reindex", timeout=60).json()
        sres = httpx.get(f"{BASE}/api/rag/search", params={"q": "hello 工作区写入"}, timeout=30).json()
        ares = httpx.post(f"{BASE}/api/rag/answer", json={"query": "量子纠缠贝尔不等式"}, timeout=60).json()
        ok = (
            st["chunks"] > 0
            and len(sres["chunks"]) > 0
            and sres["confidence"] > 0
            and ares["refused"] is True
            and ares["answer"] == ""
        )
        record(ok, "S11 RAG 索引/检索/拒答", f"chunks={st['chunks']} embed={st['embed_model']} conf={sres['confidence']}")
    except Exception as e:  # noqa: BLE001
        record(False, "S11 RAG 索引/检索/拒答", str(e))

    # S12 自动化真实执行通道：手动触发 → running → 回填 success/error + session_id
    try:
        autos = httpx.get(f"{BASE}/api/automations", timeout=5).json()["automations"]
        tgt = next((a for a in autos if a["status"] in ("active", "paused")), None)
        ok = bool(tgt)
        final = None
        if tgt:
            run = httpx.post(f"{BASE}/api/automations/{tgt['id']}/run", timeout=10).json()
            ok = ok and run["status"] == "running"
            for _ in range(60):
                runs = httpx.get(f"{BASE}/api/automations", timeout=5).json()["runs"]
                hit = next((x for x in runs if x["id"] == run["id"]), None)
                if hit and hit["status"] != "running":
                    final = hit
                    break
                time.sleep(1)
        ok = ok and bool(final) and final["status"] in ("success", "error") and bool(final.get("session_id"))
        record(ok, "S12 automation 真实执行通道", str(final and (final["status"], final["detail"][:60])))
    except Exception as e:  # noqa: BLE001
        record(False, "S12 automation 真实执行通道", str(e))

    # S13 认证开关：401 拦截 / 正确 token 放行 / health 豁免 / 关闭恢复
    try:
        en = httpx.post(f"{BASE}/api/auth/enable", json={}, timeout=5)
        en.raise_for_status()
        token = en.json()["token"]
        r401 = httpx.get(f"{BASE}/api/settings", timeout=5)
        rbad = httpx.get(f"{BASE}/api/settings", headers={"Authorization": "Bearer wrong-token-xx"}, timeout=5)
        rok = httpx.get(f"{BASE}/api/settings", headers={"Authorization": f"Bearer {token}"}, timeout=5)
        rhealth = httpx.get(f"{BASE}/api/health", timeout=5)
        ok = (
            r401.status_code == 401 and rbad.status_code == 401
            and rok.status_code == 200 and rhealth.status_code == 200
        )
        httpx.post(f"{BASE}/api/auth/disable", timeout=5)
        rafter = httpx.get(f"{BASE}/api/settings", timeout=5)
        ok = ok and rafter.status_code == 200
        record(ok, "S13 认证开关（401/放行/豁免/关闭恢复）", "")
    except Exception as e:  # noqa: BLE001
        httpx.post(f"{BASE}/api/auth/disable", timeout=5)
        record(False, "S13 认证开关（401/放行/豁免/关闭恢复）", str(e))

    failed = [r for r in RESULTS if not r[0]]
    print(f"\n==== {len(RESULTS) - len(failed)}/{len(RESULTS)} PASS ====")
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        # 无论正常结束、断言失败还是 Ctrl-C：先还原 settings，再清扫数据残留 + 重建索引
        restore_settings(_SNAPSHOT)
        cleanup_residue(_BASELINE)