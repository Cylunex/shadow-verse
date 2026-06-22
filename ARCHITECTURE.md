# ShadowVerse · 暗宇宙引擎 — 架构地基(master spec)

> 工程地基。代码与数据以本文为准。这是 **真实软件项目**(零依赖 Python),不是 skill 集。
> 终极目标三词:**暗宇宙 · 无限世界 · AIGC**。不是"写小说工具",是一个**生成并连接无数世界的多元宇宙引擎**;小说、RP 只是其中两个"体验透镜"。
> 旧 `F:\Project\ShadowVerse`(markdown 工艺 skill 库)**仅供参考思路**,不照搬;craft 工艺被吸收成引擎喂生成的数据(`sv/craft.py`)。

---

## 北极星

> **一个会生长的暗宇宙:从元件与一句话生成无数自洽世界(无限世界),万物皆 AIGC 产出并可重生;角色在世界间穿梭、世界彼此相连(强连接),你能用多种方式体验同一个世界——读它、玩它、看它自己跑、把它画出来。**

每加一个设计过一遍:**它让"造世界更快更自洽 / 体验方式更多 / 世界与角色连接更深"吗?都不是,就不做。**

---

## 分工(Model A · 沿用 Doll 成功范式)

引擎管**确定性状态**:数据契约、核心循环、取料、落盘、谱系、连接。**生成世界/写正文/玩场景的智力 = 宿主 Agent 的模型**(OpenClaw/Hermes/Claude)。锻造器 `prep` 取料组装上下文 → Agent 用最强模型生成 → `commit` 落盘盖谱系。**引擎不内置生成/写作模型,不限制尺度(后端中立)。**

**可插拔 LLM(`sv/llm.py`,闭合单机生成回路)**:作为 skill 时不用它;单机网页/CLI 想"一键造世界/写章"可在 `sv.conf` 配 `SV_PROVIDER`(openai/anthropic/ollama,零依赖 urllib)。默认 `stub`(关,返回占位)。这与"引擎不绑定模型"不矛盾——provider 是用户自配的可选件(同 render/embed),引擎本身不 bundle。`forge.generate_*` / `lenses.narrate_generate` 即此路:取料→LLM→**返回正文供人审后再 commit**(不自动落盘,保留人在环)。

---

## 五层模型

```
L4 枢纽 Nexus      跨世界实体(升格+召唤化身) + 世界互联 = 暗宇宙之所以是"宇宙"
        ▲
L3 透镜 Lenses     读 narrate · 玩 play · 模拟 simulate(自演化,默认关) · 可视化 render(多模态,可插拔)
        ▲          —— 同一条线可被多种方式体验,发生的事都落进同一基质
L2 基质 Substrate  世界 World · 实体 Entity · 叙事线 Thread —— 持久暗宇宙(稳定 id + 谱系 + 跨透镜事件日志)
        ▲
L1 锻造 Forge      AIGC 核心:world/entity/thread 三个生成器(prep 取料 → 宿主生成 → commit 落盘+谱系)
        ▲
L0 元件 Codex      创世素材:可复用抽象元件 + AI摘要 + 标签 —— 无限生成的"元素周期表"
```

| 层 | 模块 | 职责 |
|----|------|------|
| L0 | `codex.py` | 元件入库/取料(`pick` 按相关度+标签喂锻造器) |
| L1 | `forge.py` | 世界/实体/线生成器 + **创作包**(`card_prep`/`worldbook_prep`/`gen_card`:一句话→完整卡+四类世界书);每个 `*_prep`+`*_commit` |
| L1 | `recipes.py` | 题材配方(pacing/爽点/疲劳词)+ **字段化 profile**(节奏红线阈值)+ 钩型分类 |
| L2 | `world/entity/thread.py` | 持久基质;`provenance` 记谱系;`memory` 管记忆;`merge` 世界融合;`branch` 线分支(分叉+蝴蝶效应) |
| L3 | `lenses.py` | narrate/play/simulate/render 四透镜,各 `*_prep`+`*_commit`;narrate 产线带 `journal`(运行审计) |
| L3+ | `modes.py` / `convert.py` | **模式层**:11 模式注册表(透镜+模板+视图,加模式不改核心)+ 数据互通(模式间一键转换) |
| L4 | `nexus.py` | `ascend`/`summon`(跨世界穿梭)/`link_worlds`/`render_map` |
| 扮演 | `chat`/`group`/`varstate`/`worldbook`/`expressions`/`macros`/`promptkit` | 扮演页(swipe/变量三段式/HUD/立绘表情)· 群聊(发言人+意图路由)· 世界书触发引擎 · 内联宏 · 提示词组装 |
| 质量 | `checks`/`craft`/`skills`/`dedup` | 质检(单章+全书 stylestat+规则化诊断)· 工艺库 · SKILL.md 知识包 · 别名合并去重 |
| 容错/安全 | `jsonloose`/`importer`/`util` | 脏 JSON 容错 · ST 导入(卡/世界书/预设/正则)· 外部文件安全三件套 |

---

## 数据契约(暗宇宙唯一真相 · `universe/`)

人类创作内容用 **Markdown**;引擎结构态用 **JSON/JSONL**(可靠解析、可检索、可 fork)。

```
universe/
├── codex/<category>/<id>.md + index.json   # L0 元件(worlds/mechanics/characters/conflicts/organizations/scenes/themes)
├── worlds/<world-id>/
│   ├── world.md          # 12 模块设定 + 与其它世界的连接 + 世界契约
│   ├── meta.json         # genre/scale/contract/links/provenance        引擎管
│   ├── canon.md · pulse.md   # world.md 可含「导入世界书」「融入自<src>」标记块(可精确剥离)
│   ├── entities/<id>/    # 本地实体
│   │   ├── card.json(id/name/role/appearance/greeting/tags/provenance) + profile.md
│   │   ├── state.json · experiences.jsonl   # 此刻 / 经历(核心循环)
│   │   ├── avatar.{png,jpg,webp}   # 头像/立绘(导入 PNG 卡自动设;可手动上传)
│   │   ├── chat.jsonl · vars.json  # 扮演对话史 / 该对话的变量(好感度/HP/进度…)
│   │   └── portraits/*.png         # 生成的立绘
│   └── threads/<id>/     # 叙事线(被透镜体验)
│       ├── meta.json     # genre/scale/pacing/lenses[]/chapter_count/provenance
│       ├── thread.md · hooks.json  # 立意+大纲 / 结构化钩子台账(α+状态机)
│       ├── beats.jsonl   # 跨透镜事件日志(读/玩/模拟 发生的事都落这)  引擎管
│       ├── chapters/NNN.md · sessions/<s>.md · renders/*.png   # 读/玩/可视化产出
├── nexus/                # L4 枢纽
│   ├── nexus.json / nexus.md / links.json   # 多元宇宙索引 + 世界互联边
│   └── entities/<id>/    # 跨世界实体:soul.md + meta.json + incarnations/<world>/{state,experiences,growth,summary}
└── player.json           # 你扮演谁(用户身份;治对话身份漂移)
```
(机器/密钥配置在项目根 `sv.conf`[模板,入库] + `sv.local.conf`[本机密钥,gitignore];见「接口形态」)

**实体四类 + 成长写回(代码门控)**:main/secondary 写回、cameo 客串不写回(引擎丢弃)、npc 随戏份。`*_commit` 按 `role` 门控,skill 做不到的硬保证。

---

## 核心循环(所有透镜共享,只在「生成」分叉)

```
① 状态重建 rebuild(entity)  state + 近期经历 + anchors → "现在什么样"   【确定性·范围小】
② 记忆检索 retrieve(entity, query, k)  全历史加权挑 → "该想起什么"      【加权·全历史】
③ 生成     [读]写一章 / [玩]互动 / [模拟]自主行动 / [可视化]出图          【宿主模型】
④ 经历沉淀 append experiences(瞬时/持久/身份)——按 role 门控 + thread.beats 记事件
⑤ 状态更新 write state
⑥ [触发] 成长时刻(两难/被深触动/违背或捍卫原则/不可逆失去 → 有界提升 anchors)
```

> **铁律:① rebuild(确定性)≠ ② retrieve(加权),`sv/memory.py` 两个函数物理隔离,绝不混成"加载历史"。** 跨世界化身也走这套(同一灵魂 anchors、各化身记忆独立)。

---

## 强连接多元宇宙(L4 是重点,不是远期)

- **升格 ascend**:把某世界的本地实体升进枢纽 → 成为跨世界实体(灵魂/anchors 跨世界一致)。
- **召唤 summon**:跨世界实体进入另一个世界,开一条独立化身(incarnation);`entry` 决定带不带记忆(本体进/换皮进)。**这就是角色跨世界穿梭。**
- **世界互联 link_worlds**:世界之间连边(裂隙/同源/传承…),多元宇宙有拓扑而非孤岛。
- 同一灵魂 + 多个世界化身,各化身记忆独立不串味——这是"暗宇宙"而非"一堆故事"的本质。

---

## narrate 产线(读透镜 = 小说 · 主线)

把 NovelKB 验证有效的产线落成代码强制闭环:**写手 → 审校 →(修订)→ 落章**,外加**反思**横向校验。
```
narrate_prep → [写手] → narrate_commit(落章+沉淀+自动质检)
review_prep  → [审校] verdict pass/revise + findings(OOC/连续性/钩子/去AI味/节奏)
narrate_revise ← 据审校意见改稿(保情节与篇幅)
reflect_prep → [反思] 横向校验时间锚/战力刻度/α进度/配速 + 补漏掉的成长
```
- **两种用法**:① 宿主模型——`*_prep` 取包,host agent 自己跑写手/审校/反思(最强模型)。② 单机编排 `narrate_run`——配了 `SV_PROVIDER` 一键 写→审→改→落,返回全过程 trace。stub 模式产出占位草稿+确定性审校+落盘(不进修订循环,不死循环)。
- **结构化钩子台账** `hooks.json`(α悬念 + 每条钩子 type/level/status 状态机:待回收/进行中/已回收/顺延/放弃 + 埋章/计划回收章)。写作包注入开放钩子让写手推进其一;审校**确定性揪出过期未回收的伏笔**(payoff_target 已过却仍开放 → verdict=revise);反思带 overdue 清单。
- **确定性质检** `sv/checks.py`(`check_text` 可审未落盘的草稿):字数/题材疲劳词/括号旁白/半角标点/重复短语/长句堆叠。审校与落章回执都带。题材专属审校维度由 `recipes.AUDIT_DIMS` 注入审校 rubric。

## 玩透镜 = 扮演(`sv/chat.py` + play)

两条玩法,共享同一份实体/记忆:
- **play**(记录式):给场景,记录一段 RP(`play_prep`/`play_commit`),触发成长时刻才条件写回(客串不写)。
- **chat**(逐句对话,单机交互):和一个实体实时聊。**不是纯聊天框,是可操作的扮演页**:
  - **用户身份** `universe/player.json`(name+persona)——系统提示注入"和你对话的是「玩家」"+**铁律(只写角色言行/绝不替玩家说话/绝不把玩家写成别人/说完就停)**,transcript 用真名标记。**治"对话里我的身份老变"的根**。
  - **变量系统** `entity/vars.json`(好感度/HP/进度…):模型可在回复尾 `===变量===` 块下 JSON 结算(`+N/-N`/新值),引擎解析+从正文剥离;面板可手动改。
  - **头像/立绘**:导入 PNG 卡自动设头像;手动上传;聊天头像气泡。
  - **swipe(一楼多候选)**:char 楼存 `swipes[]`/`swipe_id`/`swipe_meta`/`vars_before`;◀▶切候选(▶到末尾自动生成新候选),切候选时**从楼前基线重放变量增量**(不越加越多);`regenerate` 升级为追加候选(旧的可切回);`floor_regenerate` 任意楼重生成(截断+变量回滚到截断前)。借 Luker append 模型(2026-06-18,强化酒馆第1刀)。
  - 撤回 / 清空。
- 写正文/扮演的智力 = 宿主模型 或 单机配的可插拔 LLM(同 narrate)。

## 自演化(simulate 透镜)· 多模态(render 透镜)

- **simulate(自演化)**:世界 pulse 推进 + 实体按欲望自主行动生成 beat。**能力已建,默认关**(`SV_SIMULATE=off`)。开启即"世界你不在时自己长"。
- **render(多模态)**:角色立绘(用实体 `appearance` 固定外貌词锁脸保持同一人)+ 叙事线场景图(Gitee z-image,零依赖 urllib,带空白图重试,同 Doll)。已接进 CLI(`render-entity`/`render-scene`)+ 网页(出图按钮 + 图库,`/img/` 路由防目录穿越服务 PNG)。**可插拔,未配 `SV_RENDER=gitee + GITEE_API_KEY` 则休眠**。
- 二者都是"留接口、规模/需求到了点亮",不挡当下。

---

## 接口形态(三种,Model A)

引擎一套,三种用法:
- **`sv/skill_api.py` CLI** — 全部动词:codex-* / 锻造 prep|commit / 手建 / 透镜 prep|commit / narrate 产线 / hooks / 枢纽 ascend·summon·link / 导入 import-card[-world]·undo-import / merge-world / gen-* / config / check·status·show·doctor。
- **`sv/mcp_server.py` 零依赖 stdio MCP**(**59 个 typed 工具**,翻译成 CLI argv 复用,零回归)——作 OpenClaw/Hermes skill 时用,生成走宿主模型。
- **`sv/webapp.py` + `web/index.html` 网页控制台**(零依赖 stdlib server,深色 SPA)——单机独立运行的主入口:造世界/角色/线(手填·AI生成·**导入ST卡**)、narrate 产线、**扮演页**(对话+身份+变量+立绘)、钩子台账、跨世界穿梭、多模态出图、故事时间线、导出、删除/**世界融合**、⚙设置(配 LLM)。读写同一批 `universe/` 文件;只绑 `127.0.0.1`。

**配置**:`sv.conf`(入库模板,无密钥)+ `sv.local.conf`(本机/UI 写入,含密钥,gitignore),优先级 env > local > base > 默认;**网页设置面板写入即热加载,无需重启**。

**两种模式**:① 独立运行——网页配自己的 LLM(OpenAI/兼容端/Anthropic/Ollama)。② 嵌入 Agent——作 skill,生成走宿主模型,不配 LLM。

---

## 现状(已建)
五层贯通 + 产线 + 扮演页(流式输出+中止 · 多 provider 容错+超时 · 作者笔记 · 快速回复 · 多开场白 · 任意楼编辑/删/重生 · 后台自动总结) + 群聊 + 线分支 + 模式层 + 枢纽穿梭 + 多模态 + 导入/融合 + 网页控制台 + 设置热加载。**测试 35 套全绿**。37 个引擎模块、59 个 MCP 工具。

**模式层 + 数据互通(2026-06-18,落地《参考功能.txt》愿景骨架,对照见 docs/VISION-MAP.md)**:
- `modes.py` —— 把「体验模式」形式化成可插拔注册表(11 模式作纯数据:酒馆RP/小说/陪伴/CYOA/剧本/漫画/音乐/跑团/教育/梦境/世界探索)。每模式 = 透镜 lens + 提示模板 guide + 输出格式 + 视图 view;`mode_pack` 按模式组装提示模板包。**加模式只加一条 MODES 数据,不改核心**——正是愿景「新增模式只需模板+视图」。
- `convert.py` —— 数据互通,以 thread.beats(跨透镜事件日志)为枢纽:chat→小说章节 / 小说→CYOA分支 / 小说→剧本 / 小说→漫画分镜 / beats→跑团战役日志,一键转换(prep 包供宿主改写,配 LLM 则 `run` 直出)。
- 网页加「🎚 模式」Hub(按 core/pillar/world 分组展示 11 模式)。

**借鉴生态再吸收一批(2026-06-18,详见 docs/competitor-archives/)**:
- `util` 外部文件安全三件套(safe_name 路径遍历 / guard_size 体积上限 / redact 日志脱敏)接进导入器(借 MimirLink)。
- `dedup.py` UnionFind 别名合并 + LLM 输出归一化三件套(normalize_flag/results_array/resolve_pair_index,容忍模型乱答)——实体/记忆去重(借 Novel-Auto-Generator)。
- `craft` 增补输出前自检清单 + 一致性5校验 + 变量增量UPDATE协议(借 interactive-novel);`recipes` 字段化(题材 profile 节奏红线 + 钩型分类)+ `REVIEWER_DISCIPLINE` 逐维只给证据(借 webnovel-writer)。
- `checks.reflect_diagnose` 规则化诊断(Finding 带证据+target writer/recipe)+ `thread.related_chapters` 四维相关章节反查(零 embedding 长篇召回,借 ainovel-cli)。
- `group` 结构化消息头 + `analyze_focus` 意图路由(意图分类+回复目标+策略提示,借 MimirLink)。
- `branch.py` 线分支(从某章分叉,共享母线前N章 + 蝴蝶效应 divergence_points + Scene/Beat 图,借 infiplot+interactive-novel)。
- `journal.py` Run Event Journal(append-only JSONL+seq 单调,接进 narrate_run 全程落账,借 TauriTavern)。
- `skills.py` Anthropic 兼容 SKILL.md 加载器(frontmatter+三 scope later-wins+短目录注入写手,含起始写作 skill 种子,借 Luker)。
- `forge` 创作包(card_prep/worldbook_prep/gen_card:一句话→完整角色卡+四类世界书内容规范,借 Narratium)。

**强化酒馆/RP（2026-06-18,第1-6刀,详见 BORROW-ROADMAP.md）**:
- **swipe** 一楼多候选 + 任意楼重生成 + 变量可回滚快照(chat.py)。
- **变量三段式** `varstate.py`(data/rules/meta + 深路径 + 五op + validate 护栏 clamp/step/ro/enum)+ **HUD sandbox iframe**(前端把 ```html``` 块塞进 `allow-scripts` 不 `allow-same-origin` 的 iframe,主题色拼进 srcdoc)。
- **立绘表情切换** `expressions.py`(seed+appearance 锁脸预生成 portraits/<emotion>.png + 轻量 LLM 情绪分类,回复按情绪换立绘)+ 卡 `sd_character_prompt→appearance`、`depth_prompt`、`talkativeness` 取字段。
- **群聊** `group.py`(多角色同场,activate_natural_order 发言人选择:@提名→talkativeness掷骰→禁连说→话痨池兜底;群级共享 vars+世界书,各角色私有记忆)。
- **世界书时效** `worldbook.py` 升级(sticky/cooldown/delay 按楼号 + wi_state.json + sticky→cooldown 交接;position 0-4 分桶 + @D depth 注入;probability;inclusion group 互斥)。
- **内联宏** `macros.py`(只读 getvar/roll/random/if)+ **预设组装器** `promptkit.py`(role 分离 + @D apply_depth + 卡 depth_prompt 注入)+ **AI 建变量卡**(从人设识别该追踪哪些状态)。

**借鉴酒馆/小说生态吸收的能力(2026-06-18,详见竞品分析)**:
- `jsonloose.py` —— LLM 脏 JSON 容错解析(去围栏/思考块/补闭合符/中文标点兜底),narrate/chat 落库统一走它(借 InfiPlot parseJsonLoose + Novel-Auto-Generator)。
- `checks.check_book` —— 全书纵向 stylestat(句式 tic 章均/跨≥3章逐字复读/章末同构/开篇时间词率/标题问题),补单章 check 的盲区,接进 reflect(借 ainovel-cli/stylestat.go)。
- `craft.py` 工艺库 —— 悬念钩13式/章首引子7式/扩充6技法/对话工艺/防注水四问/三层弧/play 权限分离双段输出协议,注入写作包与 play 包(借 chinese-novelist-skill + interactive-novel)。
- `worldbook.py` —— 世界书运行时触发引擎(matchKey 正则/全词/CJK + selective AND_ANY/ALL/NOT + 常驻 + 递归 lore + 字符预算),导入卡的世界书结构化存 `worlds/<w>/worldbook.json`、按上下文激活注入 narrate/chat(借 SillyTavern world-info.js + Narratium world-book.ts)。
- `importer` 扩 ST 预设/正则 —— preset→采样集 + 有序提示词模块 + `assemble_preset` 组装器;regex→消息渲染改写(忠实文本替换,$1/{{match}}/placement/depth;HTML 面板渲染待前端沙箱)。

## Backlog(后面再做 · 已记)
> 已完成的不再列(立绘表情/世界书触发引擎/线分支/swipe/变量三段式/HUD/群聊/预设导入/模式层/数据互通…见上「现状」)。

| 项 | 说明 | 状态 |
|----|------|------|
| 各模式专属前端视图 | CYOA 选项驱动 UI / 跑团属性面板 / 漫画分镜排版 / 世界探索地图导航(branch/macros/render/simulate 引擎已就位) | 待做(加视图不改核心) |
| MCP↔SSE 桥 | 让 MCP 直接操控网页控制台(已有 MCP+网页+都绑 127.0.0.1,差一条 SSE 回执桥 + Origin 锁) | 待做(借 infinite-canvas/canvas-agent) |
| 向量记忆全量版 | L0-L3 分层记忆 + Dense/Lexical/RRF/MMR + PPR 图扩散(EMBED_PROVIDER 接口已留;蓝图见 competitor-archives/LittleWhiteBox) | 规模驱动才上(已有 bigram 占位 + 四维相关章节反查零依赖先行版) |
| 小说→世界书 | 章回切分+UnionFind 别名合并(dedup 已就位)→ 对接 Novel/知轩藏书 7815 本 | 待做(基建已备) |
| 文生图入对话 / 漫画排版 | render 已有,接进 chat/comic 模式 | 待做 |
| 正则 HTML 面板高级 | apply_regex 已做文本改写,HUD sandbox iframe 已渲染;余主题色同步/多面板管理 | 大部分 done |
| 音频生成 / PDF·EPUB 导出 | music 模式有模板无音频后端;export 有 md 无 PDF/EPUB | 待做(可插拔接口) |
| 批量造世界 / simulate 自演化 | 选题材一次生成一批 / 世界自主跑 | 用户暂缓(simulate 能力已建,默认关) |

接口都留好不挡路。**当下最大杠杆 = 最强宿主模型 + 已建工艺 + 取料组合 + 给各模式补视图。**

## 坚决不做 / 已判过
- ❌ 引擎内置生成/写作模型 / 限尺度(智力=宿主模型,后端中立)。
- ❌ 现在就上向量库/数据库(规模驱动才上,接口已留)。
- ❌ 把暗宇宙做回"小说产线"——小说只是一个透镜,别让它喧宾夺主。
- ⚠ 别为远期基建,牺牲"先用最强模型把世界造好、体验做爽"这件当下最重要的事。
