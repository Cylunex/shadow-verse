# ShadowVerse · 酒馆/RP/小说生态借鉴路线图

> **用途**:`F:/Project/projects/Tavern` 下 20 个类酒馆/RP/小说项目的竞品借鉴分析,固化成可复查的路线图——借鉴时直接查本表,不必重读源码。
> **逐项目深度档案**:见 [`docs/competitor-archives/`](docs/competitor-archives/INDEX.md)(20 项目 + 2 ST JSON 各一份完整档案 + 总索引,标注 ✅已吸收/🔵仍可借/⚪以后可能用)。本文件是高层路线图,档案库是深度解析。
> **方法**:重型外壳(Next.js/Electron/Tauri/Android/monorepo)只读思路;埋在里面的**零依赖纯算法** + **打磨过的中文写作工艺文本**可直接吸收。守 shadow-verse 原则:零依赖、人在环、引擎不绑模型、单机本地。
> **首轮分析**:2026-06-18(5 路 Agent)。**深挖**:见文末「深挖规格」。

---

## A. 已落地(第一梯队 5 项,2026-06-18,20 套测试全绿)

| 模块 | 拿了什么 | 来源 |
|---|---|---|
| `sv/jsonloose.py` | LLM 脏 JSON 容错解析(去围栏/思考块/对象切片/补闭合符/中文标点兜底)。lenses/chat 落库统一走它 | InfiPlot `jsonParser.ts` 四级 + Novel-Auto-Generator `parserService.js` 修复管线 |
| `sv/checks.py` `check_book` | 全书纵向 stylestat:句式 tic 章均/跨≥3章逐字复读/章末同构/开篇时间词率/标题问题。接进 reflect;CLI `check-book` | ainovel-cli `internal/stylestat/stylestat.go` |
| `sv/craft.py` 工艺库 | 悬念钩13式 / 章首引子7式 / 扩充6技法 / 对话工艺 / 防注水四问 / 悬念曲线 / 三层弧 / play 权限分离+双段输出协议。注入写作包+play包+修订自检 | chinese-novelist-skill `references/guides/*` + interactive-novel `SKILL.md` |
| `sv/worldbook.py` | 世界书运行时触发引擎:matchKey(正则/全词/CJK) + selective(AND_ANY/ALL/NOT_ANY/NOT_ALL) + 常驻 + 递归lore + 字符预算 + order。导入卡世界书结构化存→激活注入 narrate/chat;CLI `worldbook` | ST `world-info.js`(matchKeys/selectiveLogic/scan) + Narratium `world-book.ts` |
| `sv/importer.py` 扩 | ST 预设导入(采样集+有序模块+`assemble_preset`组装器) + ST 正则导入(`apply_regex` 文本改写 $1/{{match}}/placement/depth)。CLI `import-preset`/`import-regex`/`presets` | 夏瑾.json(ST预设) + 正则1.json(ST正则) + Narratium `preset-assembler.ts` |

> 45 个 MCP 工具同步(+check_book/worldbook/import_preset/import_regex/presets)。

---

## B. 待借鉴清单(按 shadow-verse 子系统;含 file:line 与移植方式)

### 🟧 第二梯队(高价值,需设计)

| 拿什么 | 来源:行号 | 落到 shadow-verse | 优先级 | 移植 |
|---|---|---|---|---|
| **reflect 规则化诊断**:维度持续低分/钩子连续偏弱/爽点兑现率低/改写率过高 → Finding{规则,证据,建议,指向writer还是配方} | ainovel-cli `internal/diag/rules_quality.go:11-251` | reflect 聚合多章 review 后诊断 | 高 | 直接移植 |
| **审校逐维只给证据不评分** | webnovel-writer `agents/reviewer.md:13-141` | narrate_review 纪律 | 高 | 直接移植 |
| **向量记忆零依赖先行版——四维相关章节反查**(伏笔埋设章/角色最后出场章/状态变化章/关系变化章,纯台账零embedding) | ainovel-cli `internal/tools/novel_context.go:537-625` | 长篇相关章节召回,缓解向量记忆 backlog | 高 | 直接移植 |
| **StoryState 双区**(stable 故事圣经 + volatile 每幕patch:synopsis/openThreads/relationships/nextHook) | InfiPlot `lib/types/index.ts:239` + `best_practices.md` Pattern2 | thread 轻量长程记忆 | 高 | 直接移植 |
| **四层记忆**(热/温/冷/归档 + 每20轮修剪) | interactive-novel `SKILL.md` Stage5 | 对话/长篇记忆压缩降级 | 中 | 仅思路 |
| **recipes 字段化 schema**:hook_config/coolpoint_config/micropayoff_config/pacing_config(停滞阈值/主线最大连续章/感情线最大断档) | webnovel-writer `references/genre-profiles.md:18-86` | recipes 升级为可被 checker 读的参数 | 高 | 直接移植 |
| **追读力钩型分类法**(危机/悬念/渴望/情绪/选择钩,各带触发场景+题材适配+误用) | webnovel-writer `references/reading-power-taxonomy.md` | hooks 分型库 + 写作包 | 高 | 直接移植 |
| **章节蓝图六元数据**(定位/作用/悬念密度/伏笔三态埋设-强化-回收/认知颠覆★1-5/简述) | AI_NovelGenerator `prompt_definitions.py:267-358` | thread 大纲章目录字段 + hooks 状态机 | 高 | 直接移植 |
| **角色状态树**(物品/能力/状态身心/关系网/触发事件,树形+增量更新) | AI_NovelGenerator `prompt_definitions.py:379-488` | entity 状态模板 | 高 | 直接移植 |
| **一致性检查提示词**(传设定+角色状态+前文摘要+未解决冲突plot_arcs+本章) | AI_NovelGenerator `consistency_checker.py:6-23` | review + reflect(plot_arcs≈hooks台账) | 高 | 直接移植 |
| **角色动力学**(核心驱动三角:表面追求/深层渴望/灵魂需求 + 弧线五段) | AI_NovelGenerator `prompt_definitions.py:180-206` | recipes 角色弧光配方 | 中 | 直接移植 |
| **雪花核心种子单句公式**("当[主角]遇[事件]必须[行动]否则[后果]同时[隐藏危机]发酵") | AI_NovelGenerator `prompt_definitions.py:161-176` | forge 故事核 | 中 | 直接移植 |
| **txt小说→世界书**:章回正则切分→合并→二次切 + UnionFind 别名并查集去重 + 多编码(UTF8/GBK/Big5)检测 | Novel-Auto-Generator `services/fileImportService.js:89-241`/`mergeService.js:234-527`/`parserService.js` + Nika `chat.html:1117` | 世界融合/导入,**对接 Novel/知轩藏书 7815本语料** | 高 | 直接移植 |
| **PPR 图扩散**(实体共现图 Personalized PageRank α=0.15,种子记忆扩散到叙事相关但语义远的记忆 + cosine gate) | LittleWhiteBox `vector/retrieval/diffusion.js:39-69,439-581` | 向量记忆联想召回 + 跨thread因果 | 中 | 直接移植(~300行可整段翻) |
| **L0-L3 锚点记忆模型**(L0场景锚点含三元组s/t/r + L1chunk + L2event带causedBy因果 + L3fact) + 提取prompt | LittleWhiteBox `vector/llm/atom-extraction.js:43-95` | 向量记忆数据结构 + substrate | 中 | 直接移植(prompt+结构) |
| **混合召回管线**(Dense加权+Lexical BM25+W-RRF融合+MMR去冗+rerank+实体旁路,9阶段) | LittleWhiteBox `vector/retrieval/recall.js`(CONFIG:61-101 阈值表) | 向量记忆检索层蓝图 | 中 | 仅思路(参数表可抄) |
| **节点化 Workflow DAG**(LLMNode/WorldBookNode/RegexNode/PresetNode/MemoryNode 编排一次回复) | Narratium `lib/nodeflow/WorkflowEngine.ts:44` | narrate/play 产线=可插拔Node有向图 | 中 | 仅思路(Python函数管线复刻) |

### 🟨 第三梯队(单点功能 / 主要思路)

| 拿什么 | 来源:行号 | 落到 | 优先级 | 移植 |
|---|---|---|---|---|
| **`<pic prompt="">` 标签触发出图** + 三种插入模式(swipes) | st-image-auto-generation `index.js:66-77,378-496` | 文生图入对话 backlog | 高 | 直接移植(机制极简) |
| **LLM 场景出图规划器**(读世界书+人设+末楼→SD/NAI/Comfy tag) + TAG编写指南 | LittleWhiteBox `modules/draw/shared/scene-planner.js:6-35` | render 透镜 prompt 构建 | 中 | prompt模板可移植 |
| **群聊自然顺序发言人**(@提名→talkativeness掷骰→禁连说→兜底) | Luker `group-chats.js:1422-1497` | play/simulate 多角色 | 中 | 直接移植(纯算法) |
| **Scene/Beat 分支图模型**(Beat.next=continue/choice, effect=advance-beat/change-scene) | InfiPlot `lib/types/index.ts:7,66,112` | 线分支 backlog + 时间线 | 中 | 直接移植(dataclass) |
| **本地Agent↔网页 SSE+MCP桥 + Origin锁定**(Agent发tool_call→网页执行→回result,30s超时+requestId配对) | infinite-canvas `canvas-agent/src/canvas-session.ts:152` | MCP 驱动控制台/时间线 | 中 | 直接移植(纯stdlib) |
| **三层作用域 shadow 缓存**(global<preset<character 后层覆盖→getVisible合并) | Luker `src/skills/memory-index.js:12` | codex/world/entity 可见性组装 | 中 | 直接移植(纯函数) |
| **role YAML 字段**(speakingStyle/behaviorRules/relationship数值化intimacy/trust) | Noema `role/eva.yaml` | entity 定义字段 + 呼应 Doll | 中 | 直接移植(格式) |
| **parseJsonLoose 四级**(已部分吸收进 jsonloose,可对照补 jsonrepair 级) | InfiPlot `lib/engine/jsonParser.ts` | jsonloose 健壮性 | 低 | 已大部分done |
| **五职能 Agent 两阶段重叠编排**(Architect→Writer PhaseA/B→CharacterDesigner∥Cinematographer→Painter) | InfiPlot `lib/engine/director.ts:36` | lenses Agent 编排范式 | 中 | 仅思路 |
| **prompt-cache 友好 stable-prefix**(固定前缀world/style/spine/history+动态后缀) | InfiPlot `best_practices.md` Pattern4 | LLM 成本优化 | 低 | 仅思路 |

### ⬛ 不值得碰
所有重型外壳:Next.js App Router、Electron monorepo、Tauri 桥接、Android C++/QNN/MNN 推理栈、各家云 embedding/TTS 适配器、IndexedDB/SQLite 数据层、各项目自带 Agent 框架(shadow-verse 自己就是引擎)、React Flow/AntD 全家桶。
embedding 务必保持可插拔/本地:LittleWhiteBox 绑了在线 SiliconFlow、AI_NovelGenerator 绑 langchain+chromadb——借召回算法但别照抄绑定。

---

## C. 18 个项目逐个档案

| 项目 | 定位 | 技术栈 | 借鉴价值 | 主要可借鉴点 |
|---|---|---|---|---|
| **Luker** | SillyTavern 生产化 fork | Node+浏览器ESM | ⭐⭐⭐ 算法金矿 | world-info.js(WI全套算法)、group-chats.js(发言人选择)、macros/engine、regex三层作用域、memory-index 分层缓存、char-data.js(WI字段schema) |
| **TauriTavern** | ST 套进 Tauri,Rust 重写服务端 | Rust+Tauri | ⭐⭐ 分层范式 | native_regex_service(LRU缓存)、lorebook_codec、agent_tools/world_info(index+content两段式带预算)、prompt_caching_plan |
| **AI-Chat (Narratium)** | ST 现代化重写(已停更) | Next.js+IndexedDB | ⭐⭐⭐ 完整设计 | world-book.ts(精简WI 60行)、preset-assembler.ts(有序段落装配)、nodeflow DAG、regex-processor、对话树、插件manifest |
| **LittleWhiteBox** | ST 巨型扩展 | 浏览器JS+jieba-wasm | ⭐⭐⭐ 向量记忆金矿 | vector(L0-L3锚点+PPR扩散+混合召回)、draw scene-planner、变量系统、STScript参考 |
| **Novel-Auto-Generator** | ST扩展:AI续写+txt转世界书 | 浏览器JS+IndexedDB | ⭐⭐⭐ 导入对口 | fileImportService(章节分块)、parserService(JSON容错)、mergeService(UnionFind别名合并)、双向格式+5合并策略 |
| **NikaForge** | 可视化AI游戏卡IDE | Bun/TS | ⭐ 仅资料 | stscript-reference.md(664行手册)、git冷备份思路 |
| **st-image-auto-generation** | 极简ST出图扩展 | 单文件JS | ⭐⭐ 最小范本 | `<pic prompt>`标签触发出图、三种插入模式、prompt注入解耦 |
| **AI_NovelGenerator** | Python GUI 小说生成器 | customtkinter+langchain+chroma | ⭐⭐⭐ 提示词库 | 章节蓝图六元数据、角色状态树、一致性提示词、角色动力学、雪花种子、摘要更新、embedding适配器基类 |
| **webnovel-writer** | Claude Code 长篇连载插件 | skill+python hooks+React | ⭐⭐⭐ 配方schema | genre-profiles字段化、reading-power-taxonomy钩型分类、reviewer逐维只给证据、伏笔台账三态 |
| **ainovel-cli** | Go 全自动长篇引擎 | Go+agentcore | ⭐⭐⭐ 算法金矿 | stylestat(已吸收)、diag规则诊断、四维相关章节反查、rules.md两层规则、卷弧双层滚动规划、配角名册RecentActive |
| **chinese-novelist-skill** | Claude中文写作工艺skill | 纯markdown | ⭐⭐⭐ 已吸收 | hook13式/引子7式/扩充6技法/对话/情节模板/防注水(已进 craft.py) |
| **interactive-novel** | 互动小说参与引擎 skill | 纯markdown | ⭐⭐⭐ play对口 | 权限分离(已吸收)、双段输出+状态行、YAML状态块增量更新、蝴蝶效应分支、四层记忆 |
| **Nika-Character-Studio** | 纯前端编卡器+mini酒馆 | 原生HTML/JS+IndexedDB | ⭐⭐⭐ UI同构 | 单文件SPA扮演/编卡页、`<state>`变量卡、swipe雏形、备选开场白、楼层、小说→世界书流水线、PNG卡读写 |
| **infiplot** | AI实时生成互动galgame | Next.js16/React19 | ⭐⭐ 编排标杆 | Scene/Beat分支图、StoryState双区、五职能Agent编排、parseJsonLoose、stable-prefix缓存 |
| **infinite-canvas** | 无限画布图片工作台 | Next.js+Zustand+AntD | ⭐⭐ 取canvas-agent | canvas-agent(SSE+MCP桥+Origin锁定)、画布工具schema(归一到批量op数组) |
| **Noema** | 桌面AI陪伴(JARVIS雏形) | Electron monorepo | ⭐ 取片段 | role YAML字段、plugin.json hook分类、sticker-expression情绪贴图(对立绘表情切换) |
| **local-dream** | Android端侧Stable Diffusion | Kotlin+C++ QNN/MNN | ⭐ 仅思路 | 本地可插拔出图后端、prompt tag自动补全、参数可复现ParamShare |
| **【6.12】正则1.json** | ST正则脚本 | JSON | ⭐⭐ 已支持导入 | 消息渲染→41KB HTML状态面板(HUD注入,渲染待前端沙箱) |
| **夏瑾 Beta 0.40.json** | ST预设 | JSON | ⭐⭐ 已支持导入 | 140条prompt+采样参数+injection编排(已 import-preset) |
| **JS-Slash-Runner** | 酒馆里iframe执行前端JS(Tavern-Helper) | Vue3+Vite+TS 2.4万行 | ⭐⭐ HUD对照 | iframe高度自适应57行(vh重写/ResizeObserver兜图片/rAF合批);**同源贯通路线与shadow-verse隔离沙箱相反,安全模型不可学**(详见G.1) |
| **MimirLink** | QQ/OneBot的ST卡运行时(重依赖) | Node+sqlite+express+ws | ⭐⭐ 同源异构 | 结构化消息头+意图路由(纯函数可移植)、trusted/untrusted信封、外部文件安全三件套、来源追踪;IM接入留作未来独立适配器(详见G.2) |

---

## D. 两个明确缺口
1. **立绘表情切换(同角色锁脸换喜怒哀乐)**——18 项目里只有 Noema sticker-expression 沾边,无直接现成实现,需自研(seed锁脸 + 情绪分类 + portraits/<emotion>)。深挖中。
2. **正则注入的 HTML 状态面板渲染**——`apply_regex` 已做文本改写,富 HTML 面板需前端沙箱化(iframe/白名单)。深挖中。

---

## E. 深挖规格(2026-06-18 第二轮,聚焦强化酒馆/RP)

> 4 路深挖 Agent 产出。1 已回填,2/3/4 进行中。

### E.1 高级世界书引擎(升级 `sv/worldbook.py`)

**判定**:现有 `scan()` 是 Narratium 级精简版,已实现 ST 算法**最难的那半**(matchKey 正则/全词/CJK、selectiveLogic 四态、递归回灌、order、字符预算)。缺的全是**「楼层/位置/状态」维度**——把"一次无状态文本匹配"升级成"跨楼层有记忆的注入状态机"。这是「酒馆体验」与「世界书查找器」的分水岭。源:Luker `world-info.js`(主循环8788-9629/Buffer954-1316/TimedEffects1318-1620/inclusionGroup9735-9822) + char-data.js(字段schema)。

**最该先补的 5 个(临界质变,按 ROI×沉浸感)**:
1. **timed effects (sticky/cooldown/delay)** ⭐最高 —— 无状态→有记忆的关键。sticky 让新登场角色设定粘附数楼不闪退;cooldown 防同一彩蛋反复触发;delay 让后期设定到第N楼才解锁。需持久化 `worlds/<w>/chats/<id>/wi_state.json`(effect={hash,start楼号,end楼号,protected})。精髓:sticky 到期立即挂 cooldown(on_ended回调);delay 不持久化按 floor_count 现算;sticky>cooldown 优先级。源 1318-1620。
2. **position + @D 深度注入 + role** ⭐ —— entry 加 `position`(0 before_char/1 after_char/2 an_top/3 an_bottom/4 at_depth/5 em_top/6 em_bottom)+`depth`+`role`(system/user/assistant)。`scan()` 返回从单 `injection` 改为 **buckets 分桶**,由 chat.py/lenses.py 决定塞哪;@D 注入到 `messages[-depth]` 前。源 9531-9602。
3. **scan_state 单循环状态机**(INITIAL→RECURSION→MIN_ACTIVATIONS→NONE)+ **Buffer 重构为分楼数组** —— 现在 `for range(max_recursion)` + buffer 拼成一坨是最大结构债。改成 `depth_buffer: list[str]`(倒序分楼,[0]=最新),行首 `\x01` 哨兵防跨楼误匹配(对中文短语键尤重要)。是 1/2 的承载地基。源 185-202/8930-9481/1050。
4. **inclusion group 互斥组** ⭐ —— entry 加 `group`/`group_weight`/`group_override`/`use_group_scoring`。同组只激活一条(sticky护体→cooldown剔除→scoring取命中键最高→已激活组清场→groupOverride→加权随机)。"同槽位(今日天气/NPC心情)只激活一条"避免设定打架。源 9735-9822。
5. **probability 概率触发** —— entry 加 `probability:int=100`/`use_probability`。命中后 roll;sticky 跳过。低成本给世界注入随机彩蛋。源 9285-9320。

**升级 entry schema 新增字段**:uid/source/book_layer + scan_depth + probability/use_probability + position/depth/role + group/group_weight/group_override/use_group_scoring + sticky/cooldown/delay + prevent_recursion/exclude_recursion/delay_until_recursion + ignore_budget。

**落地顺序**:① Buffer 改分楼数组 → ② scan_state 单循环 → ③ position 分桶输出(chat.py:149/lenses.py 消费点同步改契约,留 `flatten=True` 兼容参数过渡) → ④ timed effects(+wi_state.json+dry_run) → ⑤ group+probability → ⑥ 多书合并/递归细节按需。

**不抄**:token预算/tokenizer(中文字符预算更确定)、vectorized、automation_id、outlet、characterFilter、decorators、6个匹配源(只扫聊天楼层即可)。**whole_word 可对齐 ST 细节**:多词键(含空格)直接子串、单词才走 `\W` 边界。

### E.2 变量系统 + 状态HUD面板(升级 `sv/chat.py`+`web/index.html`,新 `varstate.py`/`macros.py`)

**判定**:生态里最成熟的是 LittleWhiteBox State 2.0(带 schema/规则/校验/回滚的完整状态引擎),HUD 渲染**全靠前端 iframe 沙箱**——`importer.py` 注释("HTML 渲染由前端沙箱负责")方向已对,缺的就是前端那一层。**最小可玩闭环 = ①+②+③**。零依赖红线:State 2.0 依赖 js-yaml,**shadow-verse 不跟进**,`<state>` 块换成现有 JSON+jsonloose,只搬规则/路径算法。

**① vars.json 三段式 P0**:`{data:嵌套对象/数组/标量, rules:{min/max/step/ro/enum}, meta:{label/vis/color/persist}}`。`_apply_one` 从 `+N/-N/set` 扩成五 op(set/inc/push/pop/del);路径深取支持 `关系.张三.好感`。`vis:hidden` 参与结算但不进 HUD(治"内心真实好感 vs 表面态度")。新 `sv/varstate.py`(移植 LittleWhiteBox `core/variable-path.js:18-325` + `state2/guard.js` 成 ~150 行 Python)。

**② validate 结算护栏 P0**:每个 op 落库前过 `validate`:越界 clamp、`step` 限幅(模型想 `+9999` 被砍到 step)、`ro` 拒写、未声明字段拒增——**让模型物理上写不坏变量**。收集 notes 回前端 toast。源 `state2/guard.js:116-247`(直接移植)。

**③ HUD sandbox iframe 渲染 P0(核心难点,在前端做)**:`web/index.html:469` 的 `bubbleHtml` 现在 `esc()` 全转义→面板根本不渲染。**必须用 `sandbox="allow-scripts"` 的 iframe + `srcdoc`,绝不加 `allow-same-origin`**(两者同给=没沙箱;不给则 opaque origin,拿不到主页 cookie/DOM,XSS 关盒里)。也不给 top-navigation/popups/forms。只渲染 char 气泡里的 ```html``` 块(`apply_regex` 产物),user 输入永远 `esc()`。**主题色要主动拼进 srcdoc 的 `:root`**(跨 origin 继承不了外层 CSS 变量)。iframe 内 `ResizeObserver`+`postMessage` 回报高度,宿主校验 `_svh` 是数字。源 LittleWhiteBox `iframe-renderer.js:402-461/216-246/321-400`(777行,精简成 ~40 行 srcdoc+高度监听)。chat.py 不动,只保证输出含 ```html``` 块。

**④ AI 自动建变量卡 P1**:从 profile+genre+开场让模型识别该追踪哪些状态并初始化(≤8个,数值给min/max,内心标hidden,关系用嵌套),输出 JSON→jsonloose→clamp→落 vars.json。web 扮演页「🎲 AI建卡」按钮 + `/chat/init_vars` 路由。源 Nika `part2.js:4352-4401`(prompt 范式,仅思路)。

**⑤ 解析/隐藏分离 P1**:先在 `_generate` 解析变量块(移植 `parser.js:92` extractStateBlocks 配对扫描,~30行,比正则稳),**再**对剩余 prose 套 `apply_regex`。chat.jsonl 存**原始 raw**(含 state),展示才套正则,回滚/重生成不丢数据。

**⑥ 精简 getvar/roll 宏 P2**:新 `sv/macros.py` ~30行正则替换,**只做只读宏**:`{{getvar::路径}}`/`{{roll::3d6}}`(RP检定刚需)/`{{random::a,b,c}}`/`{{if::..::..::..}}`。**不做 setvar 写宏**(绕过 guard 校验)。在 `_system` 注入变量 + HUD 包壳前各跑一次。源 `var-commands.js:120-153`(极简正则范式)。

### E.3 群聊 + swipe + 楼层/分支树(升级 `sv/chat.py` + 新 `sv/group.py`)

**ROI 排序**:swipe ⭐ → 群聊 ⭐ → 楼层编辑/删/任意楼重生成 → 自动总结 → 分支树(最后)。源:Luker `group-chats.js`(发言人) + `script.js`(swipe) + `bookmarks.js`(分支) + Narratium `character-dialogue-operation.ts`(树) + Nika `chat.html`。**关键决策**:swipe 和"从某楼重生成"用同一套数据结构同时拿下,是最高 ROI 第一刀。

**① swipe(一楼多候选)⭐ 高**:char 楼升级为 `{swipes:[文本...], swipe_id, swipe_meta:[{ts,updates}], vars_before}`,读取时 `text=swipes[swipe_id]`(保留派生 text 字段让现有代码零改;history() lazy 升级旧行)。函数 `swipe_add`(重生成追加新候选,**抄 Luker append 模型,别抄 Nika 截断重发**)/`swipe_select`/`swipe_next`。**变量回滚枢纽**:每候选存声明的 `updates`,楼级存 `vars_before` 基线;切候选=`vars=apply(vars_before, swipe_meta[i].updates)`,从基线重放不需逆运算,左右横跳变量恒一致。源 Luker `script.js:10461-10506`。

**② 群聊(多角色同场)⭐ 高**:新 `UNIVERSE/groups/<gid>/`(group.json{members,strategy,talkativeness,allow_self,greetings} + chat.jsonl(char楼带speaker) + 群级vars.json共享 + summary.jsonl)。发言人算法 `activate_natural_order`(@提名→talkativeness掷骰→禁连说banned→话痨池兜底,**纯算法直翻 Python**,源 `group-chats.js:1422-1497`;另 LIST/POOLED 可选)。串行循环逐角色 `_generate`+append(下个角色看得到上个刚说的)。各角色私有记忆走各自 entity.dir,世界书/群级vars共享。开场白随机选 alternateGreetings。

**③ 楼层管理 高/中**:`floor_edit`/`floor_delete`/`floor_regenerate`(截断 idx 后重生成=把现有 regenerate 推广到任意楼,**解决"只能重生成最后一条"**)+ 软书签(楼加 `mark` 字段,零额外文件)。源 Nika `chat.html:9905` + Luker 截断。

**④ 自动总结 中**:`summary_every`(未总结楼数阈值)触发→llm 总结→**落进现有 memory 系统**(kind:summary + 楼区间),retrieve 自动召回;已总结楼只留最近 HISTORY_WINDOW。源 Nika `chat.html:13182` + InfiPlot 滚动 synopsis。Nika token 估算器(中文1.5字/token)可选直翻做"按token触发"。

**⑤ 分支树 低(=backlog线分支)**:**先上 Luker 轻做法**(branch=复制截断的 jsonl + 定格选定swipe + branches/index.json),切支=改"当前活动 chat 文件指针"。原生 SVG 画浅树(分层布局自写20行坐标,rect+text节点/path边,当前路径染红),**别上 React-Flow**。源 Luker `bookmarks.js:227` + Narratium `DialogueTreeModal.tsx`。

> **枢纽设计**:`swipe_meta[i].updates` + 楼级 `vars_before` 同时支撑「swipe变量回滚」「分支定格swipe」「总结读每楼状态变化」三件事,一次设计到位。

### E.4 立绘表情切换 + 预设接进组装 + 角色卡补字段(`lenses.py`/`importer.py`,新 `expressions.py`/`promptkit.py`)

#### A. 立绘表情切换(真缺口已破解)
**机制**:预生成一组带标签 sprite → 回复后分类情绪 → 前端按 label 换图(ST 成熟做法)。源 Luker `expressions/index.js`。
- **A1 情绪标签集 P0**:核心8(`neutral/joy/anger/sadness/surprise/fear/embarrassment/love`)+扩展。新 `sv/expressions.py`。源 `index.js:44-73`(直接移植 GoEmotions 28 标签)。
- **A2 锁脸预生成 P0**:`_gen_image` **加 seed 入参**(现在不带 seed,是锁脸第一个洞);同实体所有表情用同一 `appearance_seed`;prompt=`{appearance}, {emotion_clause}, same character, consistent face, upper body`。新 `render_expressions()` → `portraits/<emotion>.png`(**文件名=情绪标签**,对齐 ST `/sprites/<char>/<label>.png`)。z-image 若不认 seed,退路:appearance 写更身份化 + `(same person:1.2)`。源 `lenses.py:358-404` 改造。
- **A3 情绪分类 P0**:轻量 LLM 单调用,**只在已生成 label 集里选**(别选没图的),只取文本尾部样本省 token,JSON 三级回退(jsonloose 可吃脏 JSON)。接入 `play_commit` 落 session 时给每段回复标 `<!--emotion:joy-->`。源 `index.js:906/955/1075`(直接移植)。
- **A4 前端切换 P1**:数据档(返回 `current_sprite` + transcript 内嵌情绪标记,任何渲染端按标记取图);HTML 档(固定 `<img>` 换 src + 淡入淡出)。源 `index.js:206-259`。
- CLI:`expr-gen <eid>` / `expr-classify <text>`。

#### B. 预设接进统一提示词组装(替换 narrate 手拼 sys/user)
**现状**:`assemble_preset` 只按序拼串,**没接进** `narrate_generate`(手写)。实证夏瑾预设:140 prompt/启用32/position全0(relative)/role以user为主(127/140)。
- **B1 marker 槽映射 P0**:ST marker→引擎数据(charDescription←实体身份、worldInfoBefore←`worldbook.scan().injection`、scenario←thread.md、dialogueExamples←mes_example、chatHistory←last_chapter_tail、personaDescription←player persona)。源 Narratium `preset-assembler.ts:18-33`。
- **B2 统一组装器 P0**:扩 `assemble_preset` 为**分 role**(尊重 role 字段别全塞 system)+ 收集 depth → 返回 `{system, user, depth_msgs}`;无 preset 时 fallback 引擎默认骨架(**不回退能力**)。新 `sv/promptkit.py` 或扩 importer。
- **B3 depth 注入 P1**:`injection_position=1` 项插到对话倒数第 depth 条前(author's note/depth prompt 载体)。`apply_depth(history, depth_msgs)`。narrate 单轮可简化拼 user 末尾;chat/play 多轮需加 `llm.chat(messages)`。源 Luker `PromptManager.js:1694`。
- **B4 接 narrate_generate P0**:thread.meta 加 `preset` 字段;构 slots→assemble→`sys=bundle.system or 现有手写`。**关键边界:预设管人格/越狱/语气,引擎仍掌产物结构契约**(章标题/`===沉淀===`JSON/字数/节奏),拼接时结构契约后置(优先级高)。源 `lenses.py:79-103`。

#### C. 角色卡补字段(`parse_card` 已取 post_history_instructions,缺 extensions/V3)
源 Luker `char-data.js:54-85`(直接移植字段读取):
- **C2 两个高价值联动**:① `extensions.sd_character_prompt.positive` → **直接作 appearance**(很多卡自带 SD 正向词,正是锁脸素材,import_card 时 set_appearance,A2 零额外输入出表情)P1；② `extensions.depth_prompt{prompt,depth,role}` → **B3 depth 注入**(角色私货持续注入,RP 体验关键,与 B 同批)P0。
- 其余:`creator_notes`(profile 留档不进提示词)、`regex_scripts`(复用 import_regex 导卡内嵌正则)P1、V3 `assets` type:emotion(现成 sprite 直接落 portraits/)P1、`talkativeness`(群聊发言倾向)、`group_only_greetings`、`character_version` 等 P2/P3。

#### 落地批次(强化 RP 主线)
- **批次1**:A1+A2+A3(表情集+锁脸+classify) + C2(sd_prompt→appearance、depth_prompt 取字段)。最快见效,补公认缺口。
- **批次2**:B2+B4(assemble 分role+接narrate) + C1 depth_prompt 接 B3。
- **批次3**:A4 HTML切换、B3 完整 llm.chat 多轮、C 其余字段。

---

## F. 强化酒馆 — 跨深挖的「建议先做」总排序

> **2026-06-18:第 1–6 刀全部完成,强化酒馆收官。** 26 套测试全绿、50 个 MCP 工具、32 个引擎模块。

| 批次 | 做什么 | 状态 |
|---|---|---|
| **第1刀** | swipe(一楼多候选)+任意楼重生成+变量可回滚 —— chat.py swipe_add/select/next/floor_regenerate;◀i/n▶ | ✅ test_swipe 19✓ |
| **第2刀** | 变量三段式(data/rules/meta)+validate护栏(clamp/step/ro/enum)+HUD sandbox iframe(allow-scripts 不 same-origin)+可见性面板 | ✅ 新 varstate.py;test_varstate 22✓ |
| **第3刀** | 立绘表情切换(_gen_image+seed 锁脸+render_expressions 预生成 portraits/<emotion>.png+classify 情绪)+sd_character_prompt→appearance+depth_prompt/talkativeness 取卡 | ✅ 新 expressions.py;test_expressions 15✓ |
| **第4刀** | 群聊(多角色同场+activate_natural_order @提名/talkativeness/禁连说/兜底+群级vars+群聊页) | ✅ 新 group.py;test_group 10✓ |
| **第5刀** | 世界书 timed effects(sticky/cooldown/delay 按楼号+wi_state.json)+position@D分桶+probability+inclusion group | ✅ worldbook.py 升级;test_worldbook2 14✓ |
| **第6刀** | 内联宏(getvar/roll/random/if 只读)+预设组装器(role分离+@D注入)+depth_prompt 注入_system+AI建变量卡(🎲) | ✅ 新 macros.py/promptkit.py;test_promptkit 21✓ |
| 后续(未做) | 对话分支树(SVG)、自动总结落记忆、楼层编辑/删 UI、preset 接进 narrate 组装替换手写、HUD 主题色微调 | 按需 |

> 零依赖红线(全程守):不引入 js-yaml/tokenizer/向量库/React;HUD 沙箱 `allow-scripts` 但**绝不 `allow-same-origin`**;embedding 接口保持可插拔本地。

---

## G. 追加项目档案(2026-06-18 第三轮 · 即使现在用不上也存档)

### G.1 JS-Slash-Runner(Tavern-Helper)—— 酒馆里用 iframe 执行前端 JS 的事实标准

**定位**:SillyTavern UI 扩展,把 AI 输出的 ```html```/```js``` 块通过 iframe 在酒馆里跑起来,并向 iframe 暴露 ~200 个酒馆操控 API。**技术栈**:Vue3+Pinia+Vite+TS+Tailwind,src ~2.4 万行,`@types/` 30+ 份 .d.ts(给脚本作者的 API 类型契约)。

**核心认知:它和 shadow-verse HUD 是两条对立路线,不是同一件事的两个版本**:
- shadow-verse HUD =「隔离优先」:`sandbox="allow-scripts"` 刻意**不给** `allow-same-origin`,iframe 是无 origin 孤岛,只能 postMessage 跟宿主对话。**因为模型输出=不可信输入,必须隔离。**
- JS-Slash-Runner =「贯通优先」:iframe **完全不设 sandbox**、与酒馆同源,脚本直接 `window.parent.TavernHelper.xxx()`。安全靠 README 红字 + 用户自审。**因为它要脚本能操控酒馆一切(triggerSlash)。**
- **结论:它的安全模型 shadow-verse 不能学**(场景相反);值得拿的只有它 57 行高度自适应里的工程经验。

**它比精简 HUD 多踩平的 3 个坑(已采纳为 P0,见下方"已应用")**:
1. **`100vh` 塌陷**:iframe 内 `100vh` 指 iframe 自己的视口(自适应后≈内容高),不是屏幕高,会塌成内容高/反复跳。对策:注入前正则把 `Nvh`→`calc(var(--sv-vh)*N)`,`--sv-vh` 由宿主把真实视口高拼进 :root。源 `src/panel/render/iframe.ts:5-75`。
2. **图片异步加载高度跳变**:不监听 img.onload 时,图片加载完高度不更新。对策:ResizeObserver 持久 observe(body) 兜住 + img.onload 双保险。源 `src/iframe/adjust_iframe_height.js:47-50`。
3. **内容狂变消息刷爆**:每次 ResizeObserver 回调都 postMessage 会刷爆。对策:rAF 合批 + scheduled 防重入标志。源 `adjust_iframe_height.js:28-39`。
- 另:`*{box-sizing:border-box}` + `html,body{overflow:hidden}` 注入级 reset(量 scrollHeight 不被滚动条干扰);错误可见化(iframe 内 window.onerror→回报宿主)。

**存档(以后可能用)**:blob URL 调试模式(srcdoc 没法在 DevTools 打断点;blob origin 也是 null,与隔离目标一致,配 `<base href>` 锚相对路径,源 `iframe.ts:86`);声明式 store 管理多 iframe + reload_memo(uuid key)强制重建(`store/iframe_runtimes/message.ts`);流式渲染(边生成边渲染 iframe,`Streaming.vue`);变量管理面板/Prompt查看器/调试器/宏注册/楼层按钮。**不适用**:同源 API 体系(200函数/triggerSlash/this-binding 身份)、Vue/Pinia 全家桶、jQuery/lodash 全局、CDN 注入第三方库。

### G.2 MimirLink —— QQ/OneBot 场景的 ST 卡运行时(重依赖)

**定位**:把 ST 角色卡运行时**服务端化**并嫁接到 QQ/OneBot IM 的 Node.js 守护进程。与 shadow-verse 同源异构(都做"ST卡运行时+记忆+变量+预设+MCP"),但**透镜押在 IM 多人群聊**、且**重依赖**(better-sqlite3/express/ws/@modelcontextprotocol/sdk),与零依赖冲突。`routes.js` 337K 行 + `index.js` 150K 行是工程反面教材(单文件巨石)。

**引擎核心比 shadow-verse 更弱**:记忆=纯 SQLite 关键词加权召回(无向量,理念同 memory.py,但摘要靠 LLM 非确定);变量=**扁平 key-value,无 rules/meta 分层**,结算靠 LLM 在 `<UpdateVariable>` 里自己算 JSONPatch("AI 算账");明确放弃脚本运行时。**shadow-verse 的 rules 结算引擎(变量三段式)反而更强,别倒退。**

**真正稀缺、值得吸收的(面向真人多说话人 IM)**:
| # | 借鉴点 | 对应 shadow-verse | 优先级 | 移植 |
|---|---|---|---|---|
| 1 | **结构化消息头** `[群聊\|QQ:123\|昵称:张三\|isAtBot:true\|...] 内容`——用一行文本携带说话人身份/路由元数据,让单 LLM 在线性历史里分辨"谁在说/对谁说/是否@我" | 群聊 + 用户身份 | 高 | 仅思路(格式直接抄) |
| 2 | **current-message-focus 意图路由层**(意图分类 poke/reply/call_out/topic_shift + 回复目标决策 + 策略提示+warnings) | 护栏+群聊 | 高 | **直接移植**(纯函数零依赖,`current-message-focus.js`/`standard-event.js` 几乎可照搬 Python) |
| 3 | **trusted/untrusted 上下文信封**(buildObservationEnvelope:trusted_context/untrusted_user_inputs/system_generated_memory 在 prompt 层告诉 LLM 只有用户消息不可信)+ 反注入 14 正则 | 护栏 | 中 | 直接移植(纯 prompt 范式) |
| 4 | **外部文件安全三件套**:路径遍历过滤(`../`)、JSON 体积上限(卡5MB/世界书10MB 防 parse 炸弹)、日志脱敏(password/apiKey/token) | 导入器(读外部ST卡) | **高** | 直接移植(**即使单机本地也该做**,因为导入不可信ST卡) |
| 5 | **range_trace_output 来源追踪 + range_analyze 质量评分**(反查 AI 这句来自哪条预设/世界书 + 检测八股/角色偏离) | 50工具MCP | 中 | 仅思路(补"输出可观测/质检") |
| 6 | **命名空间四元组隔离**`(scope_type,scope_key,character,preset)` + 一张表多 entry_type | memory.py scope | 中 | 仅思路 |
| 7 | **JSONPatch 变量结算协议**(`<UpdateVariable>` op/path/value)+ stat_data 前缀归一化 | 变量 data 层 | 中 | 直接移植(协议+归一化) |

**IM(QQ/OneBot)接入是否值得做?** —— **值得作为未来独立可选适配器,不进核心、不破坏零依赖**。理由:① 战略契合(暗宇宙角色在 QQ 群 RP,呼应 [[project_doll]] 陪伴方向);② 真正有价值的是「把多人真人对话压成单角色可消费的线性上下文」的**适配层**(消息头+意图路由,纯函数零依赖,可先吸收进群聊/扮演页,**即使不接 QQ 也能用于"单角色应对多用户"**);③ OneBot 接入需 WebSocket(Python 标准库无原生 ws),**正确做法是做成引擎外的独立薄适配进程,经 shadow-verse 零依赖 MCP 调引擎**,而非把 ws 塞进核心。**不值得碰**:重依赖、巨石文件、vanilla 19.8K 行 SPA、LLM 自算变量账、ELO 调教靶场。
