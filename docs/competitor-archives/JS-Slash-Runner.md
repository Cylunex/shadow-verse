# JS-Slash-Runner（Tavern-Helper）— 酒馆里用 iframe 执行前端 JS 的事实标准

> 存档 2026-06-18 · 对照 shadow-verse HUD sandbox iframe(第2刀)

## 定位
SillyTavern UI 扩展,把 AI 输出的 ```html```/```js``` 块通过 iframe 在酒馆里跑起来,并向 iframe 暴露 ~200 个酒馆操控 API(变量/世界书/预设/生成/角色卡/事件)。是「在酒馆里跑前端界面」的事实标准。

## 技术栈 / 规模
Vue 3.5(Composition+`<script setup>`)+Pinia+Vue-Router+Vite 7+TS+Tailwind 4+Zod 4;宿主侧重依赖 jQuery/lodash。打包单文件 dist。src ~2.4 万行,`@types/` 30+ .d.ts(给脚本作者的 API 类型契约)。版本 4.8.11。

## 核心认知:与 shadow-verse HUD 是两条对立路线
- **shadow-verse HUD =「隔离优先」**:`sandbox="allow-scripts"` 刻意**不给** `allow-same-origin`,iframe 是无 origin 孤岛,只能 postMessage 跟宿主对话。**因为模型输出=不可信输入,必须隔离。**
- **JS-Slash-Runner =「贯通优先」**:iframe **完全不设 sandbox**、与酒馆同源,脚本直接 `window.parent.TavernHelper.xxx()`(`predefine.js:11-19` 把 parent 的方法 merge 到 iframe window)。安全靠 README 红字+用户自审。**因为它要脚本能 triggerSlash 操控酒馆一切。**
- **结论:它的安全模型 shadow-verse 不能学**(场景相反);值得拿的只有它 57 行高度自适应里的工程经验。

## 核心机制剖析
- **iframe 创建**(`iframe.ts:78`):默认 srcdoc;blob URL 调试模式(DevTools 可打断点;blob origin 是 null,配 `<base href>` 锚相对路径)。
- **通信**:几乎不用 postMessage 做 API(全 src 仅 2 次,都是 viewport 高度);API 走同源函数直连+`this`-binding 身份(`util.ts:74` 反推哪个 iframe 在调)。
- **高度自适应**(`adjust_iframe_height.js`,57 行):ResizeObserver(body) 持久观测+rAF 合批(`scheduled` 防重入)+**直接 `frameElement.style.height`**(同源才行)。`vh` 重写(`iframe.ts:5-75`)把 `100vh` 替成 `var(--TH-viewport-height)`(治 iframe 内 100vh 塌成内容高);reset CSS `html,body{overflow:hidden}`。
- **生命周期**:Pinia store 声明式多 iframe(computed→v-for);reload_memo(uuid key)强制重建;errorCatched 隔离单 iframe 异常+toastr;blob 双重 revoke 防泄漏;Firefox srcdoc 卸载丢 frameElement 用 window.name 缓存身份。
- **流式渲染**(`Streaming.vue`):边生成边渲染 iframe,Teleport 挂宿主 div,MutationObserver 监测编辑/流式结束。

## 借鉴清单(已采纳的 P0 + 存档)

| # | 借鉴点 | 对应能力 | 状态 |
|---|---|---|---|
| 1 | **100vh 重写**→calc(var(--sv-vh)*N),治面板塌成内容高 | HUD iframe | ✅已采纳(第2刀加固) |
| 2 | **ResizeObserver 持久 observe(body)+img.onload** 兜图片加载高度跳变 | HUD iframe | ✅已采纳 |
| 3 | **rAF 合批+scheduled 标志** 防内容狂变消息刷爆 | HUD iframe | ✅已采纳 |
| 4 | **box-sizing:border-box+overflow:hidden** 注入级 reset | HUD iframe | ✅已采纳 |
| 5 | **错误可见化**(iframe window.onerror→回报宿主 console) | HUD iframe | ✅已采纳 |
| 6 | blob URL 调试模式(DevTools 可断点,origin 也是 null 与隔离一致) | HUD 调试 | ⚪以后可能用 |
| 7 | 声明式 store 管理多 iframe+reload_memo 重建 | HUD 多面板 | ⚪以后可能用 |
| 8 | Firefox window.name 缓存 iframe 身份 | HUD 多面板区分来源 | ⚪以后可能用 |

## 不值得碰(也不该用)
同源 API 体系(200 函数/triggerSlash/this-binding 身份,依赖 same-origin,与隔离模型从根排斥)、Vue/Pinia/Vite/Tailwind 全家桶(2.4 万行,需要的核心只 57 行)、酒馆事件/世界书/预设领域概念、jQuery/lodash 全局、CDN 注入第三方库。

## 存档备忘(以后可能用)
- blob 调试模式 + 声明式多 iframe 管理 + 流式渲染 + 变量管理面板/Prompt 查看器/调试器 —— HUD 从「单个」走向「多个并存+调试」时回看。
