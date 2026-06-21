# infiplot — AI 实时生成互动 galgame

> 存档 2026-06-18 · 对照 shadow-verse · Scene/Beat 分支图 = 线分支 backlog 的现成 schema

## 定位
用五职能 Agent 编排、实时生成的《完蛋！我被美女包围了！》——无预设剧情,每幕背景图+对话树+配音全部 AI 现场生成。

## 技术栈 / 规模
Next.js 16/React 19/TS,**服务端刻意无状态**(client 携带完整 Session 往返)。四类供应商:Text/Image(Runware/gpt-image/Gemini)/Vision/TTS。`lib/engine/`(director/orchestrator/writer/agents/prompts/jsonParser),`lib/types/index.ts` 568 行是领域契约单一真相源,`director.ts` 480 行。AGENTS.md 含 File Dependency Map + What Not To Do。

## 核心机制剖析

**1. 五职能 Agent 两阶段重叠编排**(`director.ts:165` directScene)— ★
五职能:Architect(仅起始建 StoryState)/Writer/CharacterDesigner/Cinematographer/Painter。
- **关键创新 = Writer 拆两阶段让出图早于对话**(`:36` ASCII 关键路径图):
  - **Phase A**(串行小):runWriterPlan 产 WriterPlan 骨架(sceneSummary/sceneKey/entryBeatId/cast/entrySpeaker)。出图只需骨架不需对话。
  - **Phase B**(立即启动、长、与整条出图管线重叠):runWriterBeats 产 beats[]+storyStatePatch,被 Phase A 约束;最后才 await,失败降级单 beat。
  - 并行段:CharacterDesigner ×N ∥ Cinematographer(Promise.all)。
  - **精细调度**:仅入场 beat 立绘阻塞 Painter(它们是 referenceImages),其余立绘+全部配音 overlap 绘画;配音永不在绘画路径上。
  - 时延地板从 `beats+image` 降到 `max(beats,image)`。AGENTS.md 死命令:Phase A→Painter 启动间不许加阻塞调用。
- mergeCharacters 按 name 保旧 voice/portrait;pickPriorSceneReference 按 sceneKey 复用前幕图(优先 URL 而非 UUID,Runware UUID 易 failedToTransferImage)。

**2. Scene/Beat 分支图数据模型**(`lib/types/index.ts:7`)— ★对应线分支 backlog
- `Scene`=一张图 + 一棵 Beat 节点图;entryBeatId 落点,sceneKey 物理空间 slug("classroom-dusk")做视觉连续性锚。
- `Beat`(`:7`):narration/speaker/line/lineDelivery(仅 TTS)/activeCharacters[]/next。`BeatNext`=continue{nextBeatId} 或 choice{choices[]}。`BeatChoiceEffect`=advance-beat{targetBeatId}(同图推进,零网络/不重绘)或 **change-scene{nextSceneSeed}(出图换幕)**。每幕至少一个 change-scene 出口。
- `SceneHistoryEntry.storyStateAfter`(`:112`)逐幕快照,支持分享回放从任意前缀续玩。
- **beat=节点、next=边、change-scene=真分叉、advance-beat=同节点推进** —— 完整分支叙事图 schema。

**3. StoryState stable/volatile 双区**(`lib/types/index.ts:239`):stable(Architect 写、Writer 不许碰:logline/genreTags/protagonist/castNotes)+volatile(每幕 StoryStatePatch 重写:synopsis/openThreads/relationships/nextHook)。`applyStoryStatePatch`(`director.ts:137`)只覆盖 volatile。解决「无单一 throughline 则 Writer 从扁平 beat log 重推全弧漂移」——长期记忆稳定层/易变层分治。

**4. parseJsonLoose 四级容错**(`jsonParser.ts:105`):①直接 parse ②```json 围栏 ③firstCompleteJsonValue 栈式扫首个完整值(处理重复吐对象)④首 `{` 到末 `}` 切片 ⑤preRepair 定向正则(`"k:"v"`→`"k":"v"`)+jsonrepair(截断/缺逗号/单引号/Python None)。Agent 四段范式:raw 宽容→coercion 归一→repair 修结构→fallback 安全值不抛。

**5. stable-prefix 缓存**(`prompts.ts:403`):提示词切「稳定前缀/动态后缀」喂 prompt caching。前缀=session 标量+圣经 spine+单调增长列表+历史 0..N-2 幕;后缀=volatile patch+last-beat+转场 hint。铁律:**每个 section header 即使空也必出、位置不许漂**否则毁缓存命中。

## 借鉴清单

| # | 借鉴点 | 对应能力 | 状态 | 移植 | 优先级 |
|---|---|---|---|---|---|
| 1 | **Scene/Beat 分支图 schema**(beat 节点+continue/choice 边+advance-beat/change-scene 双效果) | **线分支 backlog** | 🔵仍可借 重点 | 直接移植 schema(Python dataclass) | 高 |
| 2 | **五职能 Agent 两阶段重叠编排**(Writer 拆 plan/beats 让出图早于对话,只 entry 立绘阻塞绘画) | narrate/群聊/出图 render 调度 | 🔵仍可借 重点 | 仅思路(asyncio 复刻 max(a,b) 地板) | 高 |
| 3 | StoryState stable/volatile 双区+逐幕快照 | 长期记忆+故事时间线 | 🔵仍可借 | 直接移植思路(记忆加稳定/易变分治+patch merge) | 中高 |
| 4 | parseJsonLoose 四级+Agent 四段范式 | MCP/LLM 输出解析 | 🔵仍可借 | 直接移植(已有 jsonloose 可对照补) | 中 |
| 5 | stable-prefix 缓存(section 永不缺位、动态进后缀) | 可插拔 LLM 提示词组织 | ⚪以后可能用 | 直接移植思路 | 中 |
| 6 | sceneKey 物理空间 slug 视觉连续性+参考图优先级 | render 出图 | 🔵仍可借 | 仅思路 | 中 |
| 7 | 服务端无状态+client 携带 Session | 控制台/MCP 状态 | ⚪以后可能用(本地单机价值低) | 仅思路 | 低 |

## 不值得碰
Next.js16/React19/Tailwind/Vercel/Cloudflare Workers 全套重型 SSR 外壳+海量 npm,违背零依赖;各家图像/TTS 供应商 SDK 细节。

## 存档备忘(以后可能用)
- AGENTS.md 的 **File Dependency Map + What Not To Do** 是工程不变量文档范本,值得作为 shadow-verse AGENTS/CLAUDE.md 写法参考。
- `director.ts:36-66` ASCII 关键路径图把「为什么拆 Writer」讲透,编排设计文档样板。
- StepFun 路径「生成 Agent 顺带从目录选 voiceId、零额外 LLM 调用、keyword 打分兜底」是「让生成 Agent 顺带选资源不额外往返」的好模式。
