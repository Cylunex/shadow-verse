# ShadowVerse · 暗宇宙引擎

> **暗宇宙 · 无限世界 · AIGC** —— 一个生成并连接无数世界的多元宇宙引擎。
> 从元件与一句话造出自洽世界(无限世界);万物 AIGC 产出、可重生;角色在世界间穿梭、世界彼此相连(暗宇宙);同一个世界能用多种方式体验——**读它、玩它、看它自己跑、把它画出来**。

真实软件项目(零依赖 Python 3.10+),不是 skill 集。

**📚 文档导航**:[ARCHITECTURE.md](ARCHITECTURE.md)(工程地基/master spec) · [BORROW-ROADMAP.md](BORROW-ROADMAP.md)(竞品借鉴路线图) · [docs/VISION-MAP.md](docs/VISION-MAP.md)(愿景↔现状对照) · [docs/competitor-archives/](docs/competitor-archives/INDEX.md)(20 项目逐个深度档案)

## 不是"写小说工具"

小说和 RP 只是引擎的**两个体验透镜**。核心是五层:

```
L4 枢纽    跨世界实体穿梭 + 世界互联 = 暗宇宙
L3 透镜    读(narrate)· 玩(play)· 模拟自演化(默认关)· 可视化多模态(可插拔)
L2 基质    世界 / 实体 / 叙事线(持久 + 谱系 + 跨透镜事件日志)
L1 锻造    AIGC 生成世界/实体/线(取料 → 宿主模型生成 → 落盘+谱系)
L0 元件    创世素材(元素周期表式可复用元件;内置 ~40 个亲手提炼的起始元件,`codex-seed` 一键填充)
```

**分工(Model A)**:引擎管确定性状态;生成与写作的智力由**宿主 Agent 的模型**(OpenClaw/Hermes/Claude)提供。引擎不内置模型、不限尺度。

## 快速开始

```bash
PYTHONUTF8=1 python -m sv.skill_api doctor      # 自检
PYTHONUTF8=1 python -m sim.run_tests            # 全套测试(34 套全绿)

# 看得见也能用:播一个 demo 多元宇宙 → 启动网页控制台
PYTHONUTF8=1 python -m sim.seed                 # 造2世界/3角色/2章正文/跨世界穿梭
PYTHONUTF8=1 python -m sv.webapp                # → http://127.0.0.1:8787  (建/写/玩/群聊/分支/模式都能在页面做)

# AIGC 造世界:取料 → (宿主据包生成 world.md) → 落盘
python -m sv.skill_api world-prep "一座无限攀登的规则之塔" --tags 规则
echo '{"id":"infinite-tower","name":"无限之塔","genre":"无限流","body":"# 无限之塔\n..."}' | python -m sv.skill_api world-commit

# 造角色 / 线,读一章,玩一场
python -m sv.skill_api entity-prep infinite-tower "外冷内热的守护者"
python -m sv.skill_api narrate-prep infinite-tower first-climb --intent "破解第一条矛盾规则"

# 一句话造完整角色卡 + 四类世界书(创作包)
python -m sv.skill_api card-prep "外冷内热的赏金猎人" --genre 赛博朋克
python -m sv.skill_api worldbook-prep "末日废土城市" --genre 科幻

# 暗宇宙:角色跨世界穿梭
python -m sv.skill_api ascend infinite-tower ye-wudao          # 升格为跨世界实体
python -m sv.skill_api link infinite-tower linjiang "塔之裂隙"  # 世界互联
python -m sv.skill_api summon ye-wudao linjiang --entry 换皮进   # 在另一个世界开化身
python -m sv.skill_api nexus                                    # 多元宇宙鸟瞰

# 模式与数据互通(参考功能愿景)
python -m sv.skill_api modes                                    # 列 11 个体验模式
python -m sv.skill_api convert infinite-tower --thread first-climb --chapter 1 --to cyoa   # 小说章→互动分支
```

## CLI 命令(`python -m sv.skill_api <cmd>`)

| 组 | 命令 |
|----|------|
| L0 元件 | `codex-add` / `codex-seed`(填充 ~40 抽象起始元件) / `codex-list` / `codex-pick` |
| L1 锻造(AIGC) | `world-prep`→`world-commit` · `entity-prep`→`entity-commit` · `thread-prep`→`thread-commit` · `recipes`(题材配方) · `gen-world`/`gen-entity`/`gen-thread`/`gen-chapter`(配 SV_PROVIDER 一键生成) |
| 创作包(一句话生成) | `card-prep`/`gen-card`(角色卡 8 字段) · `worldbook-prep`(四类世界书内容规范) |
| 手建 | `new-world` / `new-entity` / `new-thread` |
| L3 透镜 | `narrate-prep`→`narrate-commit`(读) · `play-prep`→`play-commit`(玩) · `simulate-*`(模拟,默认关) · `render-*`(多模态) · `expr-gen`/`expr-classify`(立绘表情) |
| narrate 产线 | `narrate-run`(写→审→改→落一键,带 Run Event Journal 审计) · `review-prep`/`narrate-review`(审校) · `reflect-prep`/`narrate-reflect`(反思+规则化诊断) |
| 钩子台账 | `hook-alpha`(设α悬念) · `hook-add` · `hook-set`(状态机) · `hooks`(查;审校自动揪过期未回收的伏笔) |
| 群聊 | `group-new`/`group-chat`/`groups`(多角色同场,发言人选择+意图路由) |
| 线分支 | `branch-new`(从某章分叉+蝴蝶效应) · `branches` |
| 写作 skill | `skills`(列/读) · `skill-add` · `skills-seed`(灌起始写作 skill) |
| 模式/互通 | `modes`(列模式/取模板包) · `convert`(模式间一键转换:chat→小说/小说→cyoa/beats→剧本…) |
| L4 枢纽 | `ascend`(升格) · `summon`(召唤化身) · `link`(世界互联) · `nexus`(鸟瞰) |
| 管理/导出 | `export-thread`(全书导出) · `delete-*` · `unlink` · `merge-world`(世界融合) |
| 导入(ST 生态) | `import-card`/`import-card-world`(角色卡+世界书,带安全三件套) · `import-preset`(采样集+提示词模块) · `import-regex`(正则渲染) · `presets`(列出) |
| 工具 | `check`(单章) · `check-book`(全书纵向基线) · `worldbook`(世界书触发引擎) · `status` · `show` · `doctor` |

MCP(零依赖 stdio):`python -m sv.mcp_server`(**59 个 typed 工具**,语义同 CLI;作 OpenClaw/Hermes skill 用)。

## 目录

```
sv/         引擎(37 模块):
  L0-L4 核心  codex·codex_starter·forge(锻造+创作包)·recipes(题材字段化+钩型)·world·entity·thread·nexus·merge·lenses·memory·provenance·craft
  体验/模式   chat·group(群聊+意图路由)·branch(线分支)·modes(模式注册表)·convert(数据互通)
  质量/工艺   checks(质检+全书 stylestat+规则化诊断)·skills(SKILL.md 知识包)·journal(运行审计)·dedup(别名合并)
  扮演/世界书  worldbook(触发引擎+时效+position@D)·varstate(变量三段式)·expressions(立绘表情)·macros(内联宏)·promptkit(提示词组装)
  导入/容错   importer(ST卡/世界书/预设/正则+安全三件套)·jsonloose(脏JSON容错)·export
  基建        llm·config·clock·util(+安全)·skill_api·mcp_server(59工具)·webapp
sv/web/index.html   网页控制台(零依赖 stdlib server 的深色 SPA)
universe/   数据真相:codex/ · worlds/<w>/{world.md, entities/<e>/{card,profile,state,experiences,chat,vars,avatar,portraits/<emotion>},
            threads/<t>/{thread,meta,hooks,beats,chapters/,sessions/,renders/,branches/,runs/}, worldbook.json, wi_state/}
            · nexus/ · groups/ · presets/ · regex/ · skills/ · player.json
sim/        run_tests(总跑) · 34 套测试 · smoke · seed(demo 播种)
docs/       ARCHITECTURE.md(master spec) · BORROW-ROADMAP.md(竞品借鉴) · VISION-MAP.md(愿景对照) · competitor-archives/(20 项目逐个档案)
sv.conf / sv.local.conf · deploy/
```

## 两种用法

- **独立运行**:`python -m sv.webapp` 起网页控制台,在 **⚙ 设置** 页填自己的 LLM(OpenAI/兼容端/Anthropic/Ollama)与渲染 key——保存即时生效、无需重启,密钥只存本机 `sv.local.conf`(gitignore,不入库)。一切自包含。
- **嵌入 Agent**:作为 OpenClaw/Hermes 的 MCP skill,**不用配 LLM**——生成/写作走宿主 Agent 的模型(Model A)。见 `deploy/`。

## 网页控制台

`python -m sv.webapp` → http://127.0.0.1:8787 起一个零依赖网页控制台(读写同一批 `universe/` 文件,直接调引擎;深色"暗宇宙"主题;只绑 `127.0.0.1`):

**看**:多元宇宙地图(世界节点+连接边)、世界设定、章节阅读器、角色经历时间线、**跨世界实体的各世界化身对照**(灵魂一致/记忆独立)、元件库。

**用**(直接在页面操作):
- 新建世界 / 实体 / 叙事线 / 元件,编辑世界设定 —— 每个建表都带 **🔮 AI生成**(配了 `SV_PROVIDER` 就真生成,没配=stub 占位)
- **✍ 写一章**:**🔮 AI写本章**(一键写正文+结构化沉淀)或「取写作包」喂你自己的 LLM → 审改 → 勾每个角色这章沉淀(客串自动忽略)→ 落章,回执显示字数/自动质检/门控
- **✨ AI 产线写章**:一键跑 写手→审校→修订→落章,弹窗显示全过程(草稿字数 / 审校 findings / 修订轮数 / 落章回执)
- **🧠 反思**:横向校验最近数章全局自洽 + 提示漏掉的成长(建议,不自动落)
- **🎭 玩一场**:场景+过程+按角色勾「触发成长」条件写回
- **💬 对话**:在角色页点「对话」,用你在设置里配的 LLM 跟角色逐句聊(以第一人称扮演,带记忆与人设);对话存角色 `chat.jsonl`。需先在 ⚙ 设置 配 LLM
- **📥 导入角色卡**(总览页):吃 SillyTavern 卡 V1/V2/V3(JSON 或 PNG 内嵌)+ 世界书。卡一般自带世界,**默认「新建独立世界」**(卡→它自己的世界);也可「并入现有世界」。**PNG 卡的图自动设为角色头像**(不是纯文本了)
- **💬 扮演页**(不只是聊天框):右侧「**你扮演谁**」(用户身份,治"对话里我的身份老变")+「**变量面板**」(好感度/HP/进度…,三段式 data/rules/meta + 护栏防模型乱写 + 进度条;🎲 **AI 据人设建变量卡**)+ 头像/立绘;消息区头像气泡 + **◀ i/n ▶ swipe 一楼多候选**(切候选变量自动回滚)/ 🎭 生成表情立绘(回复按情绪换脸)/ 🔄换一个 / ↩撤回 / 清空。模型输出的 ```html``` 状态面板在 **sandbox iframe** 安全渲染。
- **👥 群聊**(多角色同场):建群选几个角色 → 自动选发言人(@提名/talkativeness/禁连说)+ 意图路由,多角色轮流发言,共享群级变量与世界书。
- **🎚 模式 Hub**:11 个体验模式(酒馆RP/小说/CYOA/剧本/漫画/跑团/梦境…)按 核心/支柱/世界 分组;模式=透镜+模板+视图,数据可一键互通(见 `convert`)。
- **↩ 撤销导入**:导入的角色页有撤销按钮(删角色 + 剥掉它并进的世界书);新建世界的导入直接删那个世界即可
- **🔗 世界融合**:把一个世界(角色/线/设定)融进另一个——小卡世界可融入大世界,为暗宇宙多元宇宙铺路
- **📜 故事时间线**:把一个世界跨所有叙事线的 beats + 角色★成长时刻合到一条时间轴,跨世界实体标出
- **⚙ 设置**:在页面里配 LLM provider/key/model、渲染 key,即时生效;状态面板显示当前 LLM/渲染是否启用
- **⬆ 升格**角色为跨世界实体、**✦ 召唤**进别的世界、**⇄ 连接**世界
- **🖼 多模态**:角色「生成立绘」(用固定 appearance 锁脸保持像同一人)、叙事线「生成场景图」,出图存进图库展示 —— 配 `SV_RENDER=gitee + GITEE_API_KEY` 才出图(Gitee z-image,~18s),没配则休眠
- **📖 导出全书**(把一条线的全部章节下载成单个 markdown)、**🗑 删除**世界/线/实体/元件(带确认,删世界自动清枢纽里它的连接与化身)

> 生成智力来自宿主模型(Model A)或你在 `sv.conf` 配的可插拔 LLM(`SV_PROVIDER`,默认 stub 关)。AI 生成**返回正文供你审改后再落盘**(人在环)。只绑 `127.0.0.1`(单机本地工具)。

## 状态

**五层贯通 + 模式层 + 完整可用**(测试 **34 套全绿**,37 模块 / 59 MCP 工具):元件取料 · AIGC 锻造世界/实体/线 + **创作包(一句话→角色卡+四类世界书)** · narrate 产线(写→审→改→落 + 钩子 + 全书 stylestat + 规则化诊断 + Run Event Journal 审计 + 写作 skill 库 + 四维相关章节反查) · **扮演页**(swipe一楼多候选 + 变量三段式+护栏 + HUD sandbox iframe + 立绘表情切换 + AI建变量卡 + 内联宏) · **群聊**(多角色同场+发言人选择+意图路由) · **线分支**(从某章分叉+蝴蝶效应) · **模式层**(11 模式注册表 + 数据互通转换) · **世界书触发引擎**(关键词/selective/递归 + sticky/cooldown/delay时效 + position@D + probability + 互斥组) · 别名合并去重 · 跨世界穿梭+互联+融合 · 多模态出图 · 导入 ST 角色卡/世界书/预设/正则(+安全三件套) · 中文写作工艺库 · LLM 脏 JSON 容错 · 故事时间线 · 导出/管理 · 网页配 LLM。

**两批竞品吸收**已落地(详见 [BORROW-ROADMAP.md](BORROW-ROADMAP.md) + [docs/competitor-archives/](docs/competitor-archives/INDEX.md));**愿景骨架**(统一底层+多模式+数据互通)已搭(详见 [docs/VISION-MAP.md](docs/VISION-MAP.md))。

**后面再做**(详见 ARCHITECTURE「Backlog」):各模式专属前端视图(CYOA 选项 UI / 跑团属性 / 漫画排版 / 地图导航)· MCP↔SSE 桥(让 MCP 直接操控网页)· 向量记忆全量版(L0-L3+图扩散,规模驱动)· 小说→世界书对接知轩藏书 7815 本 · 音频生成 / PDF/EPUB 导出。simulate 自演化与多模态渲染**接口已建、默认关/休眠**。
