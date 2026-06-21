# 项目解析存档 · AI_NovelGenerator

> 存档日期 2026-06-18 ｜ 源码路径 `F:/Project/projects/Tavern/AI_NovelGenerator`
> 对照基准：shadow-verse 零依赖暗宇宙引擎（narrate 产线 + checks.py + recipes + hooks + craft.py + memory.py）

---

## 一、定位 / 技术栈 / 规模

- **定位一句话**：基于「雪花写作法」分层展开 + 章节蓝图六元数据 + 角色状态树 + 向量库长程一致性检索的 Python GUI 全流程长篇小说生成器（Step1 设定 → Step2 目录 → Step3 草稿 → Step4 定稿 → 可选一致性审校）。
- **技术栈**：Python 3.9+；GUI 用 customtkinter（`ui/` 14 个 tab）；LLM 用 langchain_openai + 自写多家适配器；向量库 Chroma（`vectorstore_utils.py`）；embedding 多家适配（OpenAI/Azure/Ollama/LM Studio/Gemini/SiliconFlow）。**重依赖**（langchain/chromadb/google-genai/customtkinter），非零依赖。
- **规模**：核心约 20 个 py 文件；`prompt_definitions.py` 23.5KB（中文）+ `prompt_definitions_en.py` 29.5KB（英文双语）；`novel_generator/` 8 模块（architecture/blueprint/chapter/finalization/knowledge/vectorstore_utils/common）；`ui/` 15 文件。README 五语言。原作者已停止维护（2026/03 称将重构）。

---

## 二、核心机制逐子系统剖析

### 2.1 雪花写作法五层种子（`prompt_definitions.py:160-309`）

设定生成是严格分层的「雪花」展开，每层 prompt 吃上一层产物：

1. **核心种子**（`core_seed_prompt:161`）：要求用**单句公式**概括故事本质——「当[主角]遭遇[核心事件]，必须[关键行动]，否则[灾难后果]；与此同时，[隐藏的更大危机]正在发酵」，25-100 字，必含显性冲突 + 潜在危机 + 人物驱动力 + 世界观矛盾。
2. **角色动力学**（`character_dynamics_prompt:180`）：吃 core_seed，设计 3-6 角色，每个含**核心驱动力三角**（表面追求/深层渴望/灵魂需求）+ **角色弧线五段**（初始→触发→认知失调→蜕变→最终）+ **关系冲突网**（价值观冲突/合作纽带/隐藏背叛）。
3. **世界构建矩阵**（`world_building_prompt:209`）：三维交织（物理/社会/隐喻），每维度至少 3 个「可与角色决策互动的动态元素」。
4. **情节架构三幕**（`plot_architecture_prompt:237`）：三幕（触发/对抗/解决），每阶段 3 个关键转折 + 伏笔回收方案，第三幕要求「嵌套转折至少三层认知颠覆」。
5. **章节蓝图**（`chapter_blueprint_prompt:267` + 分块版 `chunked_chapter_blueprint_prompt:311`）：吃 architecture，按「每 3-5 章一个悬念单元 + 认知过山车（连续 2 章紧张→1 章缓冲）」编排。分块版支持长篇切片生成（传 n→m 章范围 + 已有章节目录），避免一次性生成几百章导致空洞。

> **要点**：每层产物落 txt 文件（`Novel_architecture.txt` / `Novel_directory.txt`），用户可在 GUI 编辑后再进下一层——人在环可干预。

### 2.2 章节蓝图六元数据 + 解析器（`chapter_directory_parser.py`）

蓝图每章是固定六字段结构化卡片：

```
第N章 - [标题]
本章定位：[角色/事件/主题]      → chapter_role
核心作用：[推进/转折/揭示]      → chapter_purpose
悬念密度：[紧凑/渐进/爆发]      → suspense_level
伏笔操作：埋设(A)→强化(B)→回收  → foreshadowing
认知颠覆：★☆☆☆☆ (1-5级)        → plot_twist_level
本章简述：[一句话]              → chapter_summary
```

解析器 `parse_chapter_blueprint()` 用正则鲁棒解析（`chapter_directory_parser.py:94`）：
- **多别名容错**（`_FIELD_ALIASES:14`）：每字段中英文多别名（如 `认知颠覆|转折程度|cognitive_subversion|twist_level`），兼容 LLM 输出漂移。
- **行前缀剥离**（`_LINE_PREFIX_PATTERN:29`）：吃掉 markdown 标题符 `#`、引用 `>`、列表符、树形符 `├└│`、序号——LLM 输出常带这些装饰。
- **包裹标点剥离**（`_strip_wrapping_punctuation:48`）：循环剥 `[]【】《》「」""''`。
- 章号支持中英双正则（`第N章` / `chapter N`）。`get_chapter_info_from_blueprint(text, N)` 给定章号取卡片，找不到返回默认结构。

> **价值核心**：这是一套**确定性的「LLM 自由文本 → 结构化字段」抽取层**，容错设计很扎实（别名 + 前缀剥离 + 包裹剥离），是 shadow-verse 解析 review verdict/findings、解析蓝图卡片可直接借的工程模式。

### 2.3 章节多阶段生成 + 向量召回（`novel_generator/chapter.py`）

非首章的 `build_chapter_prompt()`（`chapter.py:285`）是整个项目最复杂的一段，流程：

1. 读取 architecture / blueprint / global_summary / character_state 四份基础文件。
2. 取当前章 + **下一章**蓝图卡片（写当前章时已知下一章走向，保证衔接，`chapter.py:334`）。
3. **当前章摘要**（`summarize_recent_chapters:42`）：取最近 3 章正文（限 4000 字，取尾部），喂 `summarize_recent_chapters_prompt`，要求「承继 70% + 创新 30%」「承继→发展→铺垫三段式」「冲突用 [!] 标记预警」。
4. **知识库检索三步**：
   - `knowledge_search_prompt` → LLM 生成 3-5 组检索关键词（实体+属性/事件+后果/地点+特征）；
   - 向量库逐组检索（`get_relevant_context_from_vector_store`），按关键词给 `[TECHNIQUE]/[SETTING]/[GENERAL]` 打标；
   - `knowledge_filter_prompt` → LLM 三级过滤（冲突检测删重复 40%+ / 价值评估 ❗ 标记 / 按「情节燃料/人物维度/世界碎片/叙事技法」重组）。
5. **时间距离防自我复读**（`apply_content_rules:176` / `apply_knowledge_rules:195`）：检测检索结果里的章号，按与当前章的距离施加规则——近 2-3 章 `[SKIP]` 跳过；3-5 章 `[MOD40%]` 要求改写 ≥40%；更远 `[OK]` 可引用核心。**这是 embedding RAG 之上叠的一层启发式去重规则**。
6. 最终塞进 `next_chapter_draft_prompt`（`prompt_definitions.py:541`），含「相似度 >40% 必重构 / 20-40% 替换 3 要素 / <20% 改表现形式」的内置防重复纪律。

首章走简化的 `first_chapter_draft_prompt`（`:493`），要求至少 2 个动态张力场景（对话/动作/心理/环境四类，各有具体工艺要求如「潜台词冲突」「短句加速+比喻减速」「非常规感官组合」）。

### 2.4 角色状态树（`prompt_definitions.py:379-488`）

角色状态是一棵**固定五分支 ASCII 树**，LLM 增量更新：

```
角色名：
├──物品: (道具/武器 + 描述)
├──能力: (技能1/技能2 + 描述)
├──状态: (身体状态 / 心理状态)
├──主要角色间关系网: (角色名 + 关系描述)
└──触发或加深的事件: (事件名 + 描述与影响)
```

- 初始 `create_character_state_prompt:379` 从 character_dynamics 生成。
- 更新 `update_character_state_prompt:430`：吃新章正文 + 旧状态，「在已有文档基础上增删，不改变原有结构」，淡出角色可删，新角色入「新出场角色」区。
- 还有 `Character_Import_Prompt:626`：从任意正文反推角色状态树（导入已有小说用）。

> **价值核心**：用一棵**人类可读、LLM 可增量维护的固定结构树**承载角色状态，比纯散文摘要更抗漂移、更易做一致性比对。

### 2.5 定稿 + 一致性审校

- `finalization.py:37` `finalize_chapter()`：定稿时三件事——`summary_prompt` 更新全书摘要（限 2000 字）、`update_character_state_prompt` 更新角色树、`update_vector_store` 把新章入库。**写文件用临时文件 + `os.replace` 原子替换**（`_write_text_atomic:23`），防写半截损坏。
- `consistency_checker.py`：独立可选审校。`CONSISTENCY_PROMPT` 吃 novel_setting + character_state + global_summary + **plot_arcs（未解决冲突台账）** + 最新章，让 LLM 列冲突/不一致，并检查 plot_arcs 里有没有被忽略需推进的点。无冲突返回「无明显冲突」。

### 2.6 embedding 适配器（`embedding_adapters.py`）

统一 `BaseEmbeddingAdapter`（`embed_documents` / `embed_query`），工厂 `create_embedding_adapter(interface_format, ...)` 分发 6 家：OpenAI / Azure / Ollama（裸 `/api/embeddings` POST）/ LM Studio / Gemini（google-genai SDK）/ SiliconFlow。每家自处理 base_url 规整（`ensure_openai_base_url_has_v1` 自动补 `/v1`）、超时 `(5, 60)`、失败返回空向量降级。

> **价值核心**：可插拔 embedding 的适配器模式 + base_url 容错，是 shadow-verse 若以后要做「零依赖向量记忆」时对接本地 Ollama embedding 的现成参照（但 shadow-verse 优先走零 embedding 的结构化反查，见 ainovel-cli 存档）。

---

## 三、对 shadow-verse 的价值

| # | 借鉴点 | 对应能力 | 状态 | 移植方式 | 优先级 |
|---|--------|----------|------|----------|--------|
| 1 | **章节蓝图六元数据卡片**（定位/作用/悬念密度/伏笔操作/认知颠覆/简述） | narrate_prep 取料 / recipes 蓝图字段 | 🔵仍可借 | 仅思路（字段并入 recipes / 蓝图 schema） | **高** |
| 2 | **蓝图解析器容错层**（多别名 + 前缀剥离 + 包裹剥离 + 中英双章号正则） | 解析 review verdict/findings、蓝图卡片的工程模式 | 🔵仍可借 | 直接移植（纯正则，零依赖） | 中 |
| 3 | **角色状态树固定五分支结构** | memory.py 角色状态承载（抗漂移、可增量、可比对） | 🔵仍可借 | 仅思路（结构 + 增量更新 prompt） | **高** |
| 4 | **下一章蓝图前瞻**（写当前章时注入下一章卡片保证衔接） | narrate_prep 上下文包 | 🔵仍可借 | 直接移植（思路简单） | 中 |
| 5 | **时间距离防自我复读规则**（近章 SKIP / 中距改写 40% / 远章可引用） | checks.py 跨章复读已覆盖检测；此为「写前防」 | 🔵仍可借 | 仅思路（注入写作包的纪律文本） | 中 |
| 6 | **当前章摘要承继 70%/创新 30% 三段式** | narrate_prep 短摘要生成 | ⚪以后可能用 | 仅思路 | 低 |
| 7 | **知识三级过滤**（冲突删重 / 价值标记 / 四类重组） | 若做 RAG 检索后处理 | ⚪以后可能用 | 仅思路 | 低 |
| 8 | **plot_arcs 未解决冲突台账 + 审校推进检查** | hooks.json α 悬念状态机已部分覆盖；可扩到「未解决冲突」通用台账 | 🔵仍可借 | 仅思路 | 中 |
| 9 | **雪花五层种子链**（核心种子单句公式 → 角色三角/弧线 → 世界三维 → 三幕 → 蓝图） | 设定生成产线（shadow-verse 锻造层可对照） | ⚪以后可能用 | 仅思路（prompt 工艺参考） | 低 |
| 10 | **原子写文件**（temp + os.replace） | 落章/落库防损坏 | 🔵仍可借 | 直接移植（标准库） | 低 |
| 11 | **可插拔 embedding 适配器 6 家 + base_url 容错** | 零依赖向量记忆对接本地 embedding | ⚪以后可能用 | 仅思路 | 低 |

**重点**（用户已点名仍可借）：章节蓝图六元数据（#1）、角色状态树（#3）——这两项是 AI_NovelGenerator 最值钱的、与 shadow-verse 结构化记忆/取料直接对应的设计。

---

## 四、不值得碰

- **整套 customtkinter GUI**（`ui/` 15 文件）：重型桌面外壳，与 shadow-verse CLI/MCP 路线相悖。
- **langchain + chromadb 向量栈**：重依赖，违背零依赖原则；shadow-verse 走结构化反查（ainovel-cli 路线）召回长篇，不引入 embedding 服务。
- **PyInstaller 打包 / main.spec**：桌面分发，无关。
- **英文/法文/日文/壮文多语 README 与 prompt_en**：双语 prompt 维护负担，shadow-verse 中文单线即可。
- 项目本身已停维护，不必跟踪其重构分支。

---

## 五、存档备忘（以后可能用，单列）

1. **雪花写作法的「单句故事公式」**模板（`core_seed_prompt:168`）写得极精炼，若 shadow-verse 锻造层要做「一句话核心冲突」可直接抄模板。
2. **四类场景工艺清单**（对话/动作/心理/环境，各带具体技法，`first_chapter_draft_prompt:512-531`）与 craft.py 工艺库可互补，特别是「非常规感官组合（听见阳光的重量）」「短句加速+比喻减速」这类具体手法。
3. **认知颠覆 1-5 级星标量化**（★☆☆☆☆）是给「转折强度」打可比数值的轻量做法，可用于 reflect 统计「全书转折强度曲线」。
4. **chunked 蓝图分块生成**（传 n→m + 已有目录）是长篇蓝图不空洞的思路，与 ainovel-cli 卷弧滚动规划属同类问题的两种解法，对照价值高。
5. 知识检索关键词三类型（实体+属性 / 事件+后果 / 地点+特征）是生成 RAG query 的实用 prompt 套路，若以后做检索可复用。
