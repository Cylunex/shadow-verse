# Nika-Character-Studio — 纯前端编卡器 + mini 酒馆

> 存档 2026-06-18 · 对照 shadow-verse · 纯原生 HTML/JS,与 shadow-verse 网页哲学一致

## 定位
仿 SillyTavern、纯前端零安装的「编卡器+内置 mini 酒馆」一站式 AI 角色扮演工作室,含 Nika 智能体辅助编卡。

## 技术栈 / 规模
**纯原生 HTML/CSS/JS,无框架无构建工具**(与 shadow-verse 网页原生 HTML 哲学一致)。IndexedDB 本地存储;Canvas API;ST V2/V3+PNG 内嵌卡兼容。多 API。`index.html`(6385 行编卡器)+`chat.html`(15010 行 mini 酒馆)+`chat_wechat_theme.html`(11325 行)+`js/`(part1/2/3 ~20k 行+agent.js 2325 行)。总 ~55k 行纯前端。AGPL-3.0。

## 核心机制剖析

**1. 纯 HTML 编卡/扮演页**(同 shadow-verse 哲学):零框架零打包,Start.bat 直开 index.html。chat.html 把 LLM 输出的 HTML 用 **sandboxed iframe** 渲染(`chat.html:8831`,sandbox=`allow-scripts allow-same-origin allow-forms allow-modals allow-popups`),注入透明背景(`:8482`),移动端/PC 分支用 srcdoc,避免同时渲多个复杂 iframe 卡顿。**与 shadow-verse 扮演页「HUD sandbox iframe」同技术**(但 Nika 给了 allow-same-origin,shadow-verse 故意不给——隔离更强)。ContextManager(`:9919`)仿 ST 做 token 预算/裁剪(中文 1.5字/token、英文 4字/token)。

**2. state 变量卡**(小白X 2.0 state):角色卡带 tasks(`<<taskjs>>...<</taskjs>>` 代码块跑循环任务维护变量 `/setvar key=hp 100`)。状态同步走 `LWB_StateV2.applyText('<state>\n$schema...\n数据:\n  字段:"值"\n</state>')`(`part2.js:4395`),AI 在回复吐 `<state>` 块同步;配**隐藏正则**(regex_scripts,`agent.js:159`)把 `<state>` 标签从展示剥掉保沉浸 —— 即「变量卡+隐藏 state 标签+HUD 渲染」三件套。**对应 shadow-verse 已有的变量三段式+扮演页变量+HUD,机制同构**。

**3. swipe 雏形**(`chat.html:9890` regenerateMessage):**截断重发**(splice 删该 AI 消息及之后→重发),**不保留多版本不能切换**。是 swipe 最朴素雏形,**shadow-verse 已有完整多版本 swipe,故此项反而弱于现状——不值得借,仅对照**。

**4. 小说→世界书**(`part1.js:1899`):上传 txt→多编码自动探测(UTF-8/GBK/GB2312/Big5)→**章回自动检测**切章→大文件分段 AI 批量抽世界书条目(可暂停续跑)。条目=`{keys:[触发词],comment:名称,content}`层级结构。

**5. Nika 编卡 Agent**(`agent.js`):给 LLM 的上下文是**卡的清单视图**(世界书/正则/任务只列名+触发词省 token,`:148`),LLM 用 `/peek field|worldbook|regex|task|greeting`+`/list` **按需拉全文**(`:222` 懒加载);改卡靠 LLM 吐 ` ```json:patch ` 块(set/worldbook_add/worldbook_update/regex_add/task_add/greeting_add)前端 apply。**「清单视图省 token+peek 懒加载+json:patch 增量改」是 Agent 编辑结构化文档的轻量范式**。

## 借鉴清单

| # | 借鉴点 | 对应能力 | 状态 | 移植 | 优先级 |
|---|---|---|---|---|---|
| 1 | 纯原生 HTML/JS 编卡+扮演零框架+LLM HTML 输出 sandboxed iframe | 已有零依赖网页+HUD sandbox iframe | ✅已吸收(哲学/技术同构,可对照 sandbox 权限位+透明注入+移动端分支) | 仅思路 | 低 |
| 2 | 小白X state 变量卡+隐藏正则+HUD 渲染 | 已有变量卡+三段式+HUD iframe | ✅已吸收(同构) | 直接移植思路 | 低 |
| 3 | **小说→世界书**(多编码探测+章回检测+分段 AI 批量抽条目可暂停续跑) | 世界书引擎+narrate+知轩藏书 7815 本 | 🔵仍可借 | 直接移植思路(零依赖 Python 做 txt→世界书上游正合适) | 中高 |
| 4 | Nika Agent:清单视图省 token+/peek 懒加载+json:patch 增量改 | MCP 工具设计/Agent 编辑卡 | 🔵仍可借 | 直接移植思路 | 中 |
| 5 | ContextManager token 预算裁剪(中英分别估算) | 长期记忆/上下文窗口 | 🔵仍可借 | 仅思路 | 中 |
| 6 | ST V2/V3+PNG 内嵌卡兼容+IndexedDB 本地库 | 角色卡互通 | ⚪以后可能用 | 直接移植思路 | 低 |
| 7 | swipe=截断重发雏形 | 已有完整多版本 swipe | —(不借,shadow-verse 现状更强) | — | — |

## 不值得碰
swipe 截断重发不如现有多版本 swipe(不倒退);微信主题等纯 UI 皮肤、AI 前端美化;各 API 供应商接入。

## 存档备忘(以后可能用)
- **小说→世界书的章回检测+多编码探测**(`part1.js:1899` 周边)直接服务 AI 小说创作+知轩藏书整理库,**优先级实际可上调,建议单独精读存档**。
- `agent.js` 的「清单视图+/peek 懒加载+json:patch」是给 MCP 工具/编卡 Agent 省 token 的好范式。
- chat.html iframe sandbox 权限位(`:8834`)+透明背景注入(`:8482`)是 HUD iframe 安全/样式对照样本。
