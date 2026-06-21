# 项目解析存档 · ainovel-cli

> 存档日期 2026-06-18 ｜ 源码路径 `F:/Project/projects/Tavern/ainovel-cli`
> 对照基准：shadow-verse checks.py（已吸收 stylestat）+ reflect 反思 + memory.py + narrate 产线 + hooks 台账

---

## 一、定位 / 技术栈 / 规模

- **定位一句话**：Go 全自动长篇小说引擎——Coordinator/Architect/Writer/Editor 四角色 + flow 状态机驱动，stylestat 全书统计 + diag 规则诊断（统计归代码、裁定归 LLM）+ 四维结构化相关章节反查（零 embedding 长篇召回）+ 卷弧双层滚动规划（指南针 + 视野滚动），TUI 交互，支持 500+ 章。
- **技术栈**：Go（go.mod，少量依赖：bubbletea TUI、goreleaser 打包）；分层 `internal/`（agents/diag/domain/host/stylestat/tools/store/rules/entry）；存储 JSON 文件（`.ainovel/` 下 progress/outline/layered_outline/compass/style_rules 等）；可插拔 LLM（coordinator/architect/writer/editor 各自配 provider+model）；EPUB/TXT 导出。
- **规模**：内部包众多——`internal/diag/` 16+ 规则文件（flow/quality/planning/context 四类）；`internal/tools/` novel_context（上下文组装核心）+ plan_chapter + save_volume_summary；`internal/stylestat/stylestat.go`（359 行，含测试）；`internal/host/` flow/sim/imp/exp/reminder。docs 4 篇（architecture/context-management/observability/refactor-flow-driven）。README 29KB。

---

## 二、核心机制逐子系统剖析

### 2.1 stylestat 全书风格统计（`internal/stylestat/stylestat.go`）

**已被 shadow-verse `checks.py:check_book` 大部分吸收**，此处记录其完整设计供对照：

- **设计哲学**（文件头注释）：弧内评审窗口（~10 章）对全书级模式固化天然失明——句式 tic 章均几十次、章末同构、跨章复读，单章看每处都「正常」，只有全书统计能暴露。**统计归代码（确定性、零幻觉），裁定归 LLM**（editor 按数字判 aesthetic 维度分，writer 据此自避免）。
- **门槛**：`minChapters=5`（样本太小频率无意义）；动态短语只看最近 `phraseWindow=20` 章（writer 要避免的是「现在的口头禅」）。
- **统计字段**（`Stats`）：
  1. **Patterns 句式 tic 章均**（`patternDefs:73`）：4 个通用 AI 腔正则——矫正句「不是…而是…」/ 计时量词「X息/X瞬」/ 明喻「像一/仿佛/如同/宛如」/ 沉默节拍「沉默了/没有说话/没有回头」。给 Total + PerChapter。
  2. **TopPhrases 高频短语挖掘**（`minePhrases:129`）：窗口内挖 3-6 字汉字片段，阈值 `max(8, 章数/2)`；过滤首尾虚词（`gramEdgeStop`）、纯汉字校验、**stopword 人名拆 2 字片段过滤**（人名天然高频不算文风问题，`stopwordBigrams:205`）；同频取更长的；与已选互为子串去重，top 8。
  3. **RepeatedSentences 跨章逐字复读**（`repeatedSentences:229`）：跨 ≥3 章逐字重复的 ≥12 字句子，剥引号再归并（同句带/不带引号不算两条），top 5。
  4. **Ending 章末同构**（`endingShape:271`）：短结尾率（末行 ≤30 字）+ 中位数字数——短结尾本身合法，全书同构才是问题。
  5. **OpeningTimeRate 开篇时间词**（`openingTimeRate:295`）：首段命中「夜/清晨/黎明/天亮/醒来/晨光/一整夜」的章节比例（套路化转场）。
  6. **TitleFormats 标题前缀混用**（`titleFormats:305`）：「第N章」前缀有/无混用计数——统一格式不报，只有**混用**才上报（机制痕迹暴露在产物里）。

> **状态**：✅ shadow-verse checks.py 已实现等价的句式 tic 章均 / 跨章逐字复读 / 章末短结尾率 / 开篇时间词率 / 标题问题。stopword 人名过滤、短语挖掘的子串去重等细节可对照查漏。

### 2.2 diag 规则化诊断（`internal/diag/`）

**用户点名「仍可借的重点」**。这是把「全自动跑出来的工件」喂进**确定性规则集**，产出可执行 Finding 的诊断系统：

- **统一类型**（`types.go`）：`Finding{Rule, Category, Severity, Confidence, AutoLevel, Target, Title, Evidence, Suggestion}`。
  - Severity：critical（阻塞/数据损坏）/ warning（降质/费 token）/ info（可优化）。
  - Category：flow / quality / planning / context 四维。
  - Confidence：high（确定）/ medium（启发式）/ low（粗略信号）。
  - AutoLevel：none（仅报告）/ suggest（建议需确认）/ safe（可安全自动执行）——决定能否转成自动动作。
  - **Target 指向作用面**：`prompt.writer` / `prompt.editor` / `prompt.architect` / `context.foreshadow` / `runtime.flow` / `runtime.recovery` 等——诊断直接告诉你「该改哪个 prompt / 哪段流程」。
- **入口**（`diag.go:Analyze`）：load snapshot → 跑全部 16 规则 → 按 severity 排序 → `PlanActions` 把高置信 Finding 转成可执行 Action（emit_notice / enqueue_follow_up，带 Fingerprint 去重）。
- **quality 规则**（`rules_quality.go`，最值钱的一组）：
  - `ChronicLowDimension`：某评审维度跨多章均分 <70 → 「检查 Writer prompt 该维度指引 / Editor 评分标准」。
  - `ContractMissPattern`：合同履约率 <70% → 「Writer 可能没读 contract，或 required_beats 太激进」。
  - `HookWeakChain`：hook 评分连续 ≥3 章 <75 → 「检查 hook_goal 执行 / 校准 Editor 对 hook 的举证标准」。
  - `PayoffMissPattern`：带 payoff_points 的章兑现率 <60% → 「payoff_points 太多太空 / Writer 只铺垫没兑现」。
  - `ExcessiveRewrites`：改写率 >50% → 「Writer 产出持续低于 Editor 阈值，两端标准没对齐」。
  - `WordCountAnomaly`：字数 <均值 40% 或 >250% → 「极短=截断，极长=耗窗口」。
- **planning 规则**（`rules_planning.go`）：StaleForeshadow（伏笔超阈值未推进，阈值 = `max(8, 完成章数/3)`）/ CompassDrift（指南针 >15 章未更新）/ OutlineExhausted（大纲耗尽未完结，critical+AutoSafe）/ MissingSummaries（完成章缺摘要）。
- **flow 规则**（`rules_flow.go`）：RewritePendingPressure / OrphanedSteer（未消费的转向指令，high+AutoSafe）/ PhaseFlowMismatch / ChapterGaps。
- **context 规则**：GhostCharacter / TimelineGaps / RelationshipStagnation。

> **价值核心**：这套「多章工件 → 确定性规则 → 带证据+指向的 Finding → 可选自动动作」正是 shadow-verse **reflect 反思该升级的方向**——把 reflect 从「LLM 自由反思」升级为「规则诊断聚合 + LLM 解读」。每条规则的「证据格式 + Suggestion 指向 writer 还是 editor 还是配方」尤其值得直接抄。

### 2.3 四维相关章节反查（`internal/tools/novel_context.go:534` `buildRelatedChapters`）

**用户点名「向量记忆零依赖先行版」**。长篇（总章数 >30）写当前章时，**不靠 embedding**，纯用结构化数据从四个维度反查相关历史章节，去重后最多 5 条：

1. **伏笔反查**（`:570`）：活跃伏笔的 ID/描述是否出现在当前章大纲文本（标题+核心事件+场景）里 → 推荐该伏笔的埋设章。
2. **角色出场反查**（`:580`）：从大纲匹配出场角色（名+别名），批量单次遍历查这些角色最后出场章（IO 从 O(角色×章) 降到 O(章)）。
3. **状态变化反查**（`:595`）：在已加载的 state_changes slice 上查角色最近一次状态变化章（零 IO）。
4. **关系反查**（`:606`）：当前章涉及 ≥2 角色时，查这些角色对之间关系最后变化章。

每条带 `Reason`（如「伏笔X(描述)埋设章」「角色'名'最后出场章」「A-B关系变化」）。`add()` 守卫：排除未来章、排除最近 10 章（太近不推荐）、去重。

> **价值核心**：这是「**用结构化台账（伏笔/出场/状态/关系）做相关性召回，绕开向量库**」的完整工程实现——正契合 shadow-verse 零依赖原则。shadow-verse 的 memory.py + hooks.json 已有伏笔/状态台账，可据此实现等价的零 embedding 长程召回，是**仍可借的重点**。

配套 `selectStoryThreads`（`:665`）：伏笔数超阈值时，按当前章焦点词（大纲+章计划）匹配活跃伏笔，召回「当前章可能需承接的既有伏笔」；`selectReviewLessons`（`:705`）召回前 1-3 章评审教训。

### 2.4 卷弧双层滚动规划（README §长篇滚动规划 + `novel_context_builders.go` architect 路径）

**用户点名**。传统一次规划所有章 → 300+ 章时大纲空洞。本系统模拟网文作者真实流程：

- **指南针 Compass**：终局方向 + 活跃长线（open_threads）+ 规模估计（estimated_scale），每次卷边界由 Architect 更新，故事方向可随创作演化。
- **视野滚动**：初始只规划前 2 卷弧骨架 + 第 1 弧详细章节；后续弧/卷写到时再展开，每次展开参考前文摘要 + 角色快照 + 风格规则（越往后越精确）。
- **骨架弧**（`skeleton_arcs`）：只有 goal + 预估章数（`IsExpanded()` 判未展开），到达时展开。
- **弧边界检测**：自动识别弧/卷结束 → 触发 Editor 弧级/卷级评审 + 摘要生成 + 下一弧/卷展开。
- **通用弧型模板**：成长突破弧 / 竞技对抗弧 / 探索发现弧 / 恩怨冲突弧 / 日常过渡弧，每型有参考密度 + 题材映射。
- **分层摘要召回**（`buildChapterContext` 分 Layered/非 Layered 路径）：近处用章摘要，中距离用弧摘要，远处用卷摘要——层层压缩不丢信息，支撑 500+ 章。
- **completion_signals**（`completionSignals:635`）：把「全书是否该结尾」的关键事实（完成章数/字数/规划章数/卷数/规模估计/open_threads/活跃伏笔数）集中呈现给 Architect，让它裁定 complete_book / append_volume 时一眼看到对照面（散落在各处靠 LLM 脑算容易漏）。

### 2.5 上下文信封分层（`novel_context_builders.go`）

写章上下文按记忆类型分「信封」组装：`working_memory`（当前章大纲/章计划/章合同/上一章尾 800 字/近期状态变化）/ `episodic_memory`（角色/关系/伏笔台账/配角名册 RecentActive/related_chapters/style_stats）/ `reference_pack`（style_rules 或 style_anchors + voice_samples 对话样本）/ `selected_memory`（story_threads + review_lessons）。每段都有「canonical 路径 + 顶层镜像」双重注入防 prompt 指针指空。`memory_policy` 字段告诉 LLM 各类记忆的取用策略。

### 2.6 flow 状态机 + 物理兜底（README §可观测性 + `host/reminder/`）

- 纯函数 reminder generator 读 Progress+Outline，每轮 pre-turn 生成 `<system-reminder>`：`flow`（当前该做什么/弧末刹车）/ `queue_guard`（队列未清禁止新章）/ `book_complete`（全书完成才放行）。
- 物理兜底 `StopGuard`：`phase≠Complete` 时拒绝 `end_turn`——防止 LLM 自行提前收尾。
- 导入续写：`/import` 把已有小说反推导入（按章切 → LLM 反推 premise/角色/世界观/分层大纲/指南针 → 逐章落盘 → 自动接力续写）。

---

## 三、对 shadow-verse 的价值

| # | 借鉴点 | 对应能力 | 状态 | 移植方式 | 优先级 |
|---|--------|----------|------|----------|--------|
| 1 | **stylestat 全书统计** | checks.py check_book | ✅已吸收（句式tic/跨章复读/章末同构/开篇时间词/标题混用） | 已直接移植 | — |
| 2 | **diag 规则化诊断**（quality 6 规则 + Finding 带证据+指向 + AutoLevel） | reflect 升级为规则诊断 | 🔵仍可借（**重点**） | 直接移植（纯规则，零依赖） | **高** |
| 3 | **四维相关章节反查**（伏笔/出场/状态/关系 → 召回 5 章，零 embedding） | memory.py 长程召回 | 🔵仍可借（**重点**） | 直接移植（结构化反查，契合零依赖） | **高** |
| 4 | **卷弧双层滚动规划**（指南针 + 视野滚动 + 骨架弧 + 弧边界检测 + 弧型模板） | narrate 长篇规划层 | 🔵仍可借 | 仅思路（设计成本高，需配合 flow） | **高** |
| 5 | **分层摘要召回**（近章/中弧/远卷三级压缩） | memory.py 长篇上下文 | 🔵仍可借 | 仅思路 | 中 |
| 6 | **completion_signals 集中事实**（结尾裁定对照面） | narrate 全书收束判断 | 🔵仍可借 | 直接移植（聚合现有字段） | 中 |
| 7 | **stopword 人名拆 2 字过滤**（短语挖掘排除高频人名） | checks.py 短语挖掘提纯 | 🔵仍可借（checks.py 可查漏） | 直接移植 | 中 |
| 8 | **上下文信封分层 + canonical/镜像双注入** | narrate_prep 上下文包组织 | 🔵仍可借 | 仅思路 | 中 |
| 9 | **flow 物理兜底 StopGuard**（phase≠Complete 拒 end_turn） | narrate 防提前收尾 | ⚪以后可能用 | 仅思路 | 低 |
| 10 | **pre-turn system-reminder 生成**（flow/queue_guard/book_complete） | narrate 产线提醒 | ⚪以后可能用 | 仅思路 | 低 |
| 11 | **/import 反推导入已有小说续写** | 导入续写能力 | ⚪以后可能用 | 仅思路 | 低 |
| 12 | **PlanActions 高置信 Finding 转自动动作 + Fingerprint 去重** | reflect 后的自动跟进 | ⚪以后可能用 | 仅思路 | 低 |

**重点**（用户点名）：reflect 规则化诊断（#2）、四维相关章节反查（#3）、卷弧滚动规划（#4）。

---

## 四、不值得碰

- **Go 语言实现本身**：shadow-verse 是 Python，借算法思路不借代码（diag/反查/stylestat 都是可重写的纯逻辑）。
- **bubbletea TUI**（`internal/entry/tui/` 30+ 文件）：交互外壳，shadow-verse 走 CLI/MCP/webapp。
- **goreleaser 多平台打包**：分发无关。
- **EPUB 导出器**（`host/exp/epub.go`）：shadow-verse 已有导出，非优先。
- **四角色编排的完整 host/flow 状态机**：与 shadow-verse narrate 产线是平行设计，借「物理兜底/弧边界」纪律不照搬整机。

---

## 五、存档备忘（以后可能用，单列）

1. **diag 每条规则的阈值常量**（`diag.go:12` ThresholdDimScoreLow=70 / ContractMissRate=0.3 / RewriteRate=0.5 / HookWeakScore=75+连续 3 章 / PayoffMissRate=0.4 / CompassDrift=15 / ForeshadowMin=8）是一份现成的「诊断阈值校准表」，shadow-verse reflect 规则化时可直接吃。
2. **StaleForeshadow 动态阈值** `max(8, 完成章数/3)`——伏笔停滞容忍度随书长自适应，比固定阈值好，可直接抄。
3. **Target 字段枚举**（prompt.writer/editor/architect + context.* + runtime.*）是把诊断结果「路由到具体可改对象」的设计，shadow-verse reflect 输出可加这个字段。
4. **buildRelatedChapters 的 `add()` 守卫逻辑**（排未来/排最近 10 章/去重）是相关性召回的通用过滤模板。
5. **弧型模板（5 型 + 题材映射 + 参考密度）** 是长篇节奏规划的现成知识，若 shadow-verse 做卷弧规划可吃。
6. **AutoLevel 三级**（none/suggest/safe）是「诊断→自动化」的安全分级，决定哪些 Finding 可无人值守执行——shadow-verse 若做自动跟进必用。
7. docs/ 四篇（architecture/context-management/observability/refactor-flow-driven）是同类长篇引擎的设计文档，架构对照价值高。
