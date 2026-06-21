# AI-Chat（实为 Narratium.ai）— ST 现代化重写（已停更）

> 存档 2026-06-18 · 对照 shadow-verse 零依赖 Python 暗宇宙引擎

## 定位
SillyTavern 的现代化全重写(Next.js+TS),主打沉浸式冒险模式 + React Flow 可视化记忆/分支;**最独特的是把角色卡/世界书/preset/正则的「创作」做成一个工具循环 Agent**——用户给一句概念,Agent 用 observe-act 循环增量生成完整 ST 兼容资产。已停更(个人学习项目)。

## 技术栈 / 规模
Next.js+React+TS,IndexedDB/local-storage,React Flow,**LangChain**(`@langchain/openai`/`ollama`)做 LLM 编排,pake 打桌面。`lib/` 核心引擎(core+nodeflow+tools+workflow+plugins),`agent-engine.ts` **1809 行**。代码 AGPL-3.0/内容 CC BY-NC-SA。**重依赖**。

## 核心机制剖析

**1. 双架构:nodeflow 工作流引擎 + agent 引擎**
- **nodeflow**(`lib/nodeflow/WorkflowEngine.ts`):节点 DAG。节点分类 entry/normal/after,`next:[]` 连边,getEntryNodes 自动推断入口。内置 UserInput/Context/WorldBook/Preset/Regex/LLM/Memory(Storage+Retrieval)/Plugin/Output。`workflow/examples/` 有 DialogueWorkflow + RAGWorkflow 范例。把「一次回复」拆成可视化可编排节点管线。

**2. 创作 Agent — 角色卡/世界书生成器**(`lib/core/agent-engine.ts`,1809 行)— ★全档最有料
**不是 RP 对话 agent,是资产创作 agent**:一句概念→自主调工具增量产出完整 ST 角色卡+世界书。
- **9 工具**(tool-registry.ts,"Real-time Decision Architecture,无复杂工具规划,直接执行"):SEARCH(联网)/ASK_USER(对根本不确定性提早问)/CHARACTER(增量填 8 必填字段 name→description→personality→scenario→first_mes→mes_example→alternate_greetings→creator_notes→tags)/STATUS/USER_SETTING/WORLD_VIEW/SUPPLEMENT(四个世界书专用)/REFLECT(任务队列空但未完成时造新任务)/COMPLETE。
- **四类世界书工具强约束**(prompt 写死规范):STATUS(实时游戏界面,constant=true/order=1/position=0,固定关键词,`<status>` XML 包裹,含时间/环境/角色面板/数值进度条)、USER_SETTING(玩家档,800-1500字四级 md,constant/order=2)、WORLD_VIEW(世界框架,多级分类,constant/order=3)、SUPPLEMENT(**必须从 WORLD_VIEW 提非空名词作 keys**,每条 500-1000字、≥5条、constant=false/order=10+/position=2 上下文激活)。
- **实时执行循环**(`agent-engine.ts:419`):每轮 decideNextAction,XML prompt(`<prompt>/<tools_schema>/<tool_usage_guidelines>`)让 planner 输出 `<think>/<reasoning>/<tool>/<parameters>`,**planner 生成全部内容、工具只存储**(DeepResearch 范式)。**完成度门控**:角色 <50%/50-80%/>80%/100% 决定继续填还是进世界书;世界书严格 STATUS→USER_SETTING→WORLD_VIEW→SUPPLEMENT 顺序;队列空则 REFLECT 造任务。+token budget+最近 5 轮(含 quality_evaluation/tool_failure 反馈)。

**3. 运行时核心**(`lib/core/`):WorldBookManager(constant+selective、AND/OR/NOT、position 0-4 分桶、recursive)、preset-assembler、prompt-assembler、regex-processor、memory-manager、character-dialogue。

## 借鉴清单

| # | 借鉴点 | 对应能力 | 状态 | 移植 | 优先级 |
|---|---|---|---|---|---|
| 1 | **创作 Agent:一句概念→完整角色卡+世界书**(五工具+完成度门控+强制顺序) | AI建变量卡+narrate;**已导入卡但无「从零生成卡/世界书」agent** | 🔵仍可借 | 仅思路+直接移植 prompt 规范(工具循环零依赖可实现) | 高 |
| 2 | **四类世界书内容规范**(STATUS 游戏界面/USER_SETTING 四级md/WORLD_VIEW 框架/SUPPLEMENT 提名词作keys) | 世界书引擎(无「生成什么内容」规范) | 🔵仍可借 | **直接移植规范文本** | 高 |
| 3 | 实时规划范式(每轮 decideNextAction,planner 生成、工具只存,完成度/顺序门控+REFLECT 造任务) | narrate+jsonloose | 🔵仍可借 | 仅思路(稳健的生成控制流) | 高 |
| 4 | nodeflow 节点 DAG(回复=可编排节点管线) | narrate+promptkit | 🔵仍可借 | 仅思路 | 中 |
| 5 | 世界书运行时(constant+selective、AND/OR/NOT、position 0-4、recursive) | **已吸收**(shadow-verse 更全:多 sticky/cooldown/delay 时效) | ✅已吸收 | — | — |
| 6 | REFLECT 自造任务+token budget+任务队列 | narrate 钩子台账 | ⚪以后可能用 | 仅思路 | 中 |
| 7 | React Flow 可视化记忆/分支 | swipe+控制台 | ⚪以后可能用 | 仅思路(需前端库) | 低 |

## 不值得碰
Next.js/React/React Flow 全栈、LangChain(重依赖,与可插拔 LLM 冲突)、IndexedDB、pake。项目已停更。价值全在 agent-engine 的创作流程设计+世界书内容规范(纯 prompt/逻辑),不在代码。

## 存档备忘(以后可能用)
- **完整「角色卡/世界书自动生成」工具循环+内容规范**:shadow-verse 当前能导入/运行 ST 卡和世界书,但**没有「一句话生成完整卡+配套世界书」能力**。`agent-engine.ts`(含 `CORE_KNOWLEDGE_SECTION` 字段定义+四类世界书工具规范+完成度门控决策树)是这条能力线**最完整现成蓝图**——将来做「AI 一键造卡/造世界书」时直接照此实现(零依赖 Python 可行,替 LangChain 为可插拔 LLM)。
- nodeflow「回复=节点 DAG」可视化编排模型 + DialogueWorkflow/RAGWorkflow 范例。
