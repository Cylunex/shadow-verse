# st-image-auto-generation — 极简出图扩展

> 存档 2026-06-18 · 对照 shadow-verse

## 定位
极简 SillyTavern 出图扩展——检测 AI 回复里的 `<pic prompt="...">` 标签即自动调酒馆原生出图,把图插回消息。

## 技术栈 / 规模
单文件纯前端 ESM JS(`index.js` 507 行)+ settings.html + i18n。零自建后端,完全复用 ST 自带 `/sd` slash 和生图 API。manifest 1.0.5,作者 wickedcode01。4 项目里最小。

## 核心机制剖析(标签触发出图)

整个扩展两个 ST 事件钩子:

**1. 提示词注入**(`index.js:299-347`,钩 CHAT_COMPLETION_PROMPT_READY):每次发请求前注入出图引导 prompt(默认 `<image_generation>You must insert a <pic prompt="...">...`)。注入位置可配:role(deep_system/user/assistant)+depth(0=末尾 push;>0 从末尾往前数第 depth splice)。**提示词注入与正则触发解耦**——可换世界书/别的插件做条件注入,本插件只管「检测+出图」。

**2. 标签检测与出图**(`index.js:351-506`,钩 MESSAGE_RECEIVED)— ★
①正则 `/<pic[^>]*\sprompt="([^"]*)"[^>]*?>/g`(**第一个捕获组必须是 prompt**)matchAll。②每匹配 `setTimeout(…,0)` 延迟执行(先让消息渲染防阻塞),调 `SlashCommandParser.commands['sd'].callback({quiet}, prompt)`。③**三种插入模式**:INLINE(push 进 `message.extra.image_swipes` 多图候选+设主图)/REPLACE(`<pic>` 原地替换 `<img>`,属性 escapeHtmlAttribute 转义防注入)/NEW_MESSAGE(新建消息,兼容性最好)。每次出图后 saveChat。

## 借鉴清单

| # | 借鉴点 | 对应能力 | 状态 | 移植 | 优先级 |
|---|---|---|---|---|---|
| 1 | `<pic prompt="...">` 标签触发出图(LLM 嵌标签→正则捕获→出图→插回) | 立绘/出图 | 🔵仍可借 | 仅思路(「正文内联触发出图」最简范式) | P2 |
| 2 | 提示词注入与触发解耦(注入可换世界书/预设,本体只管检测) | 世界书引擎/预设组装 | ✅已吸收(已有世界书触发+promptkit) | — | — |
| 3 | depth/position 注入定位(@D 深度+role 选择) | 世界书 position@D | ✅已吸收 | — | — |
| 4 | image_swipes 一条消息挂多图候选 | swipe 一楼多候选 | ✅已吸收(图片版同构) | — | — |
| 5 | setTimeout(…,0) 让渲染先行再异步出图、HTML 属性转义防注入 | HUD/渲染 | ⚪小技巧 | 仅思路 | P3 |

## 不值得碰
几乎整体——强耦合 ST(SlashCommandParser/appendMediaToMessage/event_types/jQuery DOM)的极薄胶水,无可移植独立算法。价值纯粹是「标签触发出图」范式参考,思路已记,代码不必碰。

## 存档备忘(以后可能用)
无独立可存档算法。作为「ST 内联标签触发出图最小范式」备忘:正则首捕获组=prompt → 调宿主出图 → 三种插入模式(inline swipe/replace img/new message)。shadow-verse 已有的 swipe 多候选+世界书 position@D 已覆盖其核心思想。
