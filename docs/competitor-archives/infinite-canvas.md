# infinite-canvas — 无限画布工作台 + 本地 Agent 桥

> 存档 2026-06-18 · 对照 shadow-verse · canvas-agent 的 MCP↔SSE 桥 = 把 MCP 与网页控制台打通的现成蓝本

## 定位
把无限画布编排 + AI 生图 + 对话助手放一处的图片创作工作台,并通过本机 **canvas-agent** 让 Codex/Claude Code 经 MCP 反向操作线上网页画布。

## 技术栈 / 规模
网页:Next.js 16.2/React/TS/Tailwind/Ant Design/Zustand/TanStack Query;浏览器前台直连用户配置的 OpenAI 兼容接口。**canvas-agent(本档重点)**:独立 npm 包 `@basketikun/canvas-agent`,TS+Express+官方 `@modelcontextprotocol/sdk`+zod,Bun 构建,`src/` 9 文件约 700 行核心。AGPL-3.0。

## 核心机制剖析

**1. MCP↔SSE 桥(双进程三跳)**— ★
本地 Agent 同时是 MCP server 和 HTTP/SSE server,把「终端里的 Codex/Claude」与「浏览器画布」接起来:
- **MCP 端**(`mcp-server.ts`)极薄:官方 SDK 起 stdio server,把 toolNames 全注册(`:12`),每个 handler 只是 zod 校验后 `POST http://127.0.0.1:port/api/tools`(`:24`,带 token header)。MCP 不直接碰画布,只转发本地 HTTP。
- **HTTP/SSE 端**(`http-server.ts`):Express 起 127.0.0.1(`:98`)。`/events` 开 SSE 长连(浏览器订阅);`/api/tools` 收工具调用。
- **会话桥**(`canvas-session.ts` 核心):callTool 归一后 `requestCanvasTool`(`:152`)生成 requestId,经 SSE `tool_call` 事件**推浏览器执行**,挂 30s 超时 pending Promise;浏览器执行完 `POST /canvas/result` 回填,resolveResult(`:36`)按 requestId resolve/reject。浏览器周期 `POST /canvas/state` 同步快照(`:32`),读类工具(canvas_get_state/selection)直接读缓存快照零往返。
- 三跳:**Codex(stdio MCP)→本地 HTTP /api/tools→SSE tool_call→浏览器执行→/canvas/result 回填**。这是「用 MCP 驱动网页 UI」的完整范式。

**2. Origin 锁定安全**(`http-server.ts:118`、`config.ts`):默认只监听 127.0.0.1。**首连 Origin 记忆**:网页带正确 token 首次连接时把 Origin 记进 config.origins(`:126`);之后其他 Origin 即使有 token 也被拒(`:131` 403),除非手清 `~/.infinite-canvas/canvas-agent.json`。token 是 `crypto.randomBytes(18)`,URL query/`x-canvas-agent-token` header 双通道校验。/health、/config 豁免。这是「本地 Agent 服务」安全基线:loopback+token+Origin 白名单首连固化 —— 与 shadow-verse「网页只绑 127.0.0.1」哲学一致且更进一步。

**3. 工具归一到批量 op 数组**(`canvas-session.ts:47`):对外暴露 ~20 语义工具(create_text_node/generate_image/move_nodes…),**内部全塌缩成 `canvas_apply_ops`+`ops[]` 批量操作数组**过桥(每分支翻译成 add_node/update_node/delete_node/connect_nodes/run_generation 原子 op)。例:canvas_create_generation_flow 一次产出 [文本节点 op,config 节点 op,连线 op,选中 op,(可选)run_generation op]。浏览器只需实现一个 `applyOps(ops[])` 执行器,所有工具收敛单一执行路径。**op 数组=工具与渲染层之间的窄腰**。

## 借鉴清单

| # | 借鉴点 | 对应能力 | 状态 | 移植 | 优先级 |
|---|---|---|---|---|---|
| 1 | **MCP↔SSE 桥(MCP 驱动网页 UI)**:MCP server 薄转发→本地 HTTP→SSE 推浏览器执行→result 回填,requestId+pending+超时 | 已有零依赖 MCP(50工具)+零依赖网页,**两者未打通成「MCP 操作控制台」** | 🔵仍可借 重点 | 直接移植思路(两端已有且都绑 127.0.0.1,差一条 SSE 回执桥) | 高 |
| 2 | **Origin 锁定安全基线**(loopback+token+Origin 首连白名单+/health 豁免) | 网页只绑 127.0.0.1 | ✅部分已吸收(已绑 loopback);🔵Origin 白名单+token 可补 | 直接移植 | 中高 |
| 3 | 工具归一到批量 op 数组(语义工具→原子 op[] 事务→单一 applyOps) | 控制台/扮演页指令执行 | 🔵仍可借 | 直接移植思路 | 中 |
| 4 | 读类工具走缓存快照、写类才过桥(state 周期同步,读零往返) | MCP 工具时延 | 🔵仍可借 | 仅思路 | 中 |
| 5 | 侧边栏复用单 Codex thread+app-server delta→SSE 真流式+写操作二次确认 | 扮演页流式+安全 | ⚪以后可能用 | 仅思路 | 低 |

## 不值得碰
网页本体 Next.js/AntD/Zustand/TanStack 重型前端栈违背零依赖(暗宇宙网页是原生 HTML);具体生图供应商接入。

## 存档备忘(以后可能用)
- **`canvas-session.ts` 整文件**(~250 行)是「MCP 工具→SSE 推送→浏览器执行→回填」桥的最小可读实现,是 shadow-verse 若要「让 MCP 直接操控控制台/扮演页」的现成蓝本,**强烈建议存档精读**。
- `http-server.ts:118-137` 的 CORS+Origin+token 三段是本地 Agent 安全模板。
- AGENT_PROMPT(`config.ts:10`)规定「优先用通用生成工具、复杂批量才 apply_ops、不许模拟鼠标点击、不许让用户手抄 JSON」,是给驱动型 Agent 写系统提示的好例子。
