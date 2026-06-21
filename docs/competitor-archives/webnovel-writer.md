# 项目解析存档 · webnovel-writer

> 存档日期 2026-06-18 ｜ 源码路径 `F:/Project/projects/Tavern/webnovel-writer`
> 对照基准：shadow-verse narrate 产线 + recipes 配方 + hooks 台账 + checks.py + craft.py

---

## 一、定位 / 技术栈 / 规模

- **定位一句话**：Claude Code 长篇网文连载插件——题材 Profile 字段化驱动「追读力」（钩子/爽点/微兑现/节奏红线）的 7 个 Skill 工作流 + 4 个 Agent，reviewer 逐维度只给证据不评分，配确定性 Python 工具链落库。
- **技术栈**：Claude Code 插件（Marketplace 分发）；Skills/Agents 是 markdown prompt 定义；`scripts/webnovel.py` 统一 Python 入口（preflight/state/index/commit）；数据层 SQLite（`index.db`）+ JSON（`state.json`）；RAG 可选（缺 `.env` 退回 BM25 关键词检索）；Dashboard 用 Vite 前端（预打包 dist）+ Python 只读 server。
- **规模**：7 Skill（init/plan/write/review/query/learn/dashboard）、4 Agent（context/reviewer/data/deconstruction）、9 题材 CSV + 13 内置题材 Profile、`scripts/data_modules/` 多模块（api_client/artifact_validator/memory/write_gates）。`references/` 分 csv/index/outlining/review/shared/taxonomy 层。GPL-3.0。

---

## 二、核心机制逐子系统剖析

### 2.1 题材 Profile 字段化 schema（`references/genre-profiles.md`）

这是本项目最有料的设计：把「不同题材该怎么写」从经验固化成**结构化配置参数**，供 Step1.5 / Context Agent / Checkers 读取调权重（**配置只调建议，不做硬裁决**）。每个 Profile 六组字段：

1. **hook_config**（钩子）：`preferred_types`（偏好钩型按优先级）/ `strength_baseline`（strong/medium/weak）/ `chapter_end_required`（章末钩偏好）/ `transition_allowance`（过渡章豁免上限）。
2. **coolpoint_config**（爽点）：`preferred_patterns` / `density_per_chapter`（high=2+/medium=1/low=0-1）/ `combo_interval`（连击爽点每 N 章）/ `milestone_interval`（阶段胜利每 N 章）。
3. **micropayoff_config**（微兑现）：`preferred_types` / `min_per_chapter` / `transition_min`（过渡章下限）。
4. **pacing_config**（节奏红线）：`stagnation_threshold`（连 N 章无推进=HARD-003）/ `strand_quest_max`（主线最大连续章）/ `strand_fire_gap_max`（感情线最大断档）/ `transition_max_consecutive`。
5. **override_config**（约束豁免）：`allowed_rationale_types` / `debt_multiplier`（债务倍率，短篇 zhihu-short=2.0 最严）/ `payback_window_default`（偿还窗口章数）。

**13 题材**实证参数对比（节选，体现字段如何刻画题材差异）：

| 题材 | 爽点密度 | 节奏停滞阈值 | 感情线断档上限 | 过渡章连续上限 | 债务倍率 |
|------|---------|------------|--------------|--------------|---------|
| 爽文系统 shuangwen | high | 3 | 15 | 2 | 1.0 |
| 修仙玄幻 xianxia | high | 4 | 12 | 3 | 0.9 |
| 言情甜宠 romance | medium | 4 | **5**（极低） | 2 | 1.0 |
| 悬疑推理 mystery | **low** | 3 | 20 | 2 | 0.8 |
| 规则怪谈 rules-mystery | medium | **2** | 15 | **1** | 1.2 |
| 知乎短篇 zhihu-short | high | **1** | 3 | **0** | **2.0** |

- **加载机制**：`state.json → project.genre` 定位 Profile；支持 `genre_overrides` 用户覆盖（如 xianxia 把 stagnation_threshold 改 5）；预留多标签叠加（冲突字段取更严值，如 `[romance,mystery]` 断档 = min(5,20)=5）。
- **状态**：标注「Fallback Only」——高频题材主判定/调性/禁忌已迁到 Story Contracts / CSV route seed，本文件仅在合同缺失时补充。

> **价值核心**：这正是 shadow-verse **recipes 字段化**的成熟参照——把「pacing/爽点/疲劳词/审校维度」从散文配方升级为可被 checks/审校读取的结构化阈值表，且每个阈值都有题材实证依据。

### 2.2 追读力钩型分类（`references/reading-power-taxonomy.md`）

统一的「追读力」分类标准，供 Step1.5/Context Agent/Checkers 共享（**指导性建议，不硬裁决**）：

- **5 种钩子类型**：危机钩 / 悬念钩 / 渴望钩（含 5 子型：成长/关系/复仇/真相/收获渴望）/ 情绪钩 / 选择钩。每型给：定义 + 触发场景 + 题材适配表 + 过渡章降级方案 + **软提示问句**（如「本章结尾读者会产生什么情绪？是否足以让他们想知道接下来怎么办？」）+ 常见误用 + 分题材示例。
- **章内 vs 章末分工**：章内用悬念钩/情绪钩（保持沉浸），章末用危机钩/选择钩/渴望钩（驱动点下一章）。
- **8 种爽点模式**：装逼打脸/扮猪吃虎/越级反杀/打脸权威/反派翻车/甜蜜超预期 + 扩展的**迪化误解**（主角随意行为→配角脑补升华→读者优越感，给核心结构 4 步）、**身份掉马**。
- **7 种微兑现类型**：信息/关系/能力/资源/认可/情绪/线索兑现，配题材偏好表 + 每章建议数量 + 过渡章降级。
- **结构提示 30/40/30**（铺垫/兑现/余波）软化版，强调「不作硬性要求」。

### 2.3 reviewer 职责边界（`agents/reviewer.md` + `references/review-schema.md`）

**这是用户点名要剖的「逐维只给证据」纪律**：

- **身份**：章节「事实审查员」，只查 5 维——**设定一致性 / 时间线 / 叙事连贯 / 角色一致性 / 逻辑**。
- **强制逐项结论**（`reviewer.md:67`）：5 维每维必出一行结论，无问题也显式输出 `pass`（写进 `dimension_results`），有问题输出「发现N个问题：简述」。
- **五条禁区**（`reviewer.md:75`）：
  1. **不评分**——不输出 overall_score、不 pass/fail；
  2. **不评价文笔**——「写得不够好」不是 issue，「与角色性格矛盾」才是；
  3. **不建议情节改动**——「这里该加个反转」不是 issue；
  4. **不重复大纲**——不在 issue 暴露未发生剧情；
  5. **只报可验证问题**——必须有 evidence（原文引用 or 数据对比）。
- **Issue schema**：`severity`(critical/high/medium/low) + `category`(5维) + `location` + `description` + `evidence` + `fix_hint` + `blocking`。`severity=critical` 自动 `blocking=true`；存在任何 blocking → 下一步（润色/提交）不得开始。
- **评分与裁决分离**：reviewer 只产原始 issue 清单（`review_results.json`，唯一事实源）；`review-pipeline` 再派生兼容用的 `overall_score`（由严重度推导，**仅供趋势观测，不替代 issue 清单**，gate 决策仍以 blocking 为准）。
- **错误降级**：读不到角色状态→跳设定检查并在 summary 标注；正文为空→单条 critical「正文为空」。

> **价值核心**：「逐维只给证据 / 无总分 / 评分与裁决分离 / blocking 是唯一闸门 / critical 限定确定的事实矛盾」——这套纪律可直接进 shadow-verse narrate_review，治「审校给笼统打分却无据可改」的病。

### 2.4 Blocking Override 分层裁决（`references/review/blocking-override-guidelines.md`）

override 不等于「问题不存在」而是「用户决定接受后果」，且 override 后仍保留原 issue 记录。分层：

- **禁止 override**：设定冲突 / 时间线冲突 / 事实错误（死人复活、已毁道具再现）/ 连续性断裂。
- **可考虑 override（需用户确认）**：节奏偏差 / 角色风格软偏差（学者说书面语合理）/ 可选结构节点未覆盖（必须节点已覆盖）。

配 7 种 `rationale_type` 枚举（taxonomy §4.3）：TRANSITIONAL_SETUP / LOGIC_INTEGRITY（减债）/ CHARACTER_CREDIBILITY（减债）/ WORLD_RULE_CONSTRAINT（减债）/ ARC_TIMING / GENRE_CONVENTION / EDITORIAL_INTENT（增债，配额更严）。每次违背 Soft Guidance 必须选一个理由并承担「债务」，有偿还窗口——这是一套**软约束的债务记账系统**。

### 2.5 三线织网（`references/shared/strand-weave-pattern.md`）

多线叙事节奏控制（**低自由度，必须执行**）：

- 三条线占比：**Quest 主线 55-65% / Fire 感情线 20-30% / Constellation 世界观线 10-20%**。
- 交织硬规则：Quest 不连续超 5 章 → 切 Fire/Constellation；Fire 不超 10 章不出现；Constellation 不超 15 章不出现。
- `state.json.strand_tracker` 追踪：`last_quest_chapter` / `last_fire_chapter` / `last_constellation_chapter` / `current_dominant` / `chapters_since_switch` / `history[]`。
- 给前 30 章织网模板 + 警告判断示例 + 开局前 10 章占比可调（Quest 70-80%）的 edge case。

### 2.6 工作流分工（7 Skill / 4 Agent）

- Skill：`/webnovel-init`（骨架/设定/总纲）→ `/plan`（拆卷纲/时间线/章纲）→ `/write`（一条龙：context→起草→review→润色→提交→备份）→ `/review`（多维审查落库）→ `/query`（只读查询）→ `/learn`（有效写法沉淀进长期记忆）→ `/dashboard`。
- Agent：`context-agent`（写前 research 出写作任务书）/ `reviewer`（逐维事实审查）/ `data-agent`（从正文提取事实生成 commit artifacts）/ `deconstruction-agent`（拆参考书提炼可迁移写法）。
- 写时安全：`hooks/guard_runtime_write.py` 守 runtime 写入；`path_guard.py` 防越界。

---

## 三、对 shadow-verse 的价值

| # | 借鉴点 | 对应能力 | 状态 | 移植方式 | 优先级 |
|---|--------|----------|------|----------|--------|
| 1 | **题材 Profile 字段化 schema**（hook/coolpoint/micropayoff/pacing/override 六组阈值） | recipes 配方升级为结构化阈值表 | 🔵仍可借（**重点**） | 仅思路（设计 shadow-verse 自己的字段 schema，吸收 13 题材阈值实证） | **高** |
| 2 | **reviewer 逐维只给证据不评分**（5 维 + 5 禁区 + 强制 pass + evidence 必填） | narrate_review 纪律 | 🔵仍可借（**重点**） | 直接移植（prompt 纪律文本） | **高** |
| 3 | **评分/裁决分离 + blocking 唯一闸门**（critical 限事实矛盾，分自动 blocking） | narrate_review verdict 语义 | 🔵仍可借 | 直接移植 | **高** |
| 4 | **追读力钩型分类**（5 钩型 + 软提示问句 + 章内/章末分工 + 过渡降级） | craft.py 钩子工艺（已有 13 式/7 式） | 🔵部分已吸收（craft.py 钩 13 式偏「手法」，本项目偏「类型+题材适配」可互补） | 仅思路 | 中 |
| 5 | **Soft 约束债务记账**（rationale_type 枚举 + debt_multiplier + payback_window） | recipes/审校的「可申诉但记账」机制 | ⚪以后可能用 | 仅思路 | 中 |
| 6 | **Blocking override 分层**（禁止/可议清单 + 需用户确认） | 人在环裁决纪律 | 🔵仍可借 | 直接移植 | 中 |
| 7 | **三线织网 strand_tracker**（Quest/Fire/Constellation 占比 + 断档红线 + 追踪器） | hooks.json 之外的「线平衡」台账 | 🔵仍可借 | 仅思路（与 hooks 状态机同构，可并入） | 中 |
| 8 | **微兑现概念**（每章「这章没白看」的小收获 7 类型 + 过渡章下限） | craft.py / recipes 爽点密度补充 | 🔵仍可借 | 仅思路 | 中 |
| 9 | **/learn 有效写法沉淀进长期记忆** | memory.py 写法库 | ⚪以后可能用 | 仅思路 | 低 |
| 10 | **题材 CSV 数据驱动**（9 CSV：人设/技法/命名/场景/桥段/爽点/裁决/金手指/题材推理） | recipes 题材知识库 | ⚪以后可能用 | 仅思路 | 低 |

**重点**（用户点名）：recipes 字段化（#1）、reviewer 逐维只给证据（#2）——这两项是本项目对 shadow-verse 最直接的价值。

---

## 四、不值得碰

- **Claude Code 插件框架本身**（marketplace/plugin.json/hooks.json）：shadow-verse 是独立引擎 + MCP，不做 CC 插件分发。
- **Vite/React Dashboard 前端**（`dashboard/frontend/`）：重型前端外壳，shadow-verse 有自己的 webapp。
- **SQLite index.db 落库层**：shadow-verse 走 JSON/文件 + memory.py，不引 SQL。
- **RAG/.env/BM25 检索栈**：shadow-verse 优先零依赖结构化反查（ainovel-cli 路线）。
- **完整 7 Skill 工作流编排**：与 shadow-verse narrate 产线是平行设计，借纪律不照搬流程。

---

## 五、存档备忘（以后可能用，单列）

1. **13 题材的阈值实证表**（genre-profiles.md §2）本身就是一份网文题材的「数值画像」语料，shadow-verse 设计 recipes 时可直接吃这些数字（stagnation_threshold / strand_fire_gap_max / debt_multiplier 等）当起点，省去自己估参。
2. **软提示问句**模式（每个钩型/爽点/微兑现都配 2-3 个自检问句）是把「工艺」转成「写前 checklist」的好范式，可注入 shadow-verse 写作包。
3. **迪化误解爽点 4 步结构**（随意行为→信息差→脑补升华→读者优越感）和**身份掉马 4 步**，是 craft.py 爽点模板可补的两式。
4. **HARD-001~004 硬约束定义**（可读性底线/承诺违背/节奏灾难/冲突真空）是「MUST_FIX 不可申诉」的最小硬约束集，可作 shadow-verse checks 硬线的参照。
5. **deconstruction-agent 拆参考书提炼可迁移写法**的思路，与 shadow-verse「读语料学写法」方向一致，prompt 可参考。
6. **多标签题材冲突取更严值**（min 规则）是题材叠加的简洁裁决法，预留扩展时可用。
