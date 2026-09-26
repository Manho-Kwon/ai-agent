"""Mock OpenAI-compatible gateway (127.0.0.1:4831).

Branches by model name to simulate each role, used for offline end-to-end verification of the orchestration pipeline:
- mock-planner   -> non-streaming structured plan（steps 绑定 tool/success，M2 契约）
- mock-evaluator -> first time for "deep" requests FAIL, thereafter PASS（score/failures）
- mock-memory    -> non-streaming JSON array (one fact)
- mock-embed     -> POST /v1/embeddings deterministic vectors（RAG 混合检索测试）
- mock-executor  -> streaming; issues tool_call based on keywords in the question, otherwise direct answer
"""
from __future__ import annotations

import json
import math
import uuid
import zlib

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

app = FastAPI()

MODELS = ["mock-executor", "mock-planner", "mock-evaluator", "mock-memory", "mock-embed"]
_EMBED_DIM = 256  # mock 向量维度（hash 词袋模拟语义向量：相关文本高相似、无关文本低相似）
_eval_attempts: dict[str, int] = {}


@app.get("/v1/models")
async def models():
    return {"data": [{"id": m} for m in MODELS]}


@app.post("/_reset")
async def reset():
    _eval_attempts.clear()
    return {"ok": True}


def _embed_vector(text: str) -> list[float]:
    """确定性伪向量：重叠 bigram 词袋哈希 → 归一化。

    256 维降低碰撞噪声：同主题文本（共享 bigram）相似度高，
    无关文本（中文 vs 英文等）相似度接近 0，贴近真实 embedding 行为。"""
    vec = [0.0] * _EMBED_DIM
    clean = "".join(ch for ch in text if not ch.isspace())
    tokens = [clean[i : i + 2] for i in range(max(len(clean) - 1, 0))] or ["<empty>"]
    for tok in tokens:
        vec[zlib.crc32(tok.encode("utf-8")) % _EMBED_DIM] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [round(v / norm, 6) for v in vec]


@app.post("/v1/embeddings")
async def embeddings(req: Request):
    body = await req.json()
    inputs = body.get("input") or []
    if isinstance(inputs, str):
        inputs = [inputs]
    return JSONResponse({
        "object": "list",
        "model": body.get("model") or "mock-embed",
        "data": [
            {"object": "embedding", "index": i, "embedding": _embed_vector(str(t))}
            for i, t in enumerate(inputs)
        ],
        "usage": {"prompt_tokens": 1, "total_tokens": 1},
    })


def _last_user(messages: list) -> str:
    for m in reversed(messages or []):
        if m.get("role") == "user":
            c = m.get("content")
            if isinstance(c, str):
                return c
    return ""


def _has_tool_msg(messages: list) -> bool:
    """仅当「最后一条 user 消息之后」存在 tool 消息时，视为工具回填轮。

    多轮会话历史里天然带有旧 tool 消息，不能全量判断。"""
    idx = -1
    for i in range(len(messages or []) - 1, -1, -1):
        if (messages[i] or {}).get("role") == "user":
            idx = i
            break
    return any(m.get("role") == "tool" for m in (messages or [])[idx + 1:])


def _nonstream(model: str, content: str) -> dict:
    return {
        "id": "mock",
        "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 32, "completion_tokens": 16, "total_tokens": 48},
    }


def _mock_tool_for(q: str) -> tuple[str, dict]:
    """Planner 步骤绑定与 Executor tool_call 同一关键词路由（保证计划-执行契约成立）。"""
    if "写入" in q or "写一个" in q:
        return "workspace_write", {"path": "hello.txt", "content": "hello from mock executor"}
    if "技能" in q:
        return "skill_list", {}
    if "定时" in q:
        return "job_create", {"title": "mock 提醒", "delay_seconds": 2, "prompt": "向用户报告：mock 提醒时间到了"}
    if "记住" in q:
        return "memory_save", {"content": "用户喜欢蓝色", "tags": "偏好"}
    if "页面" in q:
        return "page_create", {"title": "mock 页面", "content": "# mock\n内容"}
    if "状态" in q:
        return "meta_status", {}
    return "", {}


async def _stream(model: str, texts: list[str], tool_call: dict | None):
    async def gen():
        for t in texts:
            for i in range(0, max(len(t), 1), 8):
                chunk = {"choices": [{"index": 0, "delta": {"content": t[i : i + 8]}, "finish_reason": None}]}
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        if tool_call:
            args = json.dumps(tool_call["arguments"], ensure_ascii=False)
            c1 = {"choices": [{"index": 0, "delta": {"tool_calls": [{"index": 0, "id": f"call_{uuid.uuid4().hex[:8]}", "type": "function", "function": {"name": tool_call["name"], "arguments": ""}}]}, "finish_reason": None}]}
            yield f"data: {json.dumps(c1, ensure_ascii=False)}\n\n"
            c2 = {"choices": [{"index": 0, "delta": {"tool_calls": [{"index": 0, "function": {"arguments": args}}]}, "finish_reason": None}]}
            yield f"data: {json.dumps(c2, ensure_ascii=False)}\n\n"
            c3 = {"choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}]}
            yield f"data: {json.dumps(c3, ensure_ascii=False)}\n\n"
        else:
            c4 = {"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}
            yield f"data: {json.dumps(c4, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.post("/v1/chat/completions")
async def completions(req: Request):
    body = await req.json()
    model = body.get("model", "")
    messages = body.get("messages", [])
    q = _last_user(messages)

    if "planner" in model:
        tool, params = _mock_tool_for(q)
        plan = {
            "intent": q[:60],
            "goal": q[:120],
            "steps": [
                {"id": "s1", "tool": tool, "params": params,
                 "success": "工具真实执行且无报错" if tool else "理解请求并给出直接回答"},
                {"id": "s2", "tool": "", "params": {}, "success": "回答与请求对应"},
            ],
            "tool_hints": [tool] if tool else [],
            "acceptance": ["回答与请求对应", "工具操作需真实执行"],
        }
        return JSONResponse(_nonstream(model, json.dumps(plan, ensure_ascii=False)))

    if "evaluator" in model:
        # 键只取请求部分（答案每轮不同，不能进键）
        key = q.split("\n助手回答：")[0][:80]
        n = _eval_attempts.get(key, 0)
        _eval_attempts[key] = n + 1
        if "深度" in q and n == 0:
            out = {
                "pass": False, "score": 55,
                "failures": [{"step": "s1", "detail": "mock：回答缺少分步骤说明"}],
                "feedback": "mock：回答缺少分步骤说明，请补充后重试",
            }
        else:
            out = {"pass": True, "score": 92, "failures": [], "feedback": ""}
        return JSONResponse(_nonstream(model, json.dumps(out, ensure_ascii=False)))

    if "memory" in model:
        return JSONResponse(
            _nonstream(model, json.dumps(["用户偏好简洁回答"], ensure_ascii=False))
        )

    # executor / doc_compose 非流式（kb_answer 等 complete_chat 调用）
    if not body.get("stream", False):
        return JSONResponse(
            _nonstream(model, f"mock 生成：基于知识库片段回答「{q[:30]}」")
        )

    # executor（流式）
    if _has_tool_msg(messages):
        return await _stream(model, ["mock：已基于工具结果完成任务。"], None)

    tool, args = _mock_tool_for(q)
    tool_call = {"name": tool, "arguments": args} if tool else None

    if tool_call:
        return await _stream(model, ["好的，我用工具处理一下。"], tool_call)
    return await _stream(model, [f"mock 直答：收到「{q[:30]}」"], None)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=4831, log_level="warning")
