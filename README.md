# Arche Agent 工作台

本机运行的 AI Agent 工作台，支持 Windows / Linux / macOS 跨平台部署。

- 本地 Web UI：左侧会话列表 / 中央对话区（Markdown 渲染 + 工具调用卡片 + 编排过程时间线）/ 右侧工具面板 / 顶栏全局状态
- **四层编排管道**：Workflow Router 自动路由 fixed（零模型调用）/ fast（直答）/ standard（规划+执行+评估）/ deep（深度返工闭环）
- Planner→Executor→Evaluator 三角色 + Memory 回合后自动记忆抽取
- 统一工具：技能 / 工作区文件 / 定时任务 / 页面 / 长期记忆 / 元信息 / RAG 知识库 七类内建 + MCP 服务器动态注入
- LLM：OpenAI 兼容网关，SSE 流式；按角色经 model_router 分离模型（LiteLLM 式 provider 抽象）

## 环境要求

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ | 推荐 3.12 或 3.14 |
| Node.js | 20+ | 仅前端构建时需要（已预构建 dist/） |
| 操作系统 | Windows / Linux / macOS | 跨平台支持 |

## 一、快速启动

### Windows

```powershell
# PowerShell（推荐）
.\start.ps1

# 或 CMD
start.bat
```

### Linux / macOS

```bash
chmod +x start.sh
./start.sh
```

首次运行自动完成：创建 `.venv` → 安装依赖 → 初始化 `data/` 配置文件 → 启动服务。

浏览器打开 **http://127.0.0.1:4830**（仅监听本机回环地址）。停止：`Ctrl+C`。

## 二、配置（首次必读）

### 2.1 配置 API Key

编辑 `data/.env` 文件，设置你的 LLM 网关 API Key：

```bash
# 必填：API Key
API_KEY=sk-your-api-key-here

# 可选：覆盖网关地址和模型
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

**支持的网关**（任何 OpenAI 兼容接口）：

| 提供商 | base_url | 示例模型 |
|--------|----------|----------|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini`, `gpt-4o` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Moonshot (Kimi) | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| 本地 Ollama | `http://localhost:11434/v1` | `llama3.1` |
| 本地 LM Studio | `http://localhost:1234/v1` | 你加载的模型 |

> **本地 Ollama/LM Studio 注意**：无需真实 API Key，填任意占位值（如 `ollama`）即可。

### 2.2 配置文件说明

所有配置在 `data/` 目录（首次启动自动生成）：

| 文件 | 用途 |
|------|------|
| `data/.env` | **API Key 唯一存放处**：密钥只存这里，不进入 config.json |
| `data/config.json` | 网关 / 模型 / 角色模型映射 / 工作流模式 / 各功能开关 |
| `data/mcp.json` | MCP 服务器声明（默认内置 sequential-thinking） |
| `data/skills/*.md` | Agent Skills 技能卡（frontmatter：`name` / `description` / `triggers` 触发词 / `enabled` 开关；默认生成 translate/summarize/code_review 示例） |
| `data/sessions.json` + `data/sessions/` | 会话元数据与消息记录 |

### 2.3 config.json 主要字段

```jsonc
{
  "llm": {
    "base_url": "https://api.openai.com/v1",  // 网关地址
    "model": "",                               // 留空 = 未配置，可在 UI 设置中选择
    "temperature": 0.7,
    "max_tokens": 8192,
    "max_tool_rounds": 25
  },
  "providers": {                               // 命名 provider（多网关支持）
    "my_provider": {
      "base_url": "https://...",
      "api_key_env": "MY_KEY"                  // 引用环境变量名，不落明文
    }
  },
  "roles": {                                   // 按角色分离模型
    "planner":   { "provider": "default", "model": "" },
    "executor":  { "provider": "default", "model": "" },
    "evaluator": { "provider": "default", "model": "" },
    "memory":    { "provider": "default", "model": "" }
  },
  "workflow": { "mode": "auto" },              // auto | fast | standard | deep
  "evaluator": { "enabled": true, "max_rework": 3 },
  "memory": { "enabled": true, "auto_extract": true, "inject_top_k": 5 }
}
```

**配置要点**：
- `llm.model` 留空 = 未配置模型，可在顶栏 ⚙ 设置里「探测网关」选择后保存
- 角色模型解析：`roles.<role>.model` 为空 → 继承 `llm.model`；`provider` 为空/`default` → 使用 `llm` 节配置
- 密钥 SSOT：只存 `.env`；命名 provider 用 `api_key_env` 引用环境变量名
- 功能开关：`planner / evaluator / memory / skills / workspace / doc / jobs / pages / rag` 各节 `enabled`

## 三、编排管道与工具

### 3.1 四层工作流路由

| 层级 | 触发条件 | 行为 |
|------|----------|------|
| **fixed** | 命中规则（`data/workflow_rules.json`） | 零模型调用，确定性结果 |
| **fast** | 短消息 + 无工具/深度意图 + 未命中技能触发词 | 直答，不规划、不挂工具、不评估 |
| **standard** | 默认；或短请求命中技能触发词 | Planner 规划 + Executor 工具循环 + Evaluator 验收 |
| **deep** | 命中深度关键词或长文本 | 同 standard，但规划更细、评估更严 |

`workflow.mode=auto` 时按消息长度 + 关键词自动路由；也可手动指定 `fast/standard/deep`（手动优先于技能升级）。
fast 层不挂工具，因此命中技能触发词的短请求（如「翻译成英文：你好」）会自动升级到 standard，否则 `skill_load` 无从调用。

### 3.2 统一工具（OpenAI function 格式注入）

| 类别 | 工具 | 说明 |
|------|------|------|
| workspace | `workspace_read/write/list` | 读写 `data/workspace`（路径遍历防护） |
| doc | `doc_parse` | 解析 workspace 内 PDF/Word/Excel/PPT/图片/扫描件：文本、表格、布局结构（mode=auto/text/tables/structure） |
| skill | `skill_list/skill_load` | 技能目录与全文加载；请求命中技能卡 `triggers` 时 Planner 自动把 `skill_load` 写成计划首步，再由 Evaluator 规则层强制其真正被调用 |
| job | `job_create/list/cancel` | 一次性/周期定时任务 |
| page | `page_create/list/get` | 页面/笔记（REST 面 `/api/pages`） |
| memory | `memory_save/search` | 长期记忆（回合后自动抽取） |
| rag | `kb_search/kb_answer` | 知识库混合检索（BM25+向量） |
| meta | `meta_tools_list/meta_status` | 系统元信息 |
| MCP | `服务器名__工具名` | MCP 服务器动态注入 |

对话中触发工具调用：中栏出现工具卡片（参数/结果可展开），右栏时间线同步；每轮工具痕迹随消息持久化。

### 3.3 文档解析与附件（PDF/Word/图片/扫描件）

解析层 `app/doc_parser.py` 为单一来源，聊天附件、资料库（RAG）导入、`doc_parse` 工具共用：

| 输入 | 文本 | 表格 | 布局/结构 | 引擎 |
|------|------|------|-----------|------|
| PDF（文字版） | ✅ | ✅ | ✅ 块级 bbox | PyMuPDF |
| PDF（扫描件） | ✅ OCR | — | ✅ OCR 行级 bbox | PyMuPDF 渲染 + RapidOCR |
| Word .docx | ✅ | ✅ | ✅ 标题层级 → Markdown | python-docx |
| Excel .xlsx / PPT .pptx | ✅ | ✅ | 按 sheet/页分块 | openpyxl / python-pptx |
| 图片 .png/.jpg/… | ✅ OCR | — | ✅ OCR 行级 bbox | RapidOCR（中文 PP-OCR） |
| 文本/代码类 | ✅ | — | — | utf-8 → GBK 回退 |

- **双份输出**：`content.txt`（人/模型读的 Markdown 化全文）+ `structured.json`
  （程序可读取数据：页 → 块[heading/paragraph/table/ocr，带 bbox 与置信度] → 表格单元格矩阵）。
- **聊天附件**：一次性上下文——解析文本只注入发送它的那一轮，不落消息历史；
  图片/扫描件上传即 OCR，识别到文字按普通文本注入，识别不到才占位说明。
- **资料库（RAG）**：上传/导入的 PDF、Word、图片也会解析出文本进知识库索引，`kb_search` 可检索。
- **依赖与模型**：PyMuPDF / rapidocr / onnxruntime / Pillow 均纯 pip（无外部二进制）；
  OCR 模型首次运行联网下载并缓存于 `.venv/Lib/site-packages/rapidocr/models/`，之后离线可用。
- 解析失败一律 fail-open：附件标记 `parse_failed`、资料库仅托管文件，不阻断对话。

## 四、目录结构

```
ai_agent/
├── start.ps1              # Windows PowerShell 启动脚本
├── start.bat              # Windows CMD 启动脚本
├── start.sh               # Linux/macOS 启动脚本
├── server.py              # 服务入口（uvicorn，127.0.0.1:4830）
├── requirements.txt       # Python 依赖
├── .env.example           # 环境变量配置示例
├── app/                   # FastAPI 后端
│   ├── main.py            # 装配：lifespan + 路由 + 静态托管(SPA fallback)
│   ├── config.py          # data/ 目录与配置读写（密钥 SSOT 在 .env）
│   ├── llm.py             # OpenAI 兼容流式/非流式客户端
│   ├── workflow_router.py # 四层路由 fixed/fast/standard/deep
│   ├── orchestrator.py    # Planner→Executor→Evaluator 管道
│   ├── planner.py         # 结构化计划生成
│   ├── evaluator.py       # 两层质量评估（规则+语义）
│   ├── prompt_assembler.py # P0-P5 优先级 System Prompt 装配
│   ├── model_router.py    # 角色→模型映射
│   ├── tool_registry.py   # 统一工具注册表
│   ├── unified_tools.py   # 内建工具实现
│   ├── memory_manager.py  # 长期记忆管理
│   ├── skill_manager.py   # Agent Skills 管理
│   ├── job_scheduler.py   # 定时任务调度
│   ├── page_manager.py    # 资料库页面管理
│   ├── doc_parser.py      # 文档解析层（PDF/Word/Office/图片/扫描件，三方共用）
│   ├── attachments.py     # 聊天附件：会话级一次性上下文
│   ├── rag.py             # RAG 知识库引擎
│   ├── automation_manager.py # 自动化任务管理
│   ├── task_runner.py     # 无人值守任务执行
│   ├── mcp_manager.py     # MCP 服务器连接
│   ├── audit.py           # 审计日志
│   ├── tls.py             # OS 信任链注入
│   ├── workspace_manager.py # 工作区注册表
│   └── routes/            # REST API 路由
│       ├── sessions.py    # 会话 CRUD
│       ├── chat.py        # SSE 流式对话
│       ├── mcp.py         # MCP 服务器管理
│       ├── settings.py    # 配置读写
│       ├── connections.py # 模型连接管理
│       ├── automations.py # 自动化任务
│       ├── rag.py         # RAG 知识库
│       ├── workspaces.py  # 工作区管理
│       ├── storage.py     # 存储统计与清理
│       ├── retrieval.py   # 检索策略
│       ├── auth.py        # 访问认证
│       └── extras.py      # memories/skills/pages/jobs/pipeline
├── web/                   # 前端源码（Vite + React + TS）
│   ├── src/               # TypeScript 源码
│   └── dist/              # 预构建产物（可直接使用）
├── scripts/
│   ├── mock_llm.py        # 离线验收 mock 网关
│   ├── verify.py          # 端到端验证脚本
│   └── _dev_*.ps1         # 开发辅助脚本
└── data/                  # 运行时数据（首次启动自动生成）
    ├── .env               # API Key 配置
    ├── config.json        # 主配置
    ├── mcp.json           # MCP 服务器配置
    ├── sessions.json      # 会话元数据
    ├── sessions/          # 会话消息记录
    ├── skills/            # 技能卡
    ├── workspace/         # 工作区文件
    ├── library/           # 资料库文件
    └── audit/             # 审计日志
```

## 五、API 一览

所有 API 均在本机 `127.0.0.1:4830`：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET/POST | `/api/sessions` | 会话列表 / 创建 |
| GET/PATCH/DELETE | `/api/sessions/{id}` | 会话详情 / 改名 / 删除 |
| POST | `/api/chat/stream` | SSE 流式对话（编排管道驱动） |
| POST | `/api/chat/cancel` | 取消进行中的生成 |
| POST | `/api/chat/confirm` | danger 工具确认门 |
| GET | `/api/pipeline` | 编排管道配置 + 角色→模型映射 |
| GET/POST | `/api/memories` | 长期记忆列表 / 添加 |
| DELETE | `/api/memories/{id}` | 删除记忆 |
| GET/POST | `/api/skills` | 技能列表 / 创建 |
| GET | `/api/skills/{name}` | 技能详情 |
| GET/POST | `/api/pages` | 页面列表 / 创建 |
| GET/DELETE | `/api/pages/{id}` | 页面详情 / 删除 |
| GET | `/api/jobs` | 定时任务列表 |
| POST | `/api/jobs/{id}/cancel` | 取消定时任务 |
| GET | `/api/mcp/servers` | MCP 服务器状态 |
| POST | `/api/mcp/reload` | MCP 热重载 |
| GET/PUT | `/api/settings` | 配置读写 |
| POST | `/api/settings/probe` | 网关探测 |
| GET | `/api/connections` | 模型连接状态 |
| POST | `/api/connections/refresh` | 刷新连接验证 |
| GET/POST | `/api/automations` | 自动化任务 |
| GET | `/api/rag/status` | RAG 索引状态 |
| POST | `/api/rag/reindex` | 重建 RAG 索引 |
| GET | `/api/workspaces` | 工作区列表 |
| GET | `/api/storage` | 存储统计 |

**SSE 事件类型**：`start / workflow / role_active / plan / step_update / delta / tool_call / tool_result / confirm_request / eval / done / error / cancelled`

每 5s 发 SSE 注释行心跳保活。

## 六、高级配置

### 6.1 多模型支持（按角色分离）

在 `config.json` 中配置 `providers` 和 `roles`：

```jsonc
{
  "providers": {
    "deepseek": {
      "base_url": "https://api.deepseek.com/v1",
      "api_key_env": "DEEPSEEK_KEY"  // 在 .env 中设置 DEEPSEEK_KEY=sk-xxx
    }
  },
  "roles": {
    "planner": { "provider": "deepseek", "model": "deepseek-chat" },
    "executor": { "provider": "default", "model": "gpt-4o-mini" },
    "evaluator": { "provider": "deepseek", "model": "deepseek-chat" }
  }
}
```

### 6.2 MCP 服务器扩展

编辑 `data/mcp.json` 添加 MCP 服务器：

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking@2026.7.4"],
      "enabled": true
    },
    "brave-search": {
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": { "BRAVE_API_KEY": "your-key" },
      "enabled": true
    }
  }
}
```

保存后在 UI 右栏 MCP 面板点击「热重载」，或重启服务。

### 6.3 访问认证（团队共享前必须开启）

```bash
# 在 UI 设置中开启，或调用 API：
curl -X POST http://127.0.0.1:4830/api/auth/enable
# 返回 {"enabled": true, "token": "xxx"}  ← 唯一一次完整展示
```

开启后所有 `/api/*` 请求需携带 `Authorization: Bearer <token>`。

### 6.4 离线验收（配合 mock 网关）

无需真实网关即可端到端验证编排管道：

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File scripts\_dev_launch_mock.ps1
powershell -ExecutionPolicy Bypass -File scripts\_dev_start_server.ps1
.\.venv\Scripts\python.exe scripts\verify.py

# Linux/macOS
python3 scripts/mock_llm.py &
python3 server.py &
python3 scripts/verify.py
```

## 七、常见问题

### 启动问题

| 问题 | 解决方案 |
|------|----------|
| 提示未找到 Python | 安装 Python 3.10+ 并确保在 PATH 中 |
| 提示未配置 API Key | 编辑 `data/.env` 设置 `API_KEY=sk-xxx` 后重启 |
| 提示未配置模型名 | 在 UI 设置中「探测网关」选择模型，或编辑 `config.json` 设置 `llm.model` |
| 端口 4830 被占用 | 编辑 `server.py` 修改 `port` 值 |

### 运行问题

| 问题 | 解决方案 |
|------|----------|
| MCP 服务器 error | 右栏卡片展开可见原因；常见：PATH 无 npx / 首次下载超时 / 代理拦截 npm |
| 前端改动后不生效 | `web/` 下执行 `npm install && npm run build` 后重启服务 |
| 编排过程 UI 不显示 plan/eval | 确认前端已构建（`web/dist` 存在）且为新事件版本 |
| 工具调用超时 | 检查 `config.json` 中 `llm.max_tool_rounds` 和各工具 timeout 设置 |

### 性能优化

- **降低延迟**：设置 `workflow.mode=fast` 跳过规划和评估
- **减少 token 消耗**：关闭 `evaluator.enabled` 或降低 `max_rework`
- **加速 RAG**：设置 `rag.embed_model` 为空使用纯 BM25（无需向量化）

## 八、技术架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web UI (React + TS)                       │
│  ┌──────────┐  ┌──────────────────────────┐  ┌───────────────┐  │
│  │ 会话列表  │  │      对话区 (SSE)         │  │   工具面板     │  │
│  └──────────┘  └──────────────────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (Python)                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Orchestrator (编排管道)                      │    │
│  │  ┌─────────┐    ┌──────────┐    ┌───────────┐           │    │
│  │  │ Planner │───▶│ Executor │───▶│ Evaluator │           │    │
│  │  └─────────┘    └──────────┘    └───────────┘           │    │
│  │        │              │               │                  │    │
│  │        ▼              ▼               ▼                  │    │
│  │   结构化计划      工具循环执行      质量验收              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌───────────────────────────┼───────────────────────────────┐  │
│  │              Tool Registry (统一工具注册表)                 │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │  │
│  │  │Workspace│ │  Skills │ │  Memory │ │   RAG   │         │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘         │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │  │
│  │  │  Jobs   │ │  Pages  │ │  Meta   │ │   MCP   │         │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────┼───────────────────────────────┐  │
│  │              Model Router (角色模型映射)                    │  │
│  │  planner / executor / evaluator / memory / doc_*          │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              OpenAI Compatible LLM Gateway                       │
│  (OpenAI / DeepSeek / Moonshot / Ollama / LM Studio / Custom)   │
└─────────────────────────────────────────────────────────────────┘
```

## 九、许可证

本项目仅供学习和研究使用。
