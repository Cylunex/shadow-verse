# TauriTavern — ST 套进 Tauri，Rust 重写服务端

> 存档 2026-06-18 · 对照 shadow-verse 零依赖 Python 暗宇宙引擎

## 定位
把 SillyTavern 前端原封套进 Tauri v2 桌面壳，用 Rust 按 Clean Architecture 完整重写服务端，并把酒馆「工具调用递归回 Generate()」旧结构升级为一条全新 Agent 生成路径(Agent 把回复建模为「对受策略约束的 Workspace 的一组可审计/可回滚编辑」)。

## 技术栈 / 规模
后端 **Rust**(Tauri v2,Clean Architecture 四层 presentation/application/domain/infrastructure);前端沿用 ST 1.16 原生 JS,通过 patch `window.fetch` 路由到 Tauri command。约 **515 个 .rs / ~137k 行 Rust**(大头 agent_runtime_service + agent_model_gateway)+ 前端注入层 ~137 JS。跨平台 Win/mac/Linux/Android/iOS。AGPL-3.0。**极重依赖,纯架构参考**。

## 核心机制剖析

**1. 前端注入/拦截层**(`src/tauri/main/interceptors.js`/`router.js`)
不改 ST 源码,patch `window.fetch`(WeakMap 记 patch 态防重复、处理 AbortSignal race、解析相对 URL base),命中本地路由的请求路由到 Tauri command,不命中走原始 fetch。路由按域拆(system/settings/character/chat/ai)。host kernel 分层 context/kernel/services/adapters/routes;routes 层不得引用 window(类型守护)。

**2. Rust Clean Architecture**(`docs/BackendStructure.md`)
domain(纯结构 models + `#[async_trait]` repository trait + DomainError) → application/services(50+ 服务) → infrastructure(repo 实现 + `LoggingChatCompletionRepository` wrapper 强制日志/secret/policy 不被绕过 + HttpClientPool) → presentation/commands(40+ + registry.rs)。依赖严格内向。

**3. Agent = Workspace 编辑模型**(`docs/AgentArchitecture.md`/`Agent/Workspace.md`/`RunEventJournal.md`)— ★全档最有料
核心定义:「一次生成不是 LLM 返回字符串,而是 Agent 对受策略约束的 Workspace 做一组**可审计、可回滚**的编辑,最后 runtime 把 Artifact 组装提交为聊天消息。」三路径互不污染:Legacy Generate / Agent Generate / MCP·Tool Direct。
- **两级 Workspace**:chat workspace(对话级,按稳定聊天身份派生 `chat_<sha256(stableChatId)[0..16]>`,重命名/显示名变化不分裂)+ run workspace(每次 run 独立,含 input/output/plan/scratch/summaries/persist/checkpoints/patches/events.jsonl)。物理根 `_tauritavern/agent-workspaces`。
- **万物皆文件**:world/character/preset/user/skills/memory 都抽象为 workspace 资源;`persist/` 在 finish 成功后 promote 回稳定 chat workspace。
- **Run Event Journal**:append-only JSONL,`seq` 单调递增由 repository 分配,关键副作用前后必落 journal,可重放重建 UI timeline/resume/cancel;大文本/二进制不进 event 用 resource ref。
- **14 内建工具**:chat.search/read_messages(只读绑定聊天,index 从 0)/worldinfo.read_activated(只读本次 run snapshot)/dice.roll/skill.*/workspace.list/search/read/write_file/apply_patch/commit/finish。write_file/apply_patch 成功只回摘要+元数据+resource refs(要全文须显式 read_file,省 context)。
- **工具循环 ≤80 轮,必须 workspace.finish 收尾**;前台 run finish 前至少成功 commit 一次。模型直接输出文本 → 捕获到 `direct_output.md` + **soft drift recovery**(合成 user 提醒纠偏)。模型可修正错误以 `is_error=true` tool result 回填;宿主级 IO/journal 错误 fail-fast。
- provider 保真:canonical model IR(`AgentModelRequest/Response/ContentPart`),Claude/Gemini native metadata 以 opaque `Native` part 保存回放,tool id 缺失 fail-fast。

## 借鉴清单

| # | 借鉴点 | 对应能力 | 状态 | 移植 | 优先级 |
|---|---|---|---|---|---|
| 1 | Agent=Workspace 编辑模型(多轮编辑文件最后组装 artifact) | narrate 产线(已是多步产物思路,无 workspace 抽象) | 🔵仍可借 | 仅思路(narrate 升级为「workspace 多文件多轮编辑草稿/状态/小剧场」) | 高 |
| 2 | **Run Event Journal**(append-only JSONL+seq 单调+副作用前后落账+resource ref 外置+可重放) | narrate 钩子台账(雏形) | 🔵仍可借 | **直接移植**(JSONL+seq,纯 Python 零依赖) | 高 |
| 3 | Agent 工具循环护栏(80轮+必须finish+soft drift recovery+可修正错误 vs fail-fast 分级) | validate 护栏+内联宏 | 🔵仍可借 | 仅思路(「直接输出文本→捕获→合成提醒纠偏」很实用) | 高 |
| 4 | Checkpoint+回滚语义(回到某 checkpoint 而非只能重生成) | swipe | 🔵仍可借 | 直接移植(JSONL) | 中 |
| 5 | 稳定聊天身份派生 workspace id(sha256,重命名不分裂) | 扮演页 chat 标识 | ⚪以后可能用 | 直接移植(hashlib) | 中 |
| 6 | 工具结果只回摘要+resource ref,要全文须显式 read | narrate/记忆检索 | 🔵仍可借 | 直接移植(省 token 关键) | 中 |
| 7 | canonical model IR + native metadata opaque 保真 | 可插拔 LLM | 🔵仍可借 | 仅思路 | 中 |
| 8 | Clean Architecture 四层 trait 注入 | 五层 | ✅理念已吸收 | — | 低 |

## 不值得碰
整个 Rust/Tauri/cargo/pnpm 工具链、Tauri command/invoke ABI、跨平台 WebView、HttpClientPool 持久 WS、tsc host-kernel 类型守护。桌面原生壳+Rust 重写专属,与零依赖 Python 异构。Agent 系统价值全在文档定义的语义模型,Rust 实现不可移植。

## 存档备忘(以后可能用)
- **完整 Agent 文档体系**(`docs/Agent/` Workspace/RunEventJournal/ToolSystem/LlmGateway/Skill/McpSkill + AgentContract「不可破坏不变量与 fail-fast 约束」+ AgentImplementPlan「验收命令」)是一套**生产级 Agent runtime 完整设计规格**。shadow-verse 若把 narrate/nexus 升级成真正 Agent runtime,这是最完整蓝图(尤其 AgentContract 不变量清单+journal 状态机+resume/cancel 语义)。
- MCP 与 Skill 边界文档(`Agent/McpSkill.md`):将来区分「MCP 工具 vs Skill 知识包」职责时参考。
