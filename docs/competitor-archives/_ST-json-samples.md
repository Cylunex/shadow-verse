# 两个散落 ST JSON 资源（正则脚本 + 预设）

> 存档 2026-06-18 · 均落在 shadow-verse「已支持导入 ST 正则/预设」范围内 · 价值=导入器兼容性回归样本 + HUD/后处理范式

---

## 【6.12】数据库多功能美化正则1.json — ST 正则脚本

**格式**:单个 ST regex script JSON(**非数组**)。字段:`id`(uuid)/`scriptName`/`findRegex`/`replaceString`(41132 字符)/`trimStrings`([])/`placement`([1]=render前/楼层显示)/`disabled`/`markdownOnly`(true)/`promptOnly`(false)/`runOnEdit`(true)/`substituteRegex`(0)/`minDepth`(null)/`maxDepth`(5)。replaceString 是一整个 `<!DOCTYPE html>` 页面。

**核心机制**:
- findRegex 四捕获组把「本轮用户输入」块拆成 ①开头标记 ②正文 ③检定结果 meta 块 ④收尾,对应 replaceString 里 `$1$2$3$4` 注入到 `<script id="rawData">`。
- placement[1]=仅显示/AI 输出渲染时作用(不改 prompt);markdownOnly=只作用 markdown 渲染层;maxDepth:5=只对最近 5 楼。纯美化不污染上下文。
- 41KB HTML 面板:完整页+单 `<style>`+2 `<script>`,把 `$1$2$3$4` 塞进 `<script type="text/plain" id="rawData">`,JS 解析渲染成可折叠数据面板。运行在 ST 的 **sandbox iframe** 里,`<script>` 主动从 `window.parent.document` 拷贝字体样式实现与父页字体同步。
- **用到 14 个 CSS 变量(107 处 var())**:继承 ST 主题 `--SmartThemeTextColor`/`--mainFontSize`/`--mainFontWeight`;自建语义层 `--st-text`/`--t-main`/`--t-dim`/`--t-mute`/`--t-line`(用 `color-mix(in srgb, var(--st-text) X%, transparent)` 派生明暗)/`--tr`(统一过渡)。`color-scheme:dark light`+`light-dark()` 自适应。

**借鉴**:
| 借鉴点 | 对应能力 | 状态 |
|---|---|---|
| ST 正则脚本格式(全字段) | 导入 ST 正则 | ✅已支持导入 |
| **HUD HTML 面板继承 ST 主题变量**(--SmartThemeTextColor + color-mix 派生四级文字层) | HUD sandbox iframe | 🔵仍可借(直接移植 CSS 约定) |
| **sandbox iframe 主动从 parent 拷贝字体样式** | HUD iframe 与宿主样式同步 | 🔵仍可借(JS 思路) |

**存档备忘**:HUD 主题继承范式 `--st-text:var(--SmartThemeTextColor, light-dark(CanvasText,#d8dee5))`+color-mix 派生 dim/mute/line+`--tr` 统一过渡 —— shadow-verse HUD 想跟宿主主题自适应时可直接抄;iframe↔parent 字体同步 JS 是将来 HUD 要和宿主字体一致的现成做法。

---

## 夏瑾 双鱼座 Beta 0.40.json — ST 预设

**格式**:ST Chat-Completion preset,45 顶层键。`prompts` 140 条;`prompt_order` 2 角色映射(100000 默认 11 条/100001 共 57 条仅 32 启用);`extensions` 3 键(regex_scripts 9 条+SPreset+tavern_helper)。

**核心机制**:
- 采样参数全集:temperature(1)/frequency_penalty/presence_penalty/top_p/top_k/top_a/min_p/repetition_penalty;max_context_unlocked(true)/openai_max_context(2000000)/openai_max_tokens(32000)/stream_openai/use_sysprompt/names_behavior(0)/reasoning_effort(high)/seed(-1)。
- prompts[] 字段:identifier/name/role(user|system|model)/content/enabled/marker/system_prompt/injection_position/injection_depth/injection_order/injection_trigger。**injection_position 全 0(相对位置按 order)**,本预设未用绝对深度注入;marker:true 8 条(Chat History/World Info/Examples 插入锚);**enabled:false 128 条**(模块默认关靠 prompt_order 按需启用)。
- prompt_order:每角色一份 order:[{identifier,enabled}],决定该角色用哪些 prompt 及顺序(「大 prompt 池+按角色挑选/排序」ST 标准机制)。
- **内嵌 regex_scripts(9 条)**:全 promptOnly:true(只改发给模型的内容):包裹最新指示(placement[1]注入前)、八股抹除、切小总结、语气/破折号/比喻正则(placement[2]=AI 输出后处理)。即「喂模型前清洗+输出后润色」正则流水线。

**借鉴**:
| 借鉴点 | 对应能力 | 状态 |
|---|---|---|
| ST 预设全字段(采样+prompt_order+injection_*) | 导入 ST 预设 | ✅已支持导入 |
| extensions.regex_scripts 随预设打包 | 导入预设时联动导入正则 | 🔵仍可借(确认导入器解析 extensions.regex_scripts) |
| 「大 prompt 池+默认 disabled+order 按角色挑选」模块化开关 | 预设/护栏模块化 | ⚪以后可能用 |
| promptOnly 正则「喂模型前清洗+输出后润色」两段(placement 1/2) | play 透镜双段输出后处理 | 🔵仍可借 |

**存档备忘**:导入器回归样本(验证 prompt_order 双角色映射、injection_position=0、extensions.regex_scripts 嵌套三个易漏点);promptOnly 正则两段流水线(placement[1]喂模型前/placement[2]输出后)是 play 透镜「输入清洗+输出润色」后处理的现成 placement 语义范式。
