# code_map.md — Arche Agent 工作台代码映射

> **本文件是项目代码结构的唯一权威索引（SSOT for architecture）。**
> 内容均与当前代码核对（路由装饰器、文件清单、函数签名），不收录未实现功能。
> 项目根目录：`d:\Codex_Harness\ai_agent` ｜ 服务：http://127.0.0.1:4830 ｜ 启动：`.\start.ps1`

---

## 0. 维护协议（强制执行）

### 0.1 开发前必做
1. **先读本文件**相关章节：目录树（§2）→ 涉及模块说明（§3/§4）→ API 规范（§3.7）→ 红线清单（§7）。
2. 新增接口/页面/数据文件前，先在 §3.7 接口表或 §4 组件表中确认无同类实现，避免功能冗余。
3. 命名、存储位置、CSS 前缀、返回结构必须遵循 §5/§6 既有约定。

### 0.2 开发后必做（自动化同步）
0. **自查清理冗余**（红线 13）：回头审一遍本次改动块，删掉重复逻辑、死变量、失效注释与为假想需求预留的分支；后端跑 `.venv\Scripts\python.exe -m compileall -q <files>`、前端跑 `npx tsc --noEmit` 确认零告警。**这一步不依赖用户指出。**
1. 更新本文件对应章节（模块表、API 表、数据模型、组件表）。
2. 在 §9 版本日志追加一条记录（时间、摘要、修改人）。可使用辅助脚本：
   ```powershell
   .\scripts\code_map_log.ps1 -Summary "新增 XXX 接口与页面" -Author "TRAE"
   # -Version 可省略，省略时自动在上一条版本号 patch 位 +1
   ```
3. 更新 §10 当前运行状态（服务/bundle/待办，若本次改动影响了它们）与 §11 交付记录（需求来源、决策原因、验收结论、备份位置与回滚方案）。
4. 准确性校验：API 表以 `app/routes/*.py` 的路由装饰器为准；组件表以 `web/src` 实际文件为准；工具表以 `unified_tools.builtins()` 的**注册名**为准（不是 handler 函数名）。**禁止把规划中功能写成已实现。**

### 0.3 修改人约定
- `TRAE` / `Qoder` = AI 助手实施；`用户` = 用户手动修改；其余署名自行填写。

### 0.4 单文档三分区（2026-09-10 起；原 `project_memory.md` 已并入本文件后删除）
本文件是项目唯一文档，按信息的**失效方式**分区——三类内容混写会互相污染：

| 分区 | 章节 | 写什么 | 更新时机 | 能否改写既有内容 |
|---|---|---|---|---|
| 结构事实 | §1-§6、§8 | 代码现在是什么：目录、模块、接口、schema、约定、脚本 | 每次改代码必须同步 | 直接覆盖为当前真相 |
| 红线与经验 | §7 | 会重复踩的坑与硬约束 | 踩到新坑时追加 | 可修订（坑被证伪就改） |
| 易失状态 | §10 | 服务 PID、bundle 哈希、网关实况、待办 | 状态一变就改 | 直接覆盖，不留旧值 |
| 历史叙事 | §9、§11 | 版本日志、交付的需求来源/决策原因/验收结论/备份与回滚 | 每次交付追加 | **一旦写下不改写**（那是当时的事实） |

- 归属判定两问：「代码没变时它会不会过时？」会 → §10；「它描述现在的代码，还是当时的决定？」现在 → §1-§8，当时 → §9/§11。
- **结构事实严禁写进叙事区**。合并时实测：原 `project_memory.md` 的结构性章节有 6 处已随代码演进而失效却无人核对——「六类内建工具」实为 8 类 18 个、evaluator 输出 `{pass, feedback}` 实为 `{passed, score, failures, feedback, fallback}`、roles 列 4 角色实为 8、SSE 事件清单缺 `round`/`step_update`/`confirm_request`、配置 schema 与 API 一览均严重不全。这正是分区要防的事：叙事区没人拿它跟代码对，结构区每次改代码都必须对。

---

## 1. 项目概览

| 项 | 内容 |
|---|---|
| 定位 | nexus-agent 0.9.35 的复刻裁剪版：FastAPI 后端 + React/Vite 前端的三栏 AI 工作台 |
| 后端 | Python 3.14 + FastAPI + httpx（OpenAI 兼容 SSE 流式）+ MCP SDK v2.x（stdio 常驻连接） |
| 前端 | React 19 + TypeScript + Vite 7，无 UI 框架，纯 CSS（CSS 变量主题系统） |
| 存储 | 全部落 `data/`（JSON 文件 + .env 密钥 SSOT），无数据库 |
| 入口 | `start.ps1`（PowerShell，建 venv、装依赖、起 uvicorn）／`start.bat`（CMD，同流程，**必须 GBK + CRLF**，见 §7 红线 15）／`start.sh`（类 Unix）；开发重启 `scripts\_dev_start_server.ps1` / `_dev_stop_server.ps1` |
| 静态托管 | `web/dist` 由 FastAPI 挂载（`/assets`、`/library` + SPA fallback） |

---

## 2. 目录树

```
ai_agent/
├─ start.ps1                    # 一键启动（venv + 依赖 + uvicorn:4830）；UTF-8 BOM，LF 可用
├─ start.bat                    # 同上，Windows CMD 版；必须 GBK + CRLF（§7 红线 15）
├─ start.sh                     # 同上，类 Unix 版；LF
├─ server.py                    # uvicorn 启动入口（app.main:app）
├─ requirements.txt             # 后端依赖（fastapi/uvicorn/httpx/mcp/pydantic/dotenv/truststore）
├─ code_map.md                  # ← 本文件（项目唯一文档：结构 SSOT / 红线 / 运行状态 / 交付记录，见 §0.4）
├─ docs/                        # 01-架构分析.md / 02-实施方案.md
├─ scripts/                     # 开发与验收脚本（见 §8）
├─ app/                         # 后端
│  ├─ main.py                   # FastAPI 装配 + lifespan + 认证中间件 + 静态托管 + SPA
│  ├─ config.py                 # data/ 路径、config.json 读写、.env 加载/读写、默认 schema
│  ├─ tls.py                    # truststore 注入 OS 信任链（内网自签 HTTPS）
│  ├─ audit.py                  # 审计日志（data/audit/audit-YYYYMMDD.jsonl，append/digest/recent）
│  ├─ llm.py                    # OpenAI 兼容客户端（stream_chat / complete_chat / list_models，重试2次）
│  ├─ model_router.py           # 角色→模型解析 resolve_role()（providers 抽象层）
│  ├─ workflow_router.py        # 四层路由 fixed/fast/standard/deep（固定流程关键词 + 启发式）
│  ├─ fixed_flows.py            # 固定工作流层（tools/jobs/memories/status 直查直答，失败回退 fast）
│  ├─ planner.py                # 结构化规划代理（{intent,goal,steps:[{id,tool,params,success}],acceptance}）
│  ├─ evaluator.py              # 两层评估（规则层 score/failures + 语义层 {passed,feedback}）
│  ├─ prompt_assembler.py       # P0-P5 系统提示组装（超预算按 P3→P2→P4→P5→P1 裁剪）
│  ├─ orchestrator.py           # 编排核心 run_turn()（路由→规划→步骤绑定执行→危险确认→评估→记忆）
│  ├─ tool_registry.py          # 工具聚合 + 执行网关（参数校验/超时/danger 确认门/审计）
│  ├─ unified_tools.py          # 八类内建工具（ws/sk/job/page/mem/meta/kb），ws_write 触发归档
│  ├─ rag.py                    # RAG 知识库引擎（BM25+向量混合 RRF，资料库页面为语料，低置信拒答）
│  ├─ task_runner.py            # job/automation 真实 LLM 执行通道（并发闸门+超时+审计+结果回写）
│  ├─ mcp_manager.py            # MCP 常驻连接（owner-task + AsyncExitStack，stdio/http/sse）
│  ├─ session_manager.py        # 会话 CRUD + 消息持久化 + tool_trace 展开 prepare_thread()
│  ├─ memory_manager.py         # 长期记忆（去重 + token 重叠检索 + LLM 自动抽取）
│  ├─ skill_manager.py          # 技能卡（frontmatter 解析，data/skills/*.md）
│  ├─ job_scheduler.py          # 定时任务（1s tick，重启顺延；有 prompt 经 task_runner 真实执行）
│  ├─ page_manager.py           # 资料库（page/folder/bookmark/file 四态，级联删除，zip 解压）
│  ├─ workspace_manager.py     # 工作区注册表 + 真实扫描统计 + 每日同步 loop
│  ├─ automation_manager.py     # 自动化任务（15s tick；触发经 task_runner 走真实编排管道）
│  └─ routes/                   # FastAPI 路由（12 个 router，见 §3.7）
│     ├─ sessions.py  chat.py  auth.py  mcp.py  connections.py  settings.py
│     ├─ extras.py（memories/skills/pages/jobs/pipeline）  rag.py
│     ├─ workspaces.py  automations.py  retrieval.py  storage.py
├─ web/                         # 前端
│  ├─ index.html  vite.config.ts  tsconfig.json  package.json
│  └─ src/
│     ├─ main.tsx               # React 入口
│     ├─ App.tsx                # 顶层状态 + 主区条件渲染 + SettingsPageKey 路由
│     ├─ api.ts                 # fetch 封装 jsonFetch() + api 对象（全部后端接口）
│     ├─ types.ts               # 全部 TS 类型（与后端响应契约对应）
│     ├─ appearance.ts          # 主题钩子（<html> data-theme/data-tone/data-glow + CSS 变量）
│     ├─ styles.css             # 全部样式（:root 变量 + 各模块前缀，深色 [data-theme="dark"]）
│     └─ components/
│        ├─ SessionList.tsx     # 左侧栏（品牌/会话/资料库/工作区/自动化/设置齿轮）
│        ├─ ChatArea.tsx        # 中栏聊天（消息行/输入区/工具卡片/步骤时间线/评分/确认弹窗/分享/历史）
│        ├─ ToolPanel.tsx       # 右栏「工具与技能」（MCP 服务器卡 + 技能 + 开关）
│        ├─ SettingsPanel.tsx   # 左栏设置菜单（4 组 10 条目）
│        ├─ Markdown.tsx        # Markdown 渲染
│        ├─ LibraryPanel.tsx    # 资料库主区            AddPageModal.tsx   # 添加页面（5 Tab）
│        ├─ WorkspacePanel.tsx  # 工作区主区            AddWorkspaceModal.tsx
│        ├─ AutomationPanel.tsx # 自动化主区（双 Tab）   AddAutomationModal.tsx
│        └─ settings/           # 设置子页（12 个，见 §4.2）
└─ data/                        # 运行时数据（见 §5.1，自动生成，不入库）
```

---

## 3. 后端架构

### 3.1 应用装配（main.py）

- `lifespan` 启动顺序：`init_data_dir()` → `tls.setup_os_trust()` → `session_manager.load()` → `skill_manager.init_samples()` → `mcp_manager.load_config()` + 后台 `connect_all()` → `workspace_manager.start_daily_loop()` → `job_scheduler.start()` → `automation_manager.start()`；关闭按逆序 + 取消 MCP 连接任务。
- **认证中间件**（main.py `auth_middleware`）：`auth.enabled` 时所有 `/api/*` 校验 `Authorization: Bearer <token>`（`hmac.compare_digest` 常时比较）；豁免 `/api/health` 与 `/api/auth/*`；401 响应体 `{"detail": ...}`。
- 路由注册顺序：sessions → chat → **auth** → mcp → connections → settings → storage → retrieval → extras → workspaces → automations → **rag**。
- 静态托管：`/library`（StaticFiles，挂载前 mkdir）→ `/assets`（dist/assets）→ SPA fallback（`GET /{path}`，含路径遍历防护 `is_relative_to`）。**新增 API 路由不会被 SPA 吞掉**；注意 fallback 仅注册 GET，POST 打错路径会得 405。

### 3.2 配置层（config.py）

- 进程内缓存 `_config`（线程锁）；`load_config()` 与 `_DEFAULT_CONFIG` 逐节合并补默认（roles 做二层合并）。
- 密钥 SSOT：密钥只存 `data/.env`，**config.json 不存任何密钥**；`.env` 仅启动时由 dotenv 加载一次。
- `set_env_key(key, value)` / `delete_env_key(key)`：就地改写 .env（保留注释，存在则替换否则追加）并同步 `os.environ`，**界面录入密钥免重启即时生效**。
- `normalize_base_url()`：OpenAI 兼容 base 自动补 `/v1` 后缀。
- `llm_settings()`：`.env`（LLM_BASE_URL/LLM_MODEL）> config.json `llm` 节 > 内置默认。

### 3.3 编排管道（v1.1 核心）

```
用户消息 → workflow_router.route(content, mode)  → tier: fixed | fast | standard | deep
   fixed    → fixed_flows.run_flow()（tools/jobs/memories/status 直查直答，未命中规则或失败回退 fast）
   fast     → 直接 executor 流式直答（不规划/不挂工具/不评估）
   standard → planner.make_plan() → executor 工具循环（步骤绑定）→ evaluator 验收
   deep     → 规划更细（≤8 步）、评估更严（FAIL 返工上限 evaluator.max_rework=3）
```

- `orchestrator.run_turn(session_id)` 是异步生成器，产出 SSE 事件（见 §3.5）；任务状态机 `planning → executing → evaluating →(rework)→ done | paused_human | error | cancelled`。
- **结构化计划**：`{intent, goal, steps:[{id, tool, params, success}], tool_hints, acceptance}`；执行时 `_match_step()` 按工具名软绑定步骤，步骤状态经 `step_update` 事件推送（pending/running/done/failed）。
- **两层评估**：规则层（score 0-100 + failures[{step,type,detail}]，按验收标准与工具错误客观判定）→ 语义层（LLM {passed, feedback}）；FAIL 反馈驱动 `planner.revise_plan()` 修订后返工，预算 `evaluator.max_rework=3`（1 初跑 + 3 返工 = 上限 4 次执行）耗尽即置 `paused_human` 转人工，**不存在无限重复执行**。
- **规则层工具名归一化**（`evaluator._trace_names()`）：计划侧写注册表全名，而 trace 的 `tool` 来自 `tool_registry.info()`——MCP 工具被剥掉 server 前缀、内建工具保留 `category__name` 全名、执行者还可能用 `rebuild()` 建的 hidden 短别名调用（`has()` 返 False 但 `call()` 仍可执行）。三轴错位会把「已成功调用」判成「未被成功调用」而白烧返工预算，故每条痕迹展开为 {全名, 短名, server__短名} 三种写法后再比对。
- **tool_trace 落盘字段**：`{id, server, tool, arguments, content, is_error, ms}`。`is_error` 必须进 trace（不能只进 `tool_result` 事件），否则规则层「本轮全部工具调用均失败」检查永不触发、报错工具反被计入成功集。
- **danger 高危确认门**：MCP `annotations.destructiveHint` → 工具 danger 标志 → orchestrator 挂起 `confirm_request` 事件等人工放行（`_pending_confirms` + asyncio.Event，`POST /api/chat/confirm` 回传，120s 超时/拒绝 = 不执行并以 Error 消息回填工具环）。
- 取消：`cancel_turn(session_id)` 置 session 级 cancel_event，在流块/工具调用/角色切换等安全点退出。
- **恢复执行者（executor_recovery）**：工具连续 2 轮全部返回 Error、或执行模型直接抛 LLMError 时，`_executor_loop` 切换到 `resolve_role("executor_recovery")` 重试一次（配置同源则无感；切换时补发 role_active 事件）。
- 角色失败策略全部 **fail-open**：planner 不可用→启发式计划（打 `plan._fallback`）；evaluator 不可用→默认 PASS；memory 抽取在回合结束后台执行，不影响主链路。**放行必须在 `verdict.fallback` 标明原因**（`disabled` / `llm_unavailable` / `exception` / `parse_failed`），编排层据此置 `eval_degraded` 记忆门禁——未经验收的回答不沉淀进长期记忆，避免 fail-open 让质量门形同虚设。
- **思考链路落盘**：回合结束把 `{tier, plan, evals, stages, step_states, state}` 作为 `meta` 附在 assistant 消息上（`session_manager.append_messages` 用 `dict(m)` 逐字落盘），刷新页面/翻历史后仍可回看。`meta` **不进 LLM 上下文**：`_expand_tool_trace` 白名单只重建 role/content/tool_trace，其余键一律不带入请求体。取消路径（`cancel_ev.is_set()`）只写 `{role, content}`，无 meta 与 tool_trace——可据此反推该回合是用户手动取消。
- **会话自动命名**（`orchestrator._auto_title`）：答案落盘后、`done` 之前，若标题仍等于 `session_manager.DEFAULT_TITLE`，就用 `complete_chat(cfg=resolve_role("planner"), role="planner")` 拿「本轮用户消息 + 最终回答」概括出短标题（清洗：先裁首行再剥引号，反序会让行尾引号剥不掉）写回 `update_title`。**函数刻意不接收外部 cfg**：`run_turn` 里的 `cfg` 是 `load_config()` 返回的整份 config.json（顶层只有 `llm` / `roles` / `memory` 等节，没有 `base_url` / `model` 键），v1.0.11 之前把它当角色配置传进来，`_check_cfg` 必然抛「未配置网关地址」→ **自动命名 100% 失败**，而 fail-open 只留一行 `logger.info`，UI 上表现为所有会话标题永远是「新会话」且无人知晓原因。v1.0.11 修复。**触发条件只有「标题仍是占位值」这一条**，同时保证只命名一次、不覆盖用户手动改名、概括失败下一轮自动重试，无需新增字段。fail-open：异常只 `logger.info` 后返回。两个调用点——fixed 层在 `delta` 与 `done` 之间；standard/deep 层在 `append_messages` 之后、`if paused:` 之前，一处即覆盖 `done` 与 `paused_human` 两个分支。
- `model_router.resolve_role(role)`：`roles.<role>.provider` 非 default 时查 `providers.<name>`（base_url + api_key_env 指向 .env 变量 + 可选 model），model/temperature/max_tokens 逐级回退。**回退终点是 `llm.model`，而当前部署刻意把它留空**（模型全靠 roles 逐个指定），所以任一角色 `model` 留空 = 该角色功能被 fail-open 静默跳过，只在日志留一行、UI 无任何提示。v1.0.11 修掉的第二个缺陷就是这个形态：`roles.memory.model` 一直为空 → `auto_extract` 每轮抛「未配置模型名」→ 记忆自动抽取长期完全不工作。

### 3.4 工具层

- **执行网关**（tool_registry.call）：参数校验（必填缺失 → Error 文本）→ danger 确认门 → 超时控制（asyncio.wait_for，默认 30s，kb_answer 120s）→ 结果审计（audit.append：tool_call/tool_result 摘要落 data/audit/）。
- **八类内建工具 / 共 30 个**（`unified_tools.builtins()`；`_CATEGORY_GATE` 把 category 映射到 config 开关节，`None` = 恒启用）。**下表是 LLM 可见的注册名**，不是 handler 函数名（`ws_read` / `sk_list` / `mem_save` 是内部函数名，写进计划网关不认）：
  | category | 开关节 | 注册名 | 说明 |
  |---|---|---|---|
  | `workspace` | `workspace` | `workspace_read / workspace_write / workspace_list / workspace_delete / bash_execute / file_export` | 工作区读写列删（路径遍历防护；write 成功后 `_archive_to_library()` 自动归档资料库，受 `pages.enabled` 门控）；bash 执行 shell 命令（danger 确认门；危险命令黑名单）；导出到外部路径（系统目录黑名单） |
  | `skill` | `skills` | `skill_list / skill_load / skill_create / skill_update / skill_validate` | 技能列表 / 加载 / 创建 / 更新 / 格式校验 |
  | `job` | `jobs` | `job_create / job_list / job_cancel` | 定时任务 |
  | `page` | `pages` | `page_create / page_list / page_get` | 资料库 |
  | `memory` | `memory` | `memory_save / memory_search` | 长期记忆 |
  | `meta` | —（恒启用） | `meta_tools_list / meta_status` | 元信息 |
  | `doc` | `doc` | `doc_parse / doc_generate_excel / doc_generate_word / doc_generate_ppt / doc_generate_pdf / doc_import` | 解析 workspace 内文档/图片（PDF/Word/Excel/PPT/扫描件），扫描件与图片走 OCR；生成 Excel/Word/PPT/PDF 文档；导入外部文档到工作区并自动解析；timeout 30-120s |
  | `rag` | `rag` | `kb_search / kb_answer / web_search` | RAG 知识库检索 / 答案生成（低置信度拒答，见 §3.8）；DuckDuckGo 网页搜索；timeout 30s / 120s |
- **hidden 历史回放别名**：每个内建工具另注册 `{category}__{name}`（如 `rag__kb_search`），供 `prepare_thread` 展开 tool_trace 时解析；`has()` 对 hidden 返 False 但 `call()` 仍可执行——这是 §3.3 命名轴错位的第三条轴。
- **`_CATEGORY_GATE` 的 key 必须是 category 本身**：曾误写 `"kb": "rag"`，而工具 category 实为 `"rag"`，导致 `_CATEGORY_GATE.get("rag")` 返 None、门控短路，`rag.enabled=false` 对 kb 工具**完全失效**（已修，2026-09-10）。
- **MCP 工具**：`mcp_manager` 常驻连接，工具命名空间 `server__tool`；tool_registry.rebuild() 聚合内建 + MCP 生成 OpenAI tools schema；`annotations.destructiveHint` → danger 标注（工具摘要中显示「高危需确认」）。
- MCP 关键实现：owner-task 持有连接生命周期 + AsyncExitStack；`reload_config()` 热增删连接；开关/添加服务器后路由层用 `asyncio.create_task` 后台 reload（避免请求挂起 30s 连接超时）。
- **MCP SDK v2.x 的 CallToolResult 属性是 `is_error` 不是 `isError`**。

### 3.5 SSE 事件协议（POST /api/chat/stream）

事件类型：`start` / `workflow{tier,reason,rule}` / `role_active{role}` / `plan{plan:{intent,goal,steps,tool_hints,acceptance}, ms, fallback?, revised?}` / `step_update{step_id,state}` / `delta{content}` / `tool_call{id,server,tool,arguments}` / `tool_result{id,server,tool,content,is_error,ms}` / `round{round,chars,ms,tool_calls,final}` / `confirm_request{id,server,tool,arguments}` / `eval{passed,feedback,attempt,score,failures,fallback,ms}` / `done{content,state,meta?,feedback?,failures?}` / `error{message}` / `cancelled`。
- **阶段可观测性**：`plan` / `tool_result` / `round` / `eval` 均带 `ms`。`round` 是执行者每轮收尾事件（`chars` = 该轮模型输出字符数，只计模型流式耗时、工具时间由 `tool_result.ms` 单独承载不混口径；`final` = 该轮是否产出最终答案）。前端累积为 `StageMetric[]`，回合结束后由 `done.meta.stages` 接管。
- **`is_error` 判定口径全局统一为 `content.startswith("Error:")`**，danger 被拒路径同样为 True（`ms: 0`）；`orchestrator` 的「工具连续 2 轮全失败 → 切恢复执行者」判定也用同一前缀约定。
- `done` 两种形状：fast 层 `{content, state:"done"}`（无 meta，不经编排）；standard/deep 层带 `meta`（思考链路快照，见 §3.3），返工预算耗尽时 `state:"paused_human"` 且额外带 `feedback`/`failures`。
- **`start` 是前端判定「任务真正开始」的唯一信号**：草稿态会话的侧边栏条目由它触发 `refreshSessions()` 才出现（见 §4.1），后端建会话本身不刷新列表。
- 心跳：每 5s 发 `: heartbeat` 注释行。
- **红线**：禁止 `asyncio.wait_for(agen.__anext__())` 做心跳（超时取消会弄坏异步生成器导致 error 事件丢失）；正确做法 = 生产者 task + `asyncio.Queue` 解耦。
- 前端 POST SSE：fetch + ReadableStream 手工解析（EventSource 不支持 POST），按 `\n\n` 分帧、`data: ` 前缀解析；携带 `Authorization` 头（auth.enabled 时必需）。

### 3.6 Manager 层速查

| 模块 | 单例/类 | 数据文件 | 关键方法 |
|---|---|---|---|
| session_manager | `SessionManager` | sessions.json + sessions/&lt;id&gt;.json | create_session / list / get / update_title / delete / append_messages / `prepare_thread()`（tool_trace 展开为 OpenAI 消息）。模块级 `DEFAULT_TITLE = "新会话"` 是未命名占位标题，也是 `_auto_title` 的触发条件——别处不要再写这个字面量 |
| memory_manager | `MemoryManager` | memories.json | add（去重）/ retrieve（token 重叠 top-k）/ auto_extract（LLM 抽 0-3 条） |
| skill_manager | 模块函数 | skills/*.md（frontmatter） | init_samples（3 示例）/ list_skills / create_skill / set_enabled / reload_skills / index_text（注入 P3） |
| job_scheduler | `JobScheduler` | jobs.json | create / list / cancel / _tick（1s，pending/active→done/cancelled）。**有 prompt 的任务到期后经 task_runner 真实执行，结果写回 job.result**；空 prompt = 仅留痕提醒 |
| task_runner | 模块函数 | data/audit/ | `execute_prompt(prompt, ...)`：独立会话跑完整编排管道（并发信号量闸门 + 超时 + 审计），供 job/automation 复用；`automation_tier()` 映射 balanced/fast/precision → 档位 |
| page_manager | `PageManager` | pages.json + library/&lt;id&gt;/ | add_text / add_folder / add_bookmark / add_file_bytes / import_from_path / upsert_source（按 source 去重）/ list / get / delete（folder BFS 级联 + shutil.rmtree）；上传 zip 自动解压，**zip-slip 防护用 `is_relative_to`** |
| workspace_manager | 模块单例 | workspaces.json | create（绝对路径/存在/重复校验）/ stats（os.walk 真实扫描，2000 文件上限）/ sync / browse / start_daily_loop（30s 对点）。**无文件 watcher**：监视器恒「未运行」，语义缓存/重排器/搜索延迟为禁用零值（UI 照显，勿误接） |
| automation_manager | `AutomationManager` | automations.json | create/update/set_status/delete/batch/trigger/tick（15s；daily/weekly 当天去重；once 到期置 done）。**触发 = 写 running 记录 → 后台 task_runner 走真实编排管道，成功/失败回写 runs 并留 session_id**；push_wechat/push_wecom 仅存偏好不外发 |
| mcp_manager | `MCPClientManager` | mcp.json | load_config / connect_all / reload_config / connect_server / disconnect_server / call_tool / get_all_server_statuses |

写接口约定：manager 层校验失败抛 `ValueError` → 路由层转 HTTP 400；列表/创建响应统一返回公开视图（补默认字段，如 page 的 `_public(rec)`），否则前端显示「—」。

### 3.7 API 接口规范（66 个端点，按路由分组）

> 基址 `http://127.0.0.1:4830`；除 SSE 外全部 JSON；错误体 `{"detail": "..."}`；400=校验失败 / 404=不存在 / 409=配置文件损坏 / 422=验证失败但已保存或未通过。

**系统（main.py）**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查 `{status:"ok"}` |
| GET | `/library/*` | 资料库托管静态文件 |

**会话 `/api/sessions`（routes/sessions.py）**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `` | 会话元数据列表 |
| POST | `` | 新建会话 `{title?}` |
| GET | `/{id}` | 会话详情（含 messages） |
| PATCH | `/{id}` | 重命名 `{title}` |
| DELETE | `/{id}` | 删除会话 |

**聊天 `/api/chat`（routes/chat.py）**

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/stream` | SSE 流式对话 `{session_id, content}`（事件见 §3.5） |
| POST | `/cancel` | 取消当前回合 `{session_id}` |
| POST | `/confirm` | danger 高危确认回传 `{session_id, call_id, approved}`；未知/已超时 404 |

**访问认证 `/api/auth`（routes/auth.py）**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/status` | `{enabled, token_configured}` |
| POST | `/enable` | 开启认证 `{token?}`（≥8 位，缺省自动生成）；响应回完整 token（唯一一次）；**仅限本机回环调用** |
| POST | `/disable` | 关闭认证并清空 token；**仅限本机回环调用** |

**MCP `/api/mcp`（routes/mcp.py）**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/servers` | 服务器列表（status/tools/config_path/config_error） |
| POST | `/reload` | 热重载 mcp.json |
| POST | `/servers` | 添加服务器 `{name, transport:stdio\|http\|sse, command?, args?, env?, url?}`（后台 reload） |
| POST | `/servers/{name}/enabled` | 开关 `{enabled}`（写 mcp.json + 后台热应用，停用显式 disconnect） |
| POST | `/open-config-folder` | 资源管理器打开 data/ 目录 |

**模型连接 `/api/connections`（routes/connections.py）**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `` | 连接状态（只读不触网）：2 内置提供商（内部 LLM 两项）+ 自定义模型列表 + in_use 角色 |
| POST | `/refresh` | 全部并行验证（GET {base}/models，10s 超时；单体验证已并入此端点） |
| POST | `/{key}/key` | 保存密钥 `{api_key, base_url?}`（写 .env 后即验；失败 422 但密钥已存） |
| POST | `/custom/models` | 添加自定义模型 `{label, model, base_url, api_key}`：**先验证后落盘**，失败 422 不保存 |
| DELETE | `/custom/models/{pid}` | 删除（级联：引用角色回退 default + 删 .env 中 CONN_CM_*_KEY） |

状态四态：`disconnected`（需要连接/灰）、`unverified`（需要验证/橙）、`connected`（绿）、`error`（红）。自定义模型 = config.providers 中 `kind:"custom"` 条目，密钥变量名 `CONN_CM_<8hex>_KEY`。

**设置 `/api/settings`（routes/settings.py）**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `` | 生效配置（ui/llm/roles/workflow/runtime/evaluator/memory；密钥只回 api_key_set 布尔） |
| PUT | `` | 白名单更新：base_url/model/temperature/max_tokens/max_tool_rounds/ui/roles/workflow_mode/allow_export/evaluator_enabled/memory_enabled |
| POST | `/probe` | 网关探测 GET /models，返回模型列表与延迟 |

**扩展域 `/api`（routes/extras.py）**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET/POST | `/memories` | 记忆列表 / 新增 `{content, tags?}` |
| DELETE | `/memories/{id}` | 删除记忆 |
| GET | `/skills` `/skills/{name}` | 技能列表 / 全文 |
| POST | `/skills` `/skills/reload` `/skills/{name}/enabled` | 新建技能 / 重扫目录 / 开关 |
| GET/POST | `/pages` | 资料库列表 / 新建（kind=page\|folder\|bookmark 分流） |
| POST | `/pages/upload` | 上传（文本 text_content / 二进制 content_b64 base64，15MB 上限，zip 自动解压） |
| POST | `/pages/import-path` `/pages/import-hosted` | 本机路径导入 / 托管 URL 导入（先 httpx 验连通+抓 title） |
| GET/DELETE | `/pages/{id}` | 详情 / 删除（folder 级联） |
| GET / POST | `/jobs`、`/jobs/{id}/cancel` | 定时任务列表 / 取消任务 |
| GET | `/pipeline` | 编排管道配置 + 角色映射（调试用） |

**工作区 `/api/workspaces`（routes/workspaces.py）**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET/POST | `` | 注册表列表 / 注册 `{name, path, description?}`（绝对路径校验） |
| GET | `/stats` | 真实扫描统计（documents/paragraphs/pending_sync/daily/search…） |
| POST | `/sync` `/retry-failed` `/daily-config` | 立即同步 / 重试失败（恒 0）/ 每日检查 `{enabled,hour,minute}` |
| GET | `/browse?path=` | 服务端列子目录（前端目录选择器用） |
| DELETE | `/{id}` | 解除注册（不动磁盘文件） |

**自动化 `/api/automations`（routes/automations.py）**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `` | 任务列表 + 运行记录（runs 上限 200） |
| POST | `` | 创建 `{name,prompt,model_tier,access,schedule,validity,push_wechat,push_wecom,status?}` |
| PATCH | `/{aid}` | 编辑（done 单次任务编辑后回 paused） |
| POST | `/{aid}/toggle` `/run` | 启停 `{active}` / 手动触发 |
| DELETE | `/{aid}` | 删除 |
| POST | `/batch` `/runs/clear` | 批量 `{action:pause\|resume\|delete, ids}` / 清空运行记录 |

**检索 `/api/retrieval`（routes/retrieval.py）**：GET `/status`（mode/语料统计/有效深度 k/evidence，小语料 &lt;500 文档走保守值）；PUT `/mode` `{mode:auto|fast|precise}`。

**RAG 知识库 `/api/rag`（routes/rag.py）**：GET `/status`（chunks/signature/built_at/embed_model/enabled）；POST `/reindex`（重建索引）；GET `/search?q=&k=`（混合检索）；POST `/answer` `{query}`（低置信拒答）。

**存储 `/api/storage`（routes/storage.py）**：GET ``（8 类磁盘用量 + 2 保留类）；POST `/clean` `{keys:[...]}`（**体必须是对象，裸数组 422**）。

### 3.8 RAG 知识库（rag.py + routes/rag.py）

- 语料：资料库页面（page/file 的全文与描述），`_chunk_text` 切块（size/overlap 可配）。
- 混合检索：`_BM25` 词频评分 + 向量余弦（embedding 模型探测失败/不可达 → 自动退化为纯 BM25），RRF 融合排序。
- `answer()`：检索 top-k 证据生成答案，**低置信度（最高分低于阈值/无证据）直接拒答**不编造。
- 索引持久化 `data/rag_index.json`（signature 签名比对增量重建）；内置工具 `kb_search/kb_answer` 与 REST 端点同源。

---

## 4. 前端架构

### 4.1 全局结构

- `App.tsx` 持有顶层状态：sessions / settings / settingsPage（SettingsPageKey）/ toolsOpen / leftSettingsOpen / libraryOpen / workspaceOpen / navOpen（移动抽屉）/ theme / **confirmReq（danger 确认弹窗）**；streaming 态类型为 `{text, tools} & PipelineState`（tier/role/plan/evals/stepStates/stages）。
- **草稿态（draft session）**：`currentId === null` 即草稿态，后端此时还没有对应会话。点「新任务」、首屏无任何会话、删掉最后一个会话都只调 `enterDraft()`（清 currentId/messages，再经 `leaveView()` 关各浮层面板），**不建会话**，任务履历因此不会出现空壳条目。落地会话的唯一入口是 `ensureSession()`——`handleSend` 开头与 ChatArea 选附件时各调一次；它建完只 `setCurrentId`，**刻意不刷新侧边栏**，条目要等 SSE `start`（后端已接手）触发 `refreshSessions()` 才出现。`handleSend` 全程用局部 `sid` 贯穿 `streamChat` 与 finally 的 `openSession`，不依赖 setState 的异步刷新。
  - ChatArea「切换会话清空未发送附件」的 effect 用 `prevSid` ref 放行 `null→id`：草稿态选附件正是靠这次落地建会话，若当成切换就会把刚选好的文件清掉。
  - 代价：草稿态选了附件却始终不发送，后端会留下一个 0 消息会话，下次刷新页面时以「新会话（空任务）」出现在履历里（用户已确认接受此权衡，见 §11.2）。
- 主区条件渲染链：资料库 → 工作区 → 自动化 → 默认 ChatArea。**设置弹窗独立于此链**——`leftSettingsOpen` 为 true 时弹窗出现（`.settings-modal-overlay` 遮罩 + `.settings-modal-container` 居中容器）。弹窗内两级导航：无 `settingsPage` 时渲染 SettingsPanel 菜单（`.settings-modal-menu` + 标题/关闭按钮）；点击菜单项 → `settingsPage` 赋值 → 同弹窗内切换为对应设置子页，子页左上角返回箭头只回菜单（`setSettingsPage(null)`），不关闭弹窗。点击遮罩或菜单标题栏 ✕ 才真正关闭（`closeSettings()` 同时清 `settingsPage` 与 `leftSettingsOpen`）。
- 左栏 SessionList：设置齿轮在左下角，点击直接打开设置弹窗（侧边栏不再展开设置菜单，始终只显示会话列表）。会话卡片右上角 `.card-actions`（默认 hover 卡片时才显示）内含编辑（`.session-rename` 铅笔）与删除（`.session-del` X 号）两按钮，两者尺寸/间距一致（22×22、border-radius 4px），均默认常驻浅色背景（编辑浅绿 `#eaf6f1`、删除浅红 `#fdeeee`），hover/active 同色系逐级加深，暗色主题对称覆盖。
- **输入区盾牌按钮**：消息输入框下方工具栏第 3 个图标（`.ci-icon`），点击切换 YOLO 模式（`runtime.yolo_mode`）。开启时按钮样式变 `.ci-icon--yolo`（黄色 `#e6a817` / 背景 `#fff8e1`，暗色对称），title 变为「YOLO 模式：已跳过安全确认」；关闭时恢复默认灰色，title 为「安全：点击启用 YOLO 模式（跳过危险操作确认）」。YOLO 模式下后端 danger 高危工具确认门自动跳过，不弹人工放行弹窗。
- 右栏：App 直接渲染 `<div className="right-sidebar"><ToolPanel/></div>`（toolsOpen 控制，扳手按钮打开）。
- `api.ts`：`jsonFetch<T>()` 统一封装（401 专属提示 + 非 2xx 抛 `Error(detail)`；自动附 `Authorization: Bearer` 头，token 存 localStorage `auth-token`）；`api` 对象方法与 §3.7 端点一一对应；`streamChat()` 为 POST SSE 异步生成器（同样带认证头）；`confirmTool()` 回传 danger 确认结果。
- **`ThinkingTrace`（ChatArea.tsx）= 思考履历折叠外壳，包住 `PipelinePanel` + 工具卡片，流式与历史两处共用**：`useState(!!live)` 定初值——流式挂载即展开（执行中实时输出推理过程），历史挂载即折叠（回合结束后自动收起成一行摘要）。**折叠时机不需要任何新状态或协议字段**：流式块 `{streaming && …}` 与历史消息行是不同 React 子树，回合结束 `openSession` 重载后前者卸载、后者以新 key 挂载，`!!live` 自然取到 false。正文（答案）刻意留在壳外，折叠不吞答案。
  - 折叠态摘要由 `traceSummary()` 生成：层 / N次工具（含失败数）/ 最后一次评估结论 / `⚠ 待人工`。**转人工警示刻意进摘要**，否则折叠后用户看不到本轮其实没通过验收。
  - 渲染守卫：历史 `m.meta || m.tool_trace?.length`（老会话无 meta 但有工具痕迹时也收进壳）；流式恒渲染——表头「思考中…」本身即实时指示器，**取代了原 `.thinking` 占位 div**（该死样式已删）。
  - 工具成败判定抽为 `traceFailed(t)`，ToolCard 渲染点与摘要共用（此前判定只活在渲染点，摘要要用就得复制一遍）。
- **`PipelinePanel`（ChatArea.tsx）= 思考链路唯一渲染组件，流式与历史消息两处复用**：流式传 `streaming.*` + `live`，历史传 `m.meta.*`（同一 props 形状，见 §3.3 思考链路落盘）。内部结构 `pipeline-strip`（层 / 三角色 chip / 计划摘要 / `EvalStrip` 评估徽章 / `⚠ 待人工` 徽标）→ `StageMetrics`（每轮字符数与耗时）→ `StepTimeline`；**工具卡片与正文都不是它的子节点**——前者是兄弟节点（同被 `ThinkingTrace` 包住），后者在壳外。
  - 空面板保护：tier/role/plan/evals/stages 全空时 `return null`（外壳仍渲染表头，流式态「思考中…」本身有意义）。
  - `StepTimeline` 条件门 `plan?.steps?.length && (live || Object.keys(stepStates).length > 0)`：历史消息若没落 `step_states` 就不渲染步骤时间线，避免全 pending 的误导性展示。
- `ConfirmDialog`（独立组件）：弹窗渲染危险参数 JSON，拒绝/允许经 `onConfirm` 调 confirm 端点。
- `types.ts`：接口响应类型与后端契约对应（Settings / McpServer / SkillInfo / RetrievalStatus / ConnProvider / ConnCustomModel / ConnectionsState / PageMeta / WorkspaceStats / AutomationMeta / PlanStep / PlanInfo / EvalFailure / EvalInfo / ConfirmRequest / InFlightTool / AuthStatus / RagStatus / **StageMetric / MessageMeta / PipelineState**…）。
- **React 19 类型坑**：无全局 JSX 命名空间，组件类型注解用 `ReactElement`（`import type { ReactElement } from "react"`）；JSX 中输出 `>` 符号须用 `{'>'}` 或 `&gt;`。

### 4.2 设置子页映射（settings/ 目录）

| SettingsPageKey | 组件 | 功能 |
|---|---|---|
| `theme` | ThemeAppearancePage | 主题/色调/强调色/字号/光晕/聊天背景（appearance.ts 落 &lt;html&gt;） |
| `profile` | ProfileBrandPage | 用户/机器人名称头像、平台品牌 |
| `llm` | LlmSettingsPage + **ModelConnectionsModal** | 3 步卡：模型连接 / 模型分配（共享模型 select）/ 高级设置；弹窗管理提供商与自定义模型 |
| `storage` | RuntimeStoragePage | 运行策略、导出开关、磁盘用量清理 |
| `connection` | ConnectionStatusPage | 后端连接状态 |
| `mcp` | McpServersPage | MCP 服务器列表/开关/添加弹窗（sl-/slm- 样式） |
| `skills` | SkillsPage | 智能体技能列表/开关/新建 |
| `tasks` | ScheduledTasksPage | 计划任务（自动化只读视图 + 快捷添加） |
| `retrieval` | WorkspaceRetrievalPage | 检索模式 auto/fast/precise + 语料统计（rt- 样式） |
| `memory` | MemoryPage | 记忆开关（PUT settings memory_enabled） |
| `security` | AccessSecurityPage | 访问认证开关：开启（自定义/自动生成 token，仅展示一次并写入本地）/ 关闭 / 状态徽章（sec- 样式） |

共用外壳 `SettingsShell.tsx`（返回箭头 + 标题/副标题 + sp-body 滚动区 + 可选 footer 保存栏）。

### 4.3 样式约定（styles.css）

- CSS 变量（:root）：`--primary #4f6bed` / `--bg` / `--panel` / `--line` / `--text` / `--text-dim` / `--green` / `--green-dark` / `--amber` / `--red`；深色由 `[data-theme="dark"]` 整组翻转。
- 类名前缀按模块分区（新模块必须新起前缀，勿混用）：

| 前缀 | 模块 |
|---|---|
| `sp-` | 设置子页通用（card/field/btn/footer/slider/toggle…） |
| `mc-` | 模型连接弹窗 + LLM 步骤卡 + 模型分配双 Tab（mc-tabs/mc-tab/mc-info-strip/mc-role-row/mc-picker 双行选择器/mc-eval-toggle；保存钮 mc-save-btn 青绿 #0e8a7d） |
| `sl-` / `slm-` | MCP 服务器列表 / 添加弹窗 |
| `ws-` / `aw-` | 工作区主区 / 添加工作区弹窗 |
| `au-` / `apm-` | 自动化 / 添加页面弹窗（AddPageModal） |
| `rt-` | 工作区检索 |
| `tp-` | 右栏工具面板 |
| `llm-` | 旧版角色行/高级设置（遗留） |
| `sec-` / `confirm-` / `step-` | 访问安全设置页 / danger 确认弹窗 / 计划步骤时间线 |
| `trace-` | 思考履历折叠外壳（shell/head/chevron/label/summary/body；`label.live` 用 `--primary`，暗色表头覆盖并入 `.tool-card-head` 那条规则） |
| `settings-modal-` | 设置弹窗覆盖层（overlay 遮罩 / container 居中容器 / menu 菜单外壳 / menu-head 标题+关闭 / menu-title 标题文字；暗色投影加深，移动端 96% 宽 / 92vh 高） |

- 状态点通用类：`status-dot dot-green/dot-amber/dot-red/dot-gray`。
- 弹窗通用：`.lib-modal-mask`（资料库系）/ `.slm-backdrop`（MCP）/ `.mc-mask`（连接弹窗）；`.pop-backdrop` 下拉遮罩。
- 响应式断点：≤1100px（侧栏收窄）、≤720px（移动抽屉、表单单列）。

---

## 5. 数据模型

### 5.1 data/ 文件布局

| 文件/目录 | 内容 | 管理者 |
|---|---|---|
| `.env` | `API_KEY`（必填）、可选 `LLM_BASE_URL`/`LLM_MODEL`、`CONN_CM_*_KEY`（自定义模型密钥） | config.py |
| `config.json` | 全量配置（见 §5.2） | config.py |
| `mcp.json` | `{mcpServers:{name:{transport,command,args,env,url,enabled}}}` | mcp_manager |
| `sessions.json` + `sessions/<id>.json` | 会话元数据 + 消息。元数据的 `title` 初值为 `DEFAULT_TITLE`（`"新会话"`），**这个占位值同时是 `_auto_title` 的触发条件**，不是纯显示文案（见 §3.3）。`sessions/<id>.json` **顶层是消息数组不是对象**；每条含 `role`/`content`/`id`/`timestamp`，assistant 另可带 `tool_trace`（工具痕迹）与 `meta`（思考链路快照，见 §3.3） | session_manager |
| `memories.json` | 长期记忆条目 | memory_manager |
| `pages.json` + `library/<id>/` | 资料库条目 + 二进制/网页实体 | page_manager |
| `workspaces.json` | `{workspaces, meta:{daily...}}` | workspace_manager |
| `automations.json` | `{automations:{id:rec}, runs:[...], meta:{seeded}}` | automation_manager |
| `jobs.json` | 定时任务（含 prompt 任务的 result 回写） | job_scheduler |
| `skills/*.md` | 技能卡（frontmatter: name/description/enabled + 正文） | skill_manager |
| `rag_index.json` | RAG 索引（chunks + signature + embed_model + built_at） | rag.py |
| `audit/audit-YYYYMMDD.jsonl` | 按日审计日志（route/plan/tool_call/tool_result/task…，摘要截断） | audit.py |
| `workspace/` | 智能体经 ws_write 写入的工作区根 | unified_tools |
| `cache/mcp/` | MCP npx 缓存与日志 | mcp_manager |

### 5.2 config.json schema（_DEFAULT_CONFIG）

```
ui{title,subtitle,user_name,user_avatar,bot_name,bot_avatar,executor_instructions,
   appearance{mode,tone,accent,font_scale,glow,chat_bg_kind,chat_bg}}
llm{base_url, model, temperature, max_tokens, max_tool_rounds}
providers{<name>:{base_url, api_key_env, model?, label?, kind?:"custom", created_at?}}
roles{planner,executor,executor_recovery,evaluator,memory,doc_compose,doc_parse,multimodal:
      {provider?:"default", model?:"", temperature?, max_tokens?}}
# executor_recovery = 恢复执行者：工具连续2轮全失败/执行模型报错时切换（空=与executor同源）
# 共享模型 Tab 写前 6 角色（planner/executor/evaluator/doc_compose/doc_parse/multimodal）；
# 按角色分配 Tab 写 7 角色（含 executor_recovery）；memory 不在分配 UI 中
workflow{mode:"auto"|"fast"|"standard"|"deep"|"fixed"}
retrieval{mode:"auto"|"fast"|"precise"}
connections{internal,internal_proxy:{status,last_checked,error}, custom_models:{<pid>:{...}}}
runtime{allow_export:false}
planner{enabled}  evaluator{enabled, max_rework:3}
memory{enabled, auto_extract, inject_top_k, max_items}
skills{enabled}  workspace{enabled}  jobs{enabled}  pages{enabled}
rag{enabled, chunk_size, chunk_overlap, top_k, min_score, embed_model}
auth{enabled:false, token:""}   # token 仅存 config.json；API 侧中间件统一校验
```

角色模型解析：`roles.<role>.model` 空 → 继承 `llm.model`；`provider` 空/default → llm 节 + .env 的 API_KEY；非 default → providers 条目（base_url 覆盖、api_key_env 指 .env 变量、model 覆盖）。解析失败回退 default，管道永不缺配置。

---

## 6. 依赖关系

**后端（requirements.txt）**：fastapi（Web 框架）、uvicorn[standard]（ASGI）、httpx（LLM/HTTP 客户端）、mcp>=2.1（MCP SDK，注意 is_error 属性）、pydantic v2（请求模型）、python-dotenv（.env）、truststore（内网自签证书信任）。**零数据库、零 ORM**。

**前端（web/package.json）**：react 19、react-dom、vite 7、typescript 5；无 UI 组件库、无状态库（useState/useCallback 组合）、无 CSS 框架。

**外部网络**：OpenAI 兼容网关（默认 `https://api.deepseek.com`，可配内部网关）、MCP stdio 服务器（npx 拉起，如 sequential-thinking）。

---

## 7. 红线与关键经验（开发前必读）

1. **SSE 心跳**：禁止 `wait_for(agen.__anext__())`；用生产者 task + Queue（§3.5）。
2. **MCP SDK**：`is_error` 非 `isError`；stdio 连接用 owner-task + AsyncExitStack 常驻。
3. **密钥**：只写 .env（set_env_key），绝不入 config.json/日志/响应体；响应只回 `api_key_set` 布尔。
4. **前端构建不跑 tsc**：`vite build` 缺 import 也能成功，运行时才 ReferenceError 白屏。改完必须 `npx tsc --noEmit`；构建后用 `rg -c "关键标识符" web/dist/assets/*.js` 核对产物含新代码。
5. **源文件外部覆盖事故已发生 6+ 次**：症状为 JSX 引用标识符丢失 → 白屏。修改前后各 grep 一次关键标识符；发现回退整体重写文件。
6. **浏览器缓存旧 bundle**：验证新前端 URL 带 `?v=xxx` 或 Ctrl+F5；browser_use 可能谎报操作 PASS，测后必须用 API 复核 JSON 数据文件。
7. **PowerShell 5.1**：无 BOM 的 UTF-8 .ps1 按 ANSI 解析，中文注释会毁语法 → ps1 必须带 BOM；`Set-Content -Encoding utf8` 写的 BOM 会毒化 JSON（Python json.loads 报错）→ JSON 用 Python 或 [IO.File]::WriteAllText + UTF8Encoding($false) 写。
8. **Python 解释器**：必须用完整路径 `C:\Users\quan.wan.hao.note\AppData\Local\Programs\Python\Python314\python.exe`（裸 python 进 hermes venv）。
9. **重启后端**：`Get-NetTCPConnection -LocalPort 4830` 拿 OwningProcess 强杀（Start-Process 回显 pid 与监听 pid 可能不同，以 netstat 为准）；.env 改动经界面 set_env_key 免重启，手改 .env 需重启。
10. **httpx 测试**：相对路径不能写空串（`c.post("")` 打到 `/` 得 405 误导），写全 `/api/...`；storage clean 体是 `{keys:[]}` 不是裸数组。
11. **新增功能样式**：新起 CSS 前缀（§4.3），弹窗 z-index 高于侧栏；深色主题用 `[data-theme="dark"]` 补硬编码浅色。
12. **新增后端接口**：路由文件放 app/routes/，在 main.py import + include_router；Pydantic 模型校验；manager 层 ValueError → 400；长操作（MCP 连接/网络验证）用 asyncio.create_task 后台化或直接 await 但前端给 spinner。
13. **反堆砌与代码清理**（2026-09-10 用户确立为永久规则①，**本条即全文**；流程位见 §0.2 第 0 步）：输出代码时即删冗余——重复逻辑、死导入/死变量、失效注释、为假想需求预留的分支与兼容层；**写完必须自己回头审改动块并清理，不等用户指出**。注释只在 WHY 非显然时写一行，不复述代码在做什么，不描述调用方的实现细节（调用方一改就失效）。批量清理纪律：先备份到 `data/_backup_*`、逐条留证据（前端全量 grep 零引用 / 后端端点核对 api.ts 零调用）、连带删除调用点、清理后独立复扫一遍。同名同形字段先确认语义是否真的不同，不同则不是冗余（例：`types.ts` 三处 `is_error` 分属 ToolTrace 落盘 / ChatEvent SSE / InFlightTool 流式，不可合并）。文档同受此规则约束：结构性内容只写一处，重复描述必然随代码演进而有一处过时。
14. **内网 LAN 地址在工具沙箱内不可达**：`app/tls.py` 已在 lifespan 早期注入 OS 信任链以支持内网自签 HTTPS，但沙箱网络隔离与证书信任是两回事——验证 LLM 网关（`192.168.1.128:9800`）等 LAN 地址的连通性须禁用沙箱复测，否则会把沙箱阻断误判成服务故障。
15. **`.bat` 必须 CRLF + GBK(ANSI)**（2026-09-10 实测，与红线 7 互为对照）：cmd 的批处理解析器按字节偏移读文件并假定 CRLF，**LF-only 会让偏移累积错位、从行中间开始执行**——`start.bat` 曾因此把第 10 行 `set "VENV_PYTHON=..."` 读成 `ON=.venv\Scripts\python.exe"`（丢失行首 `set "VENV_PYTH`），报 `'ON' 不是内部或外部命令` / `此时不应有 do`，venv 检测失效后掉进 `for` 循环崩溃，完全走不到启动服务。中文另需 GBK：UTF-8 中文的高位字节在 CP936 下被当 lead byte，会吞掉紧随的字符（连 `REM ` 前缀与行尾 CR 一起吞），即使换行正确仍产生 `'用法:' 不是内部或外部命令` 之类噪音。**改 .bat 禁用 Read/Edit 工具**——Read 按 UTF-8 解码 GBK 文件只得 U+FFFD 替换符（中文全部变成乱码方块），Edit 写回会毁编码；须用 Python 字节级操作：`read_bytes().decode('gbk')` → 改文本 → `.replace('\n','\r\n').encode('gbk')` → `write_bytes()`。`start.ps1` 不受此约束（PowerShell 宽容 LF，靠 UTF-8 BOM 正确解析中文）。附带教训：`grep -c $'\r' file` 在 Git Bash 下会谎报行数（对 LF-only 文件返回全部行数），**判换行必须用 `tr -dc '\r' < f | wc -c`**。
16. **验证 fail-open 后台通路要取审计、不取日志**（2026-09-11 v1.0.11 实测教训）：`_auto_title` / `memory_manager.auto_extract` 这类 fail-open 调用**失败时只留一行 `logger.info` / `warning`，成功时一行都不留**，所以「日志里没有告警」不构成成功证据，「日志里有告警」也不等于只有这一处坏了（本轮两条告警来自两个互不相干的缺陷）。更阴的是时序：`auto_extract` 是 `done` 事件**之后** `asyncio.create_task` 起的后台任务，验证脚本若在读日志前不专门等待，就会拿到空结果并误判为「模型返回 0 条事实」（本轮第一次验证正是如此）。**铁证在 `data/audit/audit-YYYYMMDD.jsonl`**：每次 `llm_call` 都落 `{at, role, model, prompt_tokens, completion_tokens, duration_ms, is_error}`，按 `role` 过滤即可确认某条后台通路是否真发过请求、用的哪个模型、成没成功（本轮据此确认 `09:06:41 role=planner ctok=8` = 标题概括、`09:06:42 role=memory ctok=16 err=None` = 抽取）。排查「某功能不工作但界面无任何报错」时，**第一步查 `GET /api/settings` 的 `roles` 映射里有没有 `(未配置)`**（空 model 为何会让整条通路静默失效，见 §3.3 `resolve_role` 条目，不在此重述）。

---

## 8. 脚本与验收工具（scripts/）

| 脚本 | 作用 |
|---|---|
| `_dev_start_server.ps1` / `_dev_stop_server.ps1` | 后台起/停 4830 服务（停服偶尔失效，配合端口强杀） |
| `mock_llm.py` | 假 LLM 网关（127.0.0.1:4831），按模型名分支 mock-planner/evaluator/memory/executor；支持 /v1/embeddings（256 维 bigram+crc32 稳定哈希向量）与结构化评估响应 |
| `_dev_launch_mock.ps1` | 后台起 mock |
| `verify.py` | 离线端到端验收 14 项（S0-S13，fixed/fast/standard/deep/工具/评估返工/job 真实执行/记忆/页面/回归/边界/RAG/automation/认证开关）；S0 自动 PUT mock 角色模型（mock-planner/executor/evaluator/memory），跑前需先起 mock（4831） |
| `_dev_dead_css.py` | 死 CSS 类检测（对比 styles.css 类选择器与 tsx/ts 字符串），清理时用；msg-user 为动态拼接误报 |
| `_dev_cleanup_restore.ps1` | 清理验收数据并恢复 config/.env 备份（注意：整删 pages/memories，真实资料场景改用按条目外科删除） |
| `_dev_online_verify.py` | 真实网关在线验收（fast 直答 + standard 工具调用） |
| `code_map_log.ps1` | **本文件维护工具**：向 §9 版本日志追加条目（见 §0.2） |

---

## 9. 版本日志

> 规则：每次开发任务完成后追加一行（脚本自动插入到表格最上方）。格式：`| 版本 | 时间 | 修改人 | 内容摘要 |`

<!-- LOG_START -->
| 版本 | 时间 | 修改人 | 内容摘要 |
|---|---|---|---|
| v1.0.18 | 2026-09-13 | Qoder | **设置页面改为平铺布局**（纯前端）。用户要求：设置页面在主页面区域内平铺展示，不以弹窗形式呈现，布局与参考图片一致。**App.tsx**：① 删除弹窗渲染逻辑（`.settings-modal-overlay` + `.settings-modal-container`）；② 主区条件渲染链改为「资料库→工作区→自动化→设置页面→ChatArea」——`settingsPage` 非 null 时在主区域渲染 `.settings-page-container` 包裹的设置子页，否则渲染 ChatArea；③ 所有设置子页 `onClose` 统一为 `() => setSettingsPage(null)`（返回聊天界面）。**styles.css**： 新增 `.settings-page-container`（`flex:1` / `min-height:0` / `overflow-y:auto` / `background:var(--bg)`）填充主区域；② `.settings-page-container .setpage` 设为 `height:100%` / `min-height:100%` 占满容器。**交互流程**：齿轮按钮 → 侧边栏展开设置菜单 → 点击菜单项 → 主区域平铺显示设置页面（ChatArea 被替换）→ 点击返回按钮 → 回到聊天界面。**验证**：`vite build` OK（bundle `index-B71jjYqg.js` 428.14 kB / `index-KoDAFuRb.css` 87.67 kB）；纯前端改动无需重启后端；浏览器 `evaluate_script` 实测 3 项全部通过——① 齿轮按钮 → 侧边栏展开设置菜单（gear-btn `.active`、settings-side 出现、ChatArea 仍显示）；② 点击菜单项 → 主区域平铺显示设置页面（settings-page-container + setpage 存在、ChatArea 消失、无 overlay 遮罩、侧边栏设置菜单仍可见）；③ 设置页面占满主区域（`flex:1` / `height:100%` 生效）。**文档**：§9 新增 v1.0.18 日志行 |
| v1.0.17 | 2026-09-13 | Qoder | **回滚设置弹窗交互至 v1.0.15 版本**（纯前端）。用户要求回滚到「设置菜单在侧边栏展开，详情页以弹窗显示」的交互模式。**SessionList.tsx**：恢复 `import SettingsPanel` 与 `import type { SettingsPageKey }`；恢复 `settingsActive` / `settingsPage` / `onOpenSettingsPage` 三个 Props；恢复条件渲染——`settingsActive` 为 true 时侧边栏内渲染 SettingsPanel（替换 nav + 会话列表），否则显示常规导航；齿轮按钮恢复 `.active` 切换。**App.tsx**：① 删除 `import SettingsPanel`（已移回 SessionList）；② SessionList 调用处恢复 `settingsActive={leftSettingsOpen}` / `settingsPage={settingsPage}` / `onOpenSettingsPage={(page) => setSettingsPage(page)}` 三个 props；③ `onToggleSettings` 恢复为 toggle `leftSettingsOpen`；④ 弹窗渲染条件由 `leftSettingsOpen` 改回 `settingsPage`——只有选中具体设置页时才显示弹窗；⑤ 所有设置子页 `onClose` 由 `() => setSettingsPage(null)`（返回菜单）改回 `closeSettings`（关闭整个弹窗 + 侧边栏菜单）；⑥ 删除 `.settings-modal-menu` 包装层渲染。**styles.css**：删除 v1.0.16 新增的 `.settings-modal-menu*` 系列样式（menu / menu-head / menu-title / menu .settings-side / 移动端 media query）。**验证**：`vite build` OK（bundle `index-BLBNR7hV.js` 428.14 kB / `index-CAwdiqQ-.css` 87.53 kB）；纯前端改动无需重启后端；浏览器 `evaluate_script` 实测 5 项全部通过——① 齿轮按钮 → 侧边栏展开设置菜单（11 个 `.sm-item`、gear-btn `.active`、无 overlay）； 点击菜单项 → 弹窗打开详情页（overlay + container + setpage 存在、侧边栏设置菜单仍可见）；③ 点击遮罩 → 弹窗关闭 + 侧边栏恢复会话列表（gear-btn 失去 `.active`、settings-side 消失）；④ 再次点击齿轮 → 设置菜单重新展开；⑤ 切换齿轮按钮可正常 toggle 设置菜单显示/隐藏。**文档**：§9 新增 v1.0.17 日志行 |
| v1.0.16 | 2026-09-13 | Qoder | **设置弹窗改为独立弹窗，侧边栏不再展开设置菜单**（纯前端）。用户纠正交互规则：点击侧边栏设置按钮，设置页面以独立弹窗形式唤起，不可在侧边栏区域内展开。**SessionList.tsx**：删除 `import SettingsPanel`、删除 `settingsActive` / `settingsPage` / `onOpenSettingsPage` 三个 Props 及解构参数；删除 `settingsActive` 条件分支（原侧边栏内渲染 SettingsPanel 的整块 ternary），侧边栏始终只显示会话列表；齿轮按钮去掉 `.active` 切换。**App.tsx**：① 新增 `import SettingsPanel`；② SessionList 调用处删除 `settingsActive` / `settingsPage` / `onOpenSettingsPage` 三个 props；③ `onToggleSettings` 改为 `setLeftSettingsOpen(true)`（只开不关，弹窗由内部关闭按钮或遮罩关闭）；④ 弹窗渲染条件由 `settingsPage` 改为 `leftSettingsOpen`——无 `settingsPage` 时渲染 `.settings-modal-menu`（标题「设置」+ ✕ 关闭按钮 + SettingsPanel 菜单），有 `settingsPage` 时渲染对应设置子页；⑤ 所有设置子页 `onClose` 由 `closeSettings`（关闭整个弹窗）改为 `() => setSettingsPage(null)`（返回菜单，不关闭弹窗）。**styles.css**：新增 `.settings-modal-menu`（flex 纵向 / `max-height:85vh`）、`.settings-modal-menu-head`（flex 水平间距 / `padding:16px 20px 8px`）、`.settings-modal-menu-title`（16px/600）、`.settings-modal-menu .settings-side`（覆盖原侧边栏宽度为弹窗适配 / `padding:8px 16px 20px`）、移动端 `@media(max-width:720px)` 放宽至 92vh。**验证**：`vite build` OK（bundle `index-BT0_3sjD.js` 428.37 kB / `index-BT0_3sjD.css` 87.94 kB）；纯前端改动无需重启后端；浏览器 `evaluate_script` 实测 5 项全部通过——① 齿轮按钮 → 弹窗打开含菜单（overlay + container + menu 存在、sidebar 无 settings-side）；② 点击菜单项「主题与外观」→ 弹窗内切换为详情页（setpage 出现、menu 消失）；③ 详情页返回箭头 → 回到菜单（menu 重现、setpage 消失）；④ 点击遮罩 → 弹窗完全关闭；⑤ 菜单标题栏 ✕ 按钮 → 弹窗完全关闭。**文档**：§4.1 渲染链与齿轮按钮描述同步更新、§4.3 CSS 前缀补 `settings-modal-menu` 系列 |
| v1.0.14 | 2026-09-13 | Qoder | **开发 7 项受限能力，新增 12 个内建工具（18→30）**。用户从能力评估表识别出 7 项「受限/不可用」功能并授权开发。**新增工具**：① 文档生成 4 个——`doc_generate_excel`（openpyxl 多 sheet + 表头样式 + 自动列宽）、`doc_generate_word`（python-docx 标题/段落/列表/表格）、`doc_generate_ppt`（python-pptx title+content / title_only 布局）、`doc_generate_pdf`（fpdf2 带页眉页脚 + 标题/段落/列表/表格）；② `doc_import`——外部文件拷入工作区并自动调 doc_parser 解析为 Markdown（支持 auto/text/tables/structure 模式）；③ `workspace_delete`——删除工作区文件/目录（danger 确认门；阻止删除工作区根目录）；④ `bash_execute`——执行 shell 命令（danger 确认门；危险命令黑名单如 `rm -rf /`、`mkfs` 等；timeout 60s、输出截断 10000 字符）；⑤ `file_export`——工作区文件导出到外部路径（系统目录黑名单 C:\\Windows / /etc 等）；⑥ `web_search`——DuckDuckGo HTML 搜索（httpx + 自定义 HTMLParser）；⑦ 技能开发 3 个——`skill_create`（创建技能卡 + triggers 写 frontmatter）、`skill_update`（更新 description/body/triggers/enabled）、`skill_validate`（格式校验：description/body 长度、trigger 数量/长度、body 关键词检查）。**依赖**：`requirements.txt` 新增 `fpdf2>=2.7,<3`（已 `pip install`）。**安全**：danger 门（workspace_delete / bash_execute）、路径遍历防护（复用 `_ws_resolve`）、系统目录黑名单（file_export）、危险命令正则（bash_execute）。**文档**：§3.4 工具表 18→30 全量更新（注册名/说明）；§9 新增 v1.0.14 日志行。**需重启**（改动 `app/unified_tools.py`） |
| v1.0.15 | 2026-09-13 | Qoder | **设置页面改为弹窗覆盖模式**（纯前端）。用户要求：点击侧边栏左下角设置按钮后，设置子页以弹窗形式展开在主区域上方，而非替换主区域内容。**App.tsx**：① 新增 `closeSettings()` 回调——同时清 `settingsPage` 与 `leftSettingsOpen`，关闭弹窗时同步收起侧边栏设置菜单；② 主区条件渲染链由「资料库→工作区→自动化→设置子页(11选1)→ChatArea」改为「资料库→工作区→自动化→ChatArea」，设置子页拆出为独立覆盖层——`settingsPage` 非 null 时渲染 `.settings-modal-overlay`（全屏遮罩，点击关闭）+ `.settings-modal-container`（居中弹窗，`position:fixed` / `z-index:51` / `max-width:720px` / `max-height:85vh` / `border-radius:14px`），11 个设置页在容器内按 key 条件渲染，所有 `onClose` 统一接 `closeSettings`。**styles.css**：新增 `.settings-modal-overlay`（`position:fixed` 全屏 / `rgba(35,40,59,0.38)` 半透明遮罩 / `z-index:50`）、`.settings-modal-container`（`translate(-50%,-50%)` 居中 / 圆角 14px / 投影 `0 12px 48px`）、`.settings-modal-container .setpage`（`height:auto` + `max-height:85vh` 覆盖原 100% 高度）、暗色主题投影加深、移动端 `@media(max-width:720px)` 放宽至 96% 宽 / 92vh 高。**验证**：`tsc --noEmit` 零报错、`vite build` OK（bundle `index-BH-0Mawu.js` 428.36 kB / `index-CAwdiqQ-.css` 87.53 kB）；纯前端改动无需重启后端；浏览器 `evaluate_script` 实测 5 项全部通过——① 弹窗正确渲染（overlay + container + setpage 三层结构存在、`position:fixed` / `z-index:51` / `border-radius:14px` / `box-shadow` / `max-width:720px` / `max-height:85vh` 全部生效）；② ChatArea 在遮罩下方保持可见；③ 点击遮罩背景 → 弹窗消失 + 侧边栏恢复会话列表（`.side-nav` 重现、`.sb-settings-head` 消失、`.gear-btn` 失去 `.active`）；④ 弹窗内返回按钮 → 同样关闭弹窗 + 恢复会话列表；⑤ 不同设置页（主题与外观 / LLM 配置）均可正常在弹窗内打开。**文档**：§4.1 主区渲染链与齿轮按钮描述同步更新 |

| v1.0.13 | 2026-09-11 11:50 | Qoder | **实现 YOLO 模式：盾牌按钮切换 + 跳过 danger 确认门**。用户要求：任务窗口输入区的安全（盾牌）按钮点击后启用 YOLO 模式，开启时跳过危险工具的人工确认弹窗。**后端**：① `config.py` runtime 节新增 `yolo_mode: False` 默认值；② `settings.py` GET 端点返回 `yolo_mode`、PUT 端点支持写入 `yolo_mode`（SettingsUpdate 补字段 + PUT 逻辑）；③ `orchestrator.py` danger 确认门 L229-230 插入检查——YOLO 开启时直接跳过挂起等待，工具照常执行。**前端**：① `types.ts` Settings / SettingsPut 补 `yolo_mode` 类型；② `App.tsx` 新增 `handleToggleYolo` 回调（调用 `api.saveSettings({ yolo_mode })` + 本地状态同步），传给 ChatArea；③ `ChatArea.tsx` Props 接口补 `yoloMode/onToggleYolo`，盾牌按钮接线 onClick，title 动态切换（「安全：点击启用 YOLO 模式」↔「YOLO 模式：已跳过安全确认」）； `styles.css` 新增 `.ci-icon--yolo` 三态样式（浅色黄 `#e6a817`/背景 `#fff8e1` → hover `#fff3cd`/`#d4940f`；暗色对称 `#f0c040`/`#3a3020` → hover `#453a28`）。**验证**：`tsc --noEmit` 零报错、`npm run build` OK（bundle `index-tmXpItat.js` 428.26 kB / gzip 122.51 kB）；浏览器 `evaluate_script` 实测：点击关闭 → `yolo_mode: false`、样式恢复默认灰色、title 变回「安全：点击启用 YOLO 模式」；点击开启 → `yolo_mode: true`、样式变黄色 `.ci-icon--yolo`、title 变「YOLO 模式：已跳过安全确认」。服务需重启（改 `app/config.py` / `app/routes/settings.py` / `app/orchestrator.py`），PID 44944（2026-09-11 11:47 启动），API 实测 PUT/GET 均正常。**文档**：§4.1 补盾牌按钮条目说明 YOLO 功能与样式、§9 新增 v1.0.13 日志行、§10 刷新 PID |

| v1.0.12 | 2026-09-11 10:30 | Qoder | **任务履历删除按钮样式对齐编辑按钮**（纯前端）。用户要求：删除（X 号）按钮默认常驻浅色背景，无需 hover 才显示。修改 `styles.css`：`.session-del` 补齐三态（默认浅红 `#fdeeee` + `var(--red)` 文字 → hover `#fbdcdc` → active `#f9cccc`），与 `.session-rename` 的浅绿三态对称；暗色主题同步覆盖（默认 `#3a2630` / hover `#452d38` / active `#503540`）。`npm run build` 成功（bundle `index-k-OEd_ZI.js` 427.91 kB / `index-CSVlv4d7.css` 86.71 kB）；浏览器 `evaluate_script` 实测 CSS 规则全部生效，默认背景色常驻。前端-only 改动无需重启后端。**文档**：§4.1 补 SessionList 按钮样式说明 |
| v1.0.11 | 2026-09-11 09:07 | Qoder | **修复两条后台 LLM 通路长期静默失效**（用户贴出服务日志发现）。**缺陷 A（自动命名 100% 失败）**：`orchestrator._auto_title` 接收 `run_turn` 的 `cfg`，而那个 `cfg` 是 `load_config()` 返回的**整份 config.json**（顶层只有 `llm` / `roles` / `memory` 等节，没有 `base_url` / `model` 键），`complete_chat` → `_check_cfg` 查 `cfg["base_url"]` 必为空 → 抛「未配置网关地址（config.json → llm.base_url 或 .env → LLM_BASE_URL）」，fail-open 只留一行 `logger.info`，UI 上表现为**自 v1.0.9 引入以来所有会话标题恒为「新会话」**、无人知晓原因。修法：删掉 `cfg` 形参，函数内部改用 `cfg=resolve_role("planner")`——与该函数注释声明的 planner 语义一致，也与 `planner.py` / `evaluator.py` / `rag.py` / `memory_manager.py` 等**其余全部** LLM 调用点一致（grep 全库确认这是唯一一处误传）；两处调用点同步去参（fixed 层 L362、standard/deep 层 L538）。**缺陷 B（记忆自动抽取从未工作）**：`roles.memory.model` 为空，而回退终点 `llm.model` **也**为空（当前部署刻意留空、模型全靠 roles 逐个指定）→ `auto_extract` 每轮抛「未配置模型名」。修法：经 `PUT /api/settings` 把 `roles.memory.model` 设为 `gemma4-26b-a4b`（与 planner / evaluator / doc_compose / doc_parse / multimodal 同档轻量模型）；**刻意走 API 而非直接改磁盘**——该路径调 `save_config()` 刷新进程内 `_config` 缓存，免重启且避开「API 写回会覆盖手改文件」的陷阱；写后核验 `providers` 节（deepseek 自定义模型 `cm_8d81ae73`）与 `data/.env` 均未被写坏、其余 7 个角色未被触碰。**§10 网关状态更正**：此前记录的「`192.168.1.128:9800` TCP 超时、无任何可用 LLM 通路」**已作废**，本轮 09:04~09:06 实测多次 `HTTP 200`，`gemma4-26b-a4b` / `qwen3.8-27b` 两档均真实可用。**验证（重启后真实模型往返，非桩件）**：`scripts\_dev_start_server.ps1` 起服务（监听 PID 34692；`Start-Process` 回显 37776 与监听 PID 不同，以 `Get-NetTCPConnection` 为准）；第一轮 prompt 过于开放 → 评估者返工烧到预算耗尽、回合以 `paused_human` 收尾，而 `auto_extract` 只在**非 paused** 分支触发（L556-567，paused 时 `return` 早于抽取），故换成自带可提取事实的短问答重跑；第二轮 `state=done`，标题被概括为「解释指数退避重试概念」。**铁证取自审计而非日志**：`data/audit/audit-20260911.jsonl` 两条新记录——`09:06:41 role=planner model=gemma4-26b-a4b ctok=8`（标题概括成功）、`09:06:42 role=memory model=gemma4-26b-a4b err=None ctok=16`（抽取真实调用成功）；`data/cache/server.err.log` 全程零 WARNING/ERROR，末行「自动抽取记忆 2 条」，**原两条告警彻底消失**。**时序教训**：`auto_extract` 是 `done` 之后 `asyncio.create_task` 的后台任务，验证脚本若在读日志前不专门等待就会漏判其成败（本次第一轮脚本正是因此给出空结果），最终以审计文件确认。**副作用与清理**：验证期间执行者主动调记忆工具写入 1 条、`auto_extract` 蒸馏 2 条（「用户昵称是K哥」「习惯使用Python编写后端」）均属测试污染，经 `DELETE /api/memories/{id}` 全删，记忆库回到原有 3 条；2 个测试会话经 `DELETE /api/sessions/{id}` 删净（会话数回到 7）；临时脚本 `scripts\_dev_verify_title_memory.py` 用毕即删零残留。**已知遗留（属设计非缺陷）**：标题仍为「新会话」的 5 个历史会话**不会被补命名**——`_auto_title` 只在该会话有新回合时触发，需用户再发一轮消息。**文档**：§3.3「会话自动命名」与 `resolve_role` 两条目同步真实签名与空 model 的静默失效形态、§10 刷新 PID / 网关实况 / memory 角色 / 用户数据现状 |
| v1.0.10 | 2026-09-11 00:07 | Qoder | **思考履历区块：执行中实时展开、回合结束后自动折叠**（纯前端）。用户 UI 规则两条：① Agent 执行任务过程中实时输出并展示思考过程、保持展开状态；② 本次任务思考逻辑执行完毕、任务结束后自动折叠思考履历区块。实现（`ChatArea.tsx` + `styles.css`）：新增 `ThinkingTrace` 折叠外壳包住 `PipelinePanel` + 工具卡片，流式与历史两个渲染点共用；**核心是 `useState(!!live)`**——流式挂载即展开、历史挂载即折叠，折叠时机因此不需要任何新状态字段或 SSE 协议改动：流式块 `{streaming && …}` 与历史消息行属不同 React 子树，回合结束 `openSession` 重载后前者卸载、后者以新 key 挂载，初值自然取 false。折叠态由 `traceSummary()` 给出一行摘要（层 / N次工具含失败数 / 最后一次评估结论 / `⚠ 待人工`），**转人工警示刻意进摘要**，否则折叠后用户看不到本轮其实没通过验收；正文（答案）留在壳外，折叠不吞答案。渲染守卫：历史放宽为 `m.meta \|\| m.tool_trace?.length`（老会话无 meta 但有工具痕迹时也收进壳），流式恒渲染——表头「思考中…」本身即实时指示器，**取代了原 `.thinking` 占位 div**（连带删掉 styles.css 里的死样式）。顺带清理三处：工具成败判定抽为 `traceFailed(t)` 供渲染点与摘要共用（此前只活在渲染点）；暗色表头覆盖并入既有 `.tool-card-head` 规则而非新增一条；自查删掉 `trace-shell` 上照抄 tool-card 习惯拼接的死类名 `open`（CSS 无对应规则）。新增 `trace-` 前缀 6 条 CSS + 一条内部块 margin 归零（外壳已用 flex gap 控距，否则与 `.pipeline-strip`/`.stage-metrics`/`.step-timeline` 自带的 8px 下边距叠加）。**刻意不合并**流式与历史两处 ToolCard 渲染：`ToolTrace` 与 `InFlightTool` 两种形状的 content/isError/elapsedMs 推导方式不同，合并需归一化适配层，得不偿失。验证：`tsc --noEmit` 零报错、`vite build` OK（bundle `index-BNJTNSrG.js` 427.91 kB / gzip 122.35 kB）；后端在 4830 同时 serve dist，**纯前端改动无需重启**（`index.html` 即刻引用新哈希，实测已生效）。浏览器 `evaluate_script` 实测规则 ②：打开会话 `eb26e7857a22`（13 消息）→ 10 个 `.trace-shell` **全部折叠**（chevron 全 `▸`、openCount=0），摘要为「1次工具」…「层:standard · 评估未过 · 0分 · ⚠ 待人工」，3 条答案 `.md-body` 仍在壳外可见；点开 standard 那条 → chevron 变 `▾`，壳内完整回看 `pipeline-strip`（层:standard / 三角色 chip / 计划链 workspace_list → workspace_read → sequential-thinking__sequentialthinking → s4）+ 4 条红色 fail EvalStrip（各 0 分、1~4 项未过）+ `⚠ 待人工` + 19 个 stage chip，且 **step-item = 0**（`step_states` 未落盘 → 条件门正确拦住误导性全 pending 时间线，**§10 待办 2 就此闭合**）；再点折回 → `▸` + 摘要重现。实测规则 ①：草稿态发送真实一轮 → **200ms 内壳出现且 `label=思考中… / live=true / open=true / ▾`**，壳内实时刷新 `层:standard`、`*执行者`（角色高亮迁移）、`规划 · 48.1s · 兜底`（网关超时致规划器走兜底计划 s1）、步骤时间线 1 步，持续 11s+ 保持展开；点「停止生成」后壳随流式块卸载（`.trace-shell` 归零），界面不残留展开态。**验证缺口**：「同一轮从展开态原地折叠成历史态」的过渡**未能观察**——该轮因网关不可达必然以 error/cancelled 收尾，而 `orchestrator.py` 的 error（L452-454）与 cancelled（L411 / L456 / L464）路径都直接 return、**不写带 meta 的 assistant 消息**，故重载后没有可折叠的历史壳；过渡正确性由两端形态均已在真实 DOM 上确认（live 展开 / 历史折叠）+ 卸载重挂载属 React 语义保证这两点支撑，网关恢复后应补一次成功回合的过渡观察。测试产生的会话 `ac8bd12128e7` 已删净（回到 8 个，未触碰用户两个既有空会话）。**文档**：§4.1 新增 `ThinkingTrace` 条目并修正 `PipelinePanel` 条目里「内部结构 …→ 工具卡片 → 正文」的失实描述（两者都不是它的子节点）、§4.3 补 `trace-` 前缀、§10 刷新 bundle 与待办、§11.2 记折叠时机与不合并 ToolCard 的决策原因、§11.3 记验收结论与缺口 |
| v1.0.9 | 2026-09-10 23:52 | Qoder | **任务履历改为「任务真正启动后才出现条目」+ 标题由会话输出自动概括**。用户要求：点侧边栏「新任务」不要立刻在履历建记录，等右侧任务真正启动运行后再生成条目，名称由本次会话输出结果自动概括。用户三项决策：标题复用 planner 角色（不新增 titler）／概括失败保持「新会话」下轮重试（不回退为首条消息前 20 字）／草稿态选文件时就建会话（不禁用附件按钮）。**后端**：`session_manager` 提出模块级 `DEFAULT_TITLE = "新会话"`（消除魔法字符串，`create_session` 改用它）；`orchestrator` 新增 `_auto_title(session_id, cfg, user_text, answer)`——标题仍等于 `DEFAULT_TITLE` 时用 `complete_chat(role="planner")` 概括短标题写回 `update_title`，fail-open（异常仅 `logger.info`）；**触发条件只有「标题仍是占位值」这一条，同时实现只命名一次 / 不覆盖用户手动改名 / 失败下轮自动重试，零新增字段**；两个调用点：fixed 层在 `delta` 与 `done` 之间，standard/deep 层在 `append_messages` 之后、`if paused:` 之前（一处覆盖 `done` 与 `paused_human`）。**前端**：`App.tsx` 引入**草稿态**（`currentId === null`）——`enterDraft()` 承接「新任务」按钮 / 首屏无会话 / 删掉最后一个会话三处，只清状态不建会话；`ensureSession()` 是落地会话的唯一入口（`handleSend` 开头 + ChatArea 选附件），建完只 `setCurrentId`、**刻意不刷新侧边栏**；新增 SSE `start` 事件分支触发 `refreshSessions()`，条目此刻才出现；`handleSend` 去掉 `!currentId` 硬阻断（此前草稿态会静默吞掉用户输入），改用局部 `sid` 贯穿 `streamChat` 与 finally 的 `openSession`。顺带清理：`refreshSessions` 返回会话列表，消除初始化与删除会话两处对 `api.listSessions()` 的重复请求；`openSession`/`enterDraft` 共用的「关面板清错误」抽成 `leaveView()`。`ChatArea.tsx`：Props 新增 `ensureSession`；`onFiles` 去掉 `!currentId` 提前返回，改为过完数量校验后 `const sid = currentId` 或 `await ensureSession()`；**「切换会话清空未发送附件」effect 用 `prevSid` ref 放行 `null→id`**——草稿态选附件正是靠这次落地建会话，当成切换会把刚选好的文件清掉（本设计唯一非显而易见的坑）。**验证**：`compileall` OK；`tsc --noEmit` 零报错；`vite build` OK（bundle `index-DcQwOR1d.js` 426.70 kB / gzip 122.02 kB）；服务于 23:38:34 重启（新 PID 见 §10）。**桩件测出并修掉一个真 bug**：标题清洗原为 `raw.strip().strip(引号).split(换行)[0]`，先剥引号只能去掉整串最外层——模型输出「引号标题 + 换行 + 解释」时行尾引号夹在串中间剥不掉、会残留进侧边栏，改为先裁首行再剥引号。8/8 桩件用例通过（裸标题 / 带引号换行 / 中文书名号 / 超长截断 24 字 / 空输出不写 / 不覆盖手动命名 / 异常 fail-open / 会话不存在静默返回）。浏览器实测（用 `evaluate_script`，`click` 与 `take_screenshot` 均被 viewport 不可用阻断）：点「新任务」→ 卡片数 8 不变、active=0、后端会话数仍 8（**零创建**）；草稿态发送 → **700ms 内卡片 8→9 且新条目高亮**；草稿态选附件 → chip 立即显示、卡片数仍为 9（条目未提前出现）、附件未被 `null→id` 清掉；取消回合后标题留在「新会话」；重载页面 → 8 卡片并打开 list[0]，点开「能力边界」正常渲染 14 个消息元素（`openSession` 经 `leaveView` 重构后无回归）。测试产生的 2 个会话已删除（回到 8），临时脚本用毕即删零残留。**验证缺口**：① 真模型标题生成**未验证**——内网网关 `192.168.1.128:9800` TCP 超时（gemma4-26b-a4b / qwen3.8-27b / gpt-oss-120b 三档各重试 3 次全失败），备用 deepseek provider 的 `CONN_CM_8D81AE73_KEY` 在 .env 中未设置，当前无任何可用 LLM 通路；红线禁止改 live config 的 roles/providers，故只在**进程内存**里覆盖 `config._config` 试过一次（磁盘全程未动），因密钥缺失同样失败——该次失败反向实证了 fail-open 在真实鉴权错误下不抛异常、标题安全留在占位值。② 故「标题文案质量 / 真实模型是否输出多余前后缀」待网关恢复后确认。③ 顺带发现一个**本轮未修**的既有缺陷：SSE `error` 事件写入的 `chatError` 会被 finally 里 `openSession()`→`leaveView()` 的 `setChatError(null)` 立刻抹掉，错误横幅实际永不显示（改动前即如此，不属本轮范围，待用户点头再修）。**文档**：§3.3 补自动命名条目、§3.5 补 `start` 语义、§3.6 session_manager 行补 `DEFAULT_TITLE`、§4.1 补草稿态生命周期与代价、§5.1 补 title 语义并修正 streaming 类型笔误（实际不含 sessionId）、§10 全量刷新、§11.2 记三项决策原因、§11.3 记验收结论与缺口 |
| v1.0.8 | 2026-09-10 23:07 | Qoder | **修复 `start.bat`（此前完全无法运行）+ 补齐文档遗漏**。用户问「start.bat 是否可正常使用」，实测答案是否，三处缺陷：① **致命**——文件是 LF-only 换行（`tr -dc '\r' \| wc -c` = 0；注意 `grep -c $'\r'` 在 Git Bash 下会谎报为全部行数，不可用于判换行），cmd 批处理解析器假定 CRLF、按字节偏移读文件，LF-only 致偏移累积错位、从行中间执行：第 10 行 `set "VENV_PYTHON=%ROOT%.venv\Scripts\python.exe"` 被读成 `ON=.venv\Scripts\python.exe"`（丢失行首 `set "VENV_PYTH`），报 `'ON' 不是内部或外部命令` / `找不到文件` / `此时不应有 do`，venv 检测失效后掉进 `for` 循环崩溃，走不到启动服务；② **中等**——中文以 UTF-8 保存而控制台代码页为 936(GBK)，高位字节被当 lead byte 吞掉紧随字符（含 `REM ` 前缀与行尾 CR），只修换行仍有 `'用法:'` / `'动]' 不是内部或外部命令` 噪音；③ **轻微**——第 60 行 hash 比对大小写敏感，而 `certutil -hashfile` 输出小写、`.venv\.deps-hash` 由 `start.ps1` 的 `Get-FileHash` 写成大写，同一哈希被判不同 → 每次从 ps1 切到 bat 白跑一次 `pip install`（离线时可能 `exit /b 1` 起不来）。修法（用户选定「CRLF + GBK」）：LF→CRLF、UTF-8→GBK 重编码（2534→2471 字节，sha256 `ea24e253`→`5fc8eda7`）、第 60 行 `if not`→`if /i not`。验证：两条路径零副作用干跑（pip 安装 / marker 写入 / venv 创建 / 服务启动四处替换为 echo，探针用毕即删）——正常路径零语法报错、中文正常显示、**`NEED_INSTALL=0`**（`/i` 生效）、`PYTHON` 正确解析为 `.venv\Scripts\python.exe`；首次使用路径（强制 venv 缺失）的 `for` 循环含 `%%c` / `2^>^&1` / `findstr /r "3\.[1-9][0-9]*"` / 嵌套括号块全部正常解析并成功找到 Python。对照实验确证根因：纯 ASCII 版仅报探针截断导致的「找不到标签」，UTF-8+CRLF 版有 2 处中文噪音，GBK+CRLF 版零报错。副作用核验：`.venv\.deps-hash`、`data\.env`、`data\config.json` 内容与 mtime 全部未变，无游离 venv 目录，探针清零。文档：§7 新增红线 15（.bat 必须 CRLF+GBK；改 .bat 禁用 Read/Edit，须 Python 字节级 `decode('gbk')`/`encode('gbk')`；附 `grep -c $'\r'` 谎报教训）、§1 入口行与 §2 目录树补 `start.bat`/`start.sh`（此前目录树只列 `start.ps1`，属本轮实测发现的文档遗漏）、§11.1 补备份行、§11.2 记编码选型原因、§11.3 记验收结论与缺口。备份：`data/_backup_start_bat_fix_20260910/start.bat.pre-fix`（2534 字节 LF+UTF-8 原文件，拷回即还原）。**仍需重启**：本轮未改 `app/`，§10 待重启三文件结论不变；用户可直接用修好的 `start.bat` 或 `.\start.ps1` 重启 |
| v1.0.7 | 2026-09-10 22:55 | Qoder | **文档合并 + 两处真实缺陷修复**。文档：按用户决定「只保留一份文档」把 project_memory.md（190 行）并入本文件后删除，§0.4 由「两文件分工」重写为**单文档三分区**方法论（结构事实随代码覆盖 / 红线经验可修订 / 易失状态即时覆盖 / 历史叙事一旦写下不改写）并附归属判定两问与合并时实测的 6 处过时描述清单（内建工具「六类」实为 8 类 18 个、evaluator 输出实为 `{passed,score,failures,feedback,fallback}`、roles 实为 8 角色、SSE 清单缺 round/step_update/confirm_request、配置 schema 与 API 一览不全）——作为分区必要性的实证；新增 §10 当前运行状态与待办（实测 PID/网关实况/bundle/用户数据现状）与 §11 交付决策与回滚索引（备份表 / 决策原因 7 条 / 验收结论 / 「任务无限重复运行」诊断叙事）；§7 新增红线 14（内网 LAN 地址在工具沙箱内不可达，`tls.py` 注入 OS 信任链 ≠ 沙箱网络可达）；§2 目录树删除 project_memory.md 行；§9 三条历史日志中对 project_memory 的引用按「不改写历史」原则保留。代码：① `tool_registry._CATEGORY_GATE` 的 key `"kb"` → `"rag"`，修复 gate key 与工具真实 `category="rag"`（`unified_tools.py`）错位导致 `.get("rag")` 返 None、门控静默短路，`rag.enabled=false` 对 `kb_search`/`kb_answer` 完全无效；内存态 5/5 验证（开→全在 `_defs`+`has()` True，关→全排除，其他 5 类不受影响），`data/config.json` sha256 前后一致证明未写盘。② `orchestrator.py` danger 拒绝路径 `is_error` 由 False 改为 True 且补进 trace，修复同一事件前端流式渲染绿点成功 / 历史回退 content 前缀渲染红色报错的双相矛盾，并使「本轮全部工具调用均失败 → 切 executor_recovery」对被拒工具恢复生效（此前被计入 ok_tools 而永不触发）；5 场景回放 5/5 通过。③ §3.4 内建工具表由 handler 函数名（`ws_read`/`sk_list`/`mem_save`）改为实测**注册名**（`workspace_read`/`skill_list`/`memory_save`），此即 §3.3 命名轴错位的第三条轴；§0.2 第 4 步补该纪律。备份：`data/_backup_doc_merge_20260910/`（project_memory.pre-merge.md 190 行 / code_map.pre-merge.md 479 行）。验证：compileall OK、临时验证脚本用毕即删零残留。**需重启**（改动 orchestrator.py 与 tool_registry.py，监听 4830 的 PID 29636 启动于 22:02:01，早于两处改动） |
| v1.0.6 | 2026-09-10 22:18 | Qoder | 思考链路可见化+持久化，并修复规则层误判导致的返工预算白烧：编排层新增 `round{round,chars,ms,tool_calls,final}` 事件、plan/eval/tool_result 补 ms 与 fallback、回合结束把 `{tier,plan,evals,stages,step_states,state}` 作为 meta 附在 assistant 消息落盘（meta 不进 LLM 上下文，`_expand_tool_trace` 白名单隔离）、新增 eval_degraded 记忆门禁（未经验收的回答不沉淀长期记忆）；**评估器新增 `_trace_names()` 归一化三条命名轴**（MCP 被 `info()` 剥 server 前缀 / 内建保留 `category__name` 全名 / `rebuild()` 的 hidden 短别名），修复「工具已成功调用却判未调用」——审计 20260909 10:47 三次同因 rule FAIL 实证，3 次返工 100% 无效；`tool_trace` 补 `is_error`（此前只进事件不进 trace，使「本轮全部工具调用均失败」检查永不触发、报错工具反计入成功集），danger 拒绝路径 is_error 口径统一为 True（与 `content.startswith("Error:")` 全局约定及连续失败切恢复执行者的判定一致）；前端新增 `PipelinePanel` 共享组件（流式与历史两处复用，空面板保护 + StepTimeline 条件门避免误导性全 pending 时间线）与 `StageMetrics` 每轮字符数/耗时展示，types.ts 新增 StageMetric/MessageMeta/PipelineState、ToolTrace 补 is_error/ms；确立 project_memory.md「永久规则」章节（① 禁代码堆砌+生成后主动自查清理 ② code_map 同步为固定流程）；§3.3/§3.5/§4.1/§5.1 同步，清理 §5.1 失效的 OPENROUTER_API_KEY（全库 grep 零引用）；验证：compileall OK、tsc --noEmit=0、vite build（bundle index-Cd4kjofT.js 426.43 kB / gzip 121.89 kB）、8/8 真实落盘数据回放对照通过（含负向场景确认未放宽判定） |
| v1.0.5 | 2026-09-06 16:40 | TRAE | 生产级升级批次一至四全量落地：编排层新增固定工作流(fixed_flows)+结构化计划(steps绑定step_update事件)+两层评估(规则score/failures+语义LLM)+danger高危确认门(confirm端点120s超时)；工具网关(参数校验/超时/审计audit.py)；RAG引擎(rag.py BM25+向量RRF混合/kb工具/低置信拒答)；job与automation接task_runner真实LLM执行通道(并发闸门/超时/结果回写含session_id)；访问认证(main.py中间件+/api/auth三端点回环保护)；前端补齐StepTimeline步骤时间线+EvalStrip评分展示+ConfirmDialog确认弹窗+AccessSecurityPage访问安全页+streamChat认证头；修复chat.py ConfirmReq未定义与AutomationPanel failed/error类型比较；API 58→66；verify.py扩至14项全PASS；tsc/vite build通过 |
| v1.0.4 | 2026-09-06 10:01 | TRAE | 移除内置 OpenRouter 模型连接（用户要求删除管理模型连接弹窗中的 openrouter 项）：connections.py 删 BUILTIN_PROVIDERS openrouter 定义及 _builtin_endpoint/_builtin_key_set/save_key 中 OPENROUTER_API_KEY 分支（两个辅助函数收敛为无参）、响应与前端 action 字段同步移除（types.ts ConnProvider 删 action、弹窗 connect/配置 死分支与网关地址条件收敛）；config.py 默认 connections 与 live config.json 的 openrouter 状态项清除；.env 本无该密钥；§3.7/§5.1/§5.2 同步（内置提供商 3→2）；备份 data/_backup_openrouter_removal_20260906/（连接信息清单+config+.env）；pyflakes/tsc/vite build 全过、新 bundle index-aRo26KZf.js 无 OpenRouter、/refresh 实测两项内部 LLM 保持 connected、浏览器验证弹窗仅剩两张内部卡+自定义区 |
| v1.0.3 | 2026-09-06 09:15 | TRAE | 全项目冗余代码清理：后端 pyflakes 6→0（删死端点 POST /connections/{key}/verify、Any/threading 死导入、global_status 死变量、无占位符 f-string；memory_manager _enforce_cap 顺带修复 auto 淘汰不足时手动条目不淘汰的潜在 bug）；前端删 api.ts 死方法 connectionVerify/createPage，styles.css 删约 50 条旧 UI 死规则（361 行，CSS bundle 84.82→80.27 kB）；§3.7 端点表 59→58 同步删 verify 行；§7 新增红线 13「代码清理/反堆砌规则」（备份/逐证据/CSS 修剪/连带删除/独立复扫/验收门槛/外科式清 mock 数据）；verify.py 补强为自包含（自动配置 mock 角色模型、S0 断言改包含校验）；mock 验收 11/11 PASS，环境已恢复真实 DeepSeek 配置 |
| v1.0.2 | 2026-09-06 08:21 | TRAE | 补齐与 project_memory 比对发现的 5 处语义缺口：job/automation 仅留痕不执行真实 LLM、workspace 无 watcher 零值语义、推送开关仅存偏好不外发、zip-slip 防护 is_relative_to、React19 无 JSX 命名空间用 ReactElement；§0.4 新增两文件分工说明（code_map=结构事实，project_memory=叙事记忆/易失状态，均保留）；修正设置子页计数 11→10 |
| v1.0.1 | 2026-09-05 23:46 | TRAE | 模型分配卡双 Tab：共享模型（单选择器+6角色面包屑）/按角色分配模型（7行含恢复Executor+评估开关）；新增 executor_recovery 角色端到端链路（config默认/model_router ROLES/settings白名单/orchestrator 工具连续失败与模型报错时切换恢复模型/connections标签）；新增页内 ModelPicker 双行下拉组件与 mc-tabs/mc-role-row/mc-picker 样式 |
| v1.0 | 2026-09-05 23:10 | TRAE | 首次建立 code_map.md：整合 project_memory.md 架构信息，核对全部 59 个路由端点（+health）、20 个后端核心模块 + 10 个路由文件、23 个前端组件；新增维护协议（§0）与 code_map_log.ps1 自动追加脚本 |
<!-- LOG_END -->

---

## 10. 当前运行状态与待办（易失分区，状态一变即改；2026-09-11 09:07 实测）

- 服务在跑：http://127.0.0.1:4830，监听进程 **PID 34692**（2026-09-11 09:00 由 `scripts\_dev_start_server.ps1` 启动；该脚本 `Start-Process` 回显的 37776 与实际监听 PID 不同，**一律以 `Get-NetTCPConnection -LocalPort 4830` 为准**）；日志重定向到 `data\cache\server.out.log` / `server.err.log`（uvicorn 走 stderr，中文经控制台读出是 GBK 乱码但文件本身是 UTF-8）；停止用 `scripts\_dev_stop_server.ps1`（注意它会**连 4831 mock 网关一起杀**，只需停主服务时用 `Stop-Process -Id <监听PID>`），正式使用/重启 `.\start.ps1` 或 `start.bat`
- **重启已闭合（2026-09-11 09:00:24）**：v1.0.11 的 `app/orchestrator.py` 改动（`_auto_title` 去 cfg 形参 + 两处调用点）与 `roles.memory.model` 配置均已在运行进程内生效。三重判据：① **mtime 早于进程 StartTime**——`app/orchestrator.py` 08:52:12、`data/config.json` 08:53:04 vs 进程 09:00:24；② **审计**出现 `role=planner` / `role=memory` 的真实调用（09:06:41 / 09:06:42）；③ **服务日志**零 WARNING/ERROR 且原两条告警消失。历史条目见 §9
- **v1.0.10 无需重启（已实测生效）**：本轮只改 `web/src/components/ChatArea.tsx` 与 `web/src/styles.css`，`app/` 未动；后端进程在 4830 同时 serve `web/dist`，静态文件按请求读盘，故 `npm run build` 后刷新浏览器即拿到新 bundle（实测 `index.html` 引用 `index-BNJTNSrG.js`）。**判据：只有改 `app/` 或直接改磁盘上的 `data/config.json` / `data/mcp.json` 才需要重启**
- **✅ 网关已恢复可达（2026-09-11 09:04~09:06 实测）**：`192.168.1.128:9800` 多次返回 `HTTP 200`，`gemma4-26b-a4b`（planner / evaluator / doc_compose / memory）与 `qwen3.8-27b`（executor）均真实可用，完整回合 25~37s 跑通（含工具调用、评估与自动命名）。此前 §10 记的「2026-09-10 23:32 首测 / 09-11 00:02 复测 TCP 连接超时、无任何可用 LLM 通路」**已作废**。**备用通路仍不通**：`providers.cm_8d81ae73`（deepseek，`https://api.deepseek.com/v1`，model `deepseek-v4-flash`）的 `api_key_env = CONN_CM_8D81AE73_KEY` 在 `.env` 中**未设置**，`resolve_role` 打 warning 后回退默认密钥（内网网关的 key，DeepSeek 不认）→ **主网关一旦再挂就没有可用回退**，所有依赖真实模型的功能会整批静默降级
- **网关不通时的失败形态（历史参照，09-11 00:02 实测；网关已恢复，留作下次不通时对照）**：规划阶段先烧 **48.1s** 重试才走兜底（UI 显示 `规划 · 48.1s · 兜底`、计划退化为单步 `s1`），随后执行者继续重试，整轮可拖数分钟；「停止生成」也**不即时生效**——cancel 只在流块/工具调用/角色切换的安全点检查，阻塞在网络重试里时要等到下一个安全点（既有特性，非缺陷引入）
- **网关配置（勿再按「DeepSeek 官方」假设）**：`llm.base_url = http://192.168.1.128:9800/v1`（内网 LiteLLM 代理，自带 token 表，与 DeepSeek 官方 key 不通用），`llm.model` **刻意留空**、由 roles 分角色指定：planner / evaluator / doc_compose / doc_parse / multimodal / **memory** = `gemma4-26b-a4b`（memory 于 v1.0.11 补齐，此前为空导致自动抽取长期不工作），executor = `qwen3.8-27b`，executor_recovery = `gpt-oss-120b`。8 角色 `provider` 全为 `default`（都走 base_url）。`evaluator = {enabled: true, max_rework: 3}`、`rag.enabled = true`
- **前端当前 bundle：`index-BjQa-0BM.js`（428.37 kB / gzip 122.18 kB，构建于 2026-09-13）+ `index-BT0_3sjD.css`（87.94 kB / gzip 15.22 kB）**，`web/dist/index.html` 已引用
- 用户数据现状（2026-09-11 09:07 实测）：会话 **7 个**——`ca7e144e7ad4`「废料数据看板」/ `2997591eebcf`「能力边界」/ 其余 5 个（`65502a067418`、`e749841aae32`、`eb26e7857a22`、`1a3f672bd19e`、`0023b1a30740`）标题仍为**「新会话」**；这 5 个是 v1.0.11 缺陷 A 的直接遗留，且**修复不会补命名历史会话**（`_auto_title` 只在该会话产生新回合时触发，需用户再发一轮消息才会被概括）。会话数由 8 降到 7 是**用户自己在 08:29 删掉了 `44a9dfa1493e`**（服务日志有 `DELETE /api/sessions/44a9dfa1493e 200`），旧记的 `2812fa1ee135` 也已不在列表，相关描述随本次覆盖作废。记忆库 **3 条**（`f18b634568b0` manual / `7902295862b2` tool / `b7ec9bb9bdef` auto）；本轮验证期间产生的 2 个测试会话与 3 条测试记忆（1 条执行者调工具写入 + 2 条 auto_extract 蒸馏）**已经 API 全部删净**，未触碰用户既有数据；资料库 2 个自动归档页（2026 中国经济趋势研判、在库现况分析报告）未动
- **待办 1（用户已知悉、未授权动手）**：规则层「计划声明了工具但执行者直接作答没调」仍是硬 FAIL，standard 层可能因此烧完 3 次返工落到 `paused_human`。2026-09-09 修复后已不再由命名轴误判引起，但真没调用的情况依旧触发（当日 10:17 那轮的 `workspace_list`/`workspace_read` 即属此类）。要彻底止住需把该条降级为 warning——用户当日明确选「只修两个 bug」，未选此项，**须其点头才动**
- **待办 2 已闭合（2026-09-11 00:05）**：会话 `eb26e7857a22` 的 PipelinePanel 历史渲染细节全部确认——层:standard、三角色 chip、4 条红色 fail EvalStrip（各 0 分、1~4 项未过）、`⚠ 待人工` 徽标、19 个 stage chip，且 **step-item = 0**（`step_states` 未落盘 → 条件门正确拦住误导性全 pending 时间线）。交互手段结论不变并补一条：`take_screenshot` 与 `click` 被 viewport 不可用阻断（`click` 报 `Element could not be scrolled into the viewport`），**一律用 `evaluate_script` 直接操作 DOM**（React 受控 textarea 用原生 value setter + `dispatchEvent(new Event('input',{bubbles:true}))`；文件上传用 `DataTransfer` 塞 `input.files` 再派 `change`；图标按钮按 `title` 属性找，`textContent` 为空）；**单次脚本必须 ~12s 内返回，超 15s 会被 MCP 掐断**（`Browser operation timed out after 15000ms`），长等待要拆成多次短轮询
- **待办 3（既有缺陷、未授权动手）**：SSE `error` 事件写入的 `chatError` 会被 `handleSend` finally 里 `openSession()` → `leaveView()` 的 `setChatError(null)` 立刻抹掉，**错误横幅实际永不显示**（v1.0.9 之前即如此）。网关不可达时用户看不到任何失败提示，只会见回合静默结束。**本轮 00:05 再次实证**：取消一轮网关失败的任务后 `.chat-error` 始终为 null。修法待定（`leaveView` 拆分为「导航清错误」与「重载不清错误」两种语义，或 finally 里保留错误），**须用户点头再动**
- **待办 4（阻塞已解除，仅剩过渡观察）**：v1.0.10「同一轮从展开态原地折叠成历史态」的过渡**仍未在浏览器里观察到**。原阻塞（网关不通使回合必然以 error/cancelled 收尾、`orchestrator.py` 这两条路径直接 return 不写带 meta 的 assistant 消息，故重载后没有可折叠的历史壳）**已随网关恢复消失**：本轮 09:06 已跑通 `state=done` 的成功回合，带 `meta` 的 assistant 消息确已落盘。**下一步只需发一轮真实消息并盯着同一位置**（预期：流式壳 `▾ 思考中…` → 回合结束后原地变成 `▸ 思考过程 · 层:… · 评估通过`）。注意本轮验证走的是 HTTP API 而非浏览器，故未顺带完成该观察

---

## 11. 交付决策与回滚索引（历史叙事分区，一旦写下不改写）

> 只记 §9 版本日志承载不了的东西：**需求来源、决策原因、备份位置、回滚方案、验收结论**。改动清单本身看 §9，结构事实看 §1-§8。

### 11.1 备份与回滚索引（改坏了从这里恢复）

| 备份目录 | 内容 | 回滚方式 |
|---|---|---|
| `data/_backup_start_bat_fix_20260910/` | `start.bat.pre-fix`（2534 字节，LF-only + UTF-8 的原文件） | 拷回项目根即还原；注意还原后 `start.bat` 重新变为不可用（见 §7 红线 15），此备份仅供对比与追溯 |
| `data/_backup_doc_merge_20260910/` | `project_memory.pre-merge.md`（190 行原文）、`code_map.pre-merge.md`（479 行） | 两文档合并前的完整快照；要恢复双文档结构，把这两份拷回项目根，并按备份里 code_map §0.4 的旧分工约定改写 |
| `data/_backup_openrouter_removal_20260906/` | `openrouter_connection_info.json`（端点 `https://openrouter.ai/api/v1`、env 名 `OPENROUTER_API_KEY`）、`config.pre-removal.json`、`env.pre-removal.env` | 从备份恢复 config，并把 openrouter dict 加回 `connections.py` 的 BUILTIN_PROVIDERS + `config.py` 默认 connections |
| `data/_backup_pre_cleanup_20260906/` | `app_backup.zip`、`web_src_backup.zip`、`config_backup.json` | 全项目冗余清理前的代码快照，按需解压覆盖 |

### 11.2 决策原因（当时为什么这么选）

- **资料库上传故意不引 `python-multipart`**（2026-09-06 v1.2）：文本走 `text_content`、二进制走 `content_b64`，保持**零新依赖**。要改成标准 multipart 表单须先接受这个依赖。
- **密钥 SSOT = `data/.env`，就地改写并同步 `os.environ`**（2026-09-05）：`config.set_env_key/delete_env_key` 让录入密钥**不重启即生效**；自定义模型密钥写生成变量 `CONN_CM_<8hex>_KEY`，`providers` 条目存 `{label, kind:"custom", base_url, model, api_key_env, created_at}`，`model_router.resolve_role` 原生消费无需胶水。
- **自定义模型「先验证后落盘」**：`POST /custom/models` 验证失败返 422 且**不保存**；而 `POST /{key}/key` 录密钥后即验，失败也 422 但**密钥已存**——两者语义不同是刻意的。
- **内置提供商无删除能力**（2026-09-06）：DELETE 端点仅支持自定义模型 `/custom/models/{pid}`，所以要移除内置项（如 openrouter）只能改代码，这是产品现状不是遗漏。
- **`_dev_cleanup_restore.ps1` 会整删 pages/memories**：真实资料场景**禁用**，改按标题/内容精确删除。
- **评估返工修复范围（2026-09-09 用户决策）**：规则层命名轴误判只修两个 bug（归一化 + trace 补 `is_error`），**明确不放宽**「计划声明的工具执行者没调」这条硬 FAIL。见 §10 待办 1。
- **两文档合并为一份（2026-09-10 用户决策）**：推翻 2026-09-06「两文件长期并存」的旧决策。合并理由是原 `project_memory.md` 的结构性章节有 6 处已随代码演进失效却无人核对（清单见 §0.4）；防复发的机制是 §0.4 的三分区归属判定，而非维持两份文件。
- **`start.bat` 选 GBK 而非纯 ASCII 英文（2026-09-10 用户决策）**：三个候选（GBK 重编码 / 中文提示改英文 / 保留 UTF-8 加 `chcp 65001`）中用户选 GBK，理由是保留中文提示，且实测该组合零报错。代价：在非 936 代码页的机器上中文提示会乱码——西欧单字节代码页下脚本仍能跑（无 lead byte 概念，不会吞字符），但在其他 DBCS 代码页（如 932）下仍可能错位。日后若要跨语言环境分发，改纯 ASCII 英文提示即可，对照实验数据见 §9 v1.0.8。
- **会话标题复用 planner 角色 + 以「标题仍是占位值」为唯一触发条件（2026-09-10 用户决策，三项）**：① *标题模型*——候选「新增专用 titler 角色 / 复用 planner / 复用 executor」，选复用 planner：不必往 `model_router.ROLES` 与设置页角色分配卡再加一行，且概括与规划同属「读用户意图、产出短结构化文本」，档位一致。代价是标题质量受 planner 档位牵制，无法单独降档省钱。② *概括失败兜底*——候选「回退为首条用户消息前 20 字 / 保持「新会话」下轮重试」，选后者：一个错标题比没标题更烦人（会被当成已命名而永不重试）。实现上把触发条件定为「标题仍等于 `DEFAULT_TITLE`」，失败自然留到下一轮，**无需新增 `title_auto` 之类状态字段**——这是本轮最省事的一处设计。③ *草稿态附件*——候选「草稿态禁用附件按钮 / 选文件时就建会话」，选后者：不削弱能力。代价是选了文件却不发送会在后端留下 0 消息会话，下次刷新页面时以「新会话（空任务）」出现在履历里（已实测确认，见 §4.1）。
- **思考履历折叠时机用 `useState(!!live)` 的挂载初值，而非显式状态（2026-09-11）**：候选「① 给 streaming/meta 加 `collapsed` 字段、靠 SSE 事件切换 / ② `useEffect` 监听 `live` 由 true→false 再折叠 / ③ 靠挂载时机的 `useState(!!live)` 初值」，选 ③。理由：回合结束时 `App.tsx` 的 finally 会 `openSession(sid)` 重载消息，流式块卸载、历史行以新 key 挂载，**折叠是「重新挂载」的自然结果，不需要任何状态迁移逻辑**，也不必动 SSE 协议或 meta 结构。② 行不通的原因是 `live` 由 true 变 false 时那个组件实例其实已被卸载，effect 根本不会触发。代价：用户手动展开的历史壳在下次重载会话后回到折叠态（可接受，与 ToolCard 既有行为一致）。同一轮里还**刻意不合并**流式与历史两处 ToolCard 渲染：`ToolTrace` 与 `InFlightTool` 的 content / isError / elapsedMs 推导方式不同（前者 `is_error ?? content.startsWith("Error:")`、后者靠 `endedAt === undefined` 判 running 并现算耗时），合并需要一层归一化适配，比留两处相似 JSX 更难维护。

### 11.3 验收结论

- **离线验收**：`scripts/verify.py` + `scripts/mock_llm.py`（4831）。2026-09-05 首次全绿 11/11；v1.0.5 扩至 14 项（S0-S13）全 PASS。跑前须先起 mock，S0 会自动 PUT mock 角色模型。
- **在线验收**：2026-09-05 2/2 PASS（当时真实网关为 DeepSeek 官方 `api.deepseek.com` + `deepseek-v4-flash`；**网关现已改为内网代理，见 §10**）。脚本 `scripts/_dev_online_verify.py`（fast 直答 + standard 工具调用，测完删会话）。
- **2026-09-09 规则层修复**：用真实落盘数据（会话 `eb26e7857a22` 的 msg 8 计划 + msg 10 痕迹）做修复前后对照回放 **8/8 通过**，含 3 个负向场景确认判定未被放宽。
- **2026-09-10 rag 门控修复**：内存态切换 `rag.enabled` 两态 + `rebuild()` **5/5 通过**，并校验 `data/config.json` 的 sha256 前后一致（确认验证过程未写盘）。
- **2026-09-10 `start.bat` 修复**：两条路径零副作用干跑通过（正常路径 `NEED_INSTALL=0`、中文正常、零语法报错；首次使用路径 `for` 循环正常解析并找到 Python），三组编码对照实验（纯 ASCII / UTF-8+CRLF / GBK+CRLF）确证根因。**验证缺口：未做真实启动的端到端验证**——端口 4830 被 PID 29636 占用且服务由用户自行启停，故只验证到「启动前一步」；用户下次用 `start.bat` 重启即为端到端确认。
- **2026-09-10 草稿态 + 标题自动概括**：后端 `compileall` OK；`_auto_title` 桩件 **8/8**——其中「带引号换行」用例**测出并修掉一个真 bug**（清洗顺序原为先剥引号后裁首行，模型输出「引号标题 + 换行 + 解释」时行尾引号夹在串中间剥不掉，会残留进侧边栏标题）。前端 `tsc --noEmit` 零报错、`vite build` OK；服务重启至 PID 21492 后用 `evaluate_script` 实测浏览器行为：点「新任务」→ 卡片 8 不变 / active=0 / **后端会话数仍 8（零创建）**；草稿态发送 → **700ms 内卡片 8→9 且新条目高亮**；草稿态选附件 → chip 立即显示、卡片仍 9（条目未提前出现）、附件未被 `null→id` 清掉；重载页面 → 8 卡片并打开 list[0]，点开「能力边界」渲染 14 个消息元素（`openSession` 经 `leaveView` 重构后无回归）。测试产生的 2 个会话已删净（回到 8），临时脚本零残留。**验证缺口：真模型标题文案未验证**——内网网关 TCP 超时、deepseek provider 密钥未设，当前无任何可用 LLM 通路（见 §10）；不过这次真实故障**反向实证了 fail-open**：鉴权失败下 `_auto_title` 不抛异常、标题安全留在占位值、回合结果不受影响。
- **2026-09-11 思考履历折叠（v1.0.10）**：`tsc --noEmit` 零报错、`vite build` OK；纯前端改动，后端在 4830 同时 serve `web/dist`，故构建即生效（实测 `index.html` 引用 `index-BNJTNSrG.js`）、无需重启。浏览器 `evaluate_script` 实测两条 UI 规则：**规则②（任务结束后自动折叠）**在真实落盘数据上通过——会话 `eb26e7857a22` 的 10 个思考壳全部折叠（chevron 全 `▸`、openCount=0），摘要正确（含 `⚠ 待人工`），3 条答案 `.md-body` 仍在壳外可见；手动点开可完整回看 4 条 fail 评估 + 19 个 stage chip + 计划链，再点折回摘要重现。**规则①（执行中实时展开）**在真实流式回合上通过——发送后 200ms 内壳即以 `live=true / open=true / ▾` 出现并持续展开 11s+，壳内实时刷新层、角色高亮迁移（规划者→执行者）、`规划 · 48.1s · 兜底`、步骤时间线；点「停止生成」后壳随流式块卸载，界面不残留展开态。**缺口**：两端形态分别实证，但「同一轮从展开原地折叠成历史态」的过渡因网关不可达（回合只能以 error/cancelled 收尾，而这两条路径不落 meta）未能观察，见 §10 待办 4。测试会话已删净（回到 8 个，未触碰用户两个既有空会话）。

### 11.4 「任务无限重复运行」诊断（2026-09-09 报障，09-10 收尾）

- **用户报障**：任务疑似无限重复运行，人工侧核实已重复执行 3 次（同一句话连发三次催办）。
- **结论：不是无限循环**。返工预算由 `orchestrator` 的 `if attempt > max_rework: paused = True; break` 兜住，`max_rework=3` → 上限 = 1 初跑 + 3 返工 = **4 次执行**。审计 `audit-20260909.jsonl` 精确记录 4 次 planner 调用（10:46:44 / 10:47:18 / 10:47:31 / 10:47:43），与「重复 3 次」= 3 次返工完全吻合。`automations.json`（唯一 automation 已 paused、7 条 runs 全 manual）与 `jobs.json`（8 个 job 全 done、run_count=1）均已排除嫌疑。
- **10:46 那轮其实是用户手动取消的**：msg 12 只有 `{role, content}`（取消路径的落盘形状，无 meta 无 tool_trace），且 10:47:47 之后缺失 executor 的 llm_call 审计行。
- **真问题不是次数，是 3 次返工 100% 无效**：三次 eval rule FAIL 的 detail 逐字相同——「计划步骤声明的工具 skill_load 未被成功调用；…sequential-thinking__sequentialthinking 未被成功调用」，而审计同时记录这两个工具**调用成功**。根因是命名轴错位（结构说明见 §3.3 归一化条目与 §3.4 hidden 别名），每次返工都在追一个不存在的问题，白烧 3 轮 token 后落到 `paused_human`。
- **证据链全部取自磁盘原文而非推断**：msg 8 的 `meta.plan.steps`（声明全名）↔ 审计 10:47:02 该工具成功 ↔ msg 10 落盘 trace `tool='sequentialthinking'`（已被剥前缀）↔ 规则层判 `'sequential-thinking__sequentialthinking' in {'sequentialthinking'}` = False。
- **附带查出反向缺陷**：`is_error` 当时只进 `tool_result` 事件、没进 trace，使同一个规则层一边过严（假 FAIL 烧预算）一边过松（「本轮全部工具调用均失败」检查永不触发、报错工具反被计入成功集）。
- **验证脚本踩坑**：裸导入时 `tool_registry._defs` 为空（工具在应用启动时经 `await rebuild()` 装载）；且脚本环境不连 MCP 导致 `has()` 返 False、规则层提前 `continue`，须按 `rebuild()` 的同形结构注入 MCP 定义桩，否则「修复前确实误判」这一对照组会假性 FAIL。
