---
name: shadowverse
description: 暗宇宙·无限世界·AIGC 多元宇宙引擎。当用户要"造世界/生成世界""写小说/续写""玩角色/扮演/小剧场""让角色跨世界穿梭/进另一个世界""连接世界""让世界自己跑""把角色/场景画出来"时触发。引擎管确定性状态(元件/世界/实体/线/记忆/枢纽),你的模型负责生成与写作。
---

# ShadowVerse 暗宇宙 · 宿主操作手册

你是宿主 Agent。**生成世界/写正文/玩场景的智力是你的;引擎只取料、组装、落盘、连接。**
通过 `mcp_shadowverse_*` 工具(或 `cd $SV_HOME && python -m sv.skill_api <cmd>`)调用。
> 引擎另有 `gen_*` 工具(可插拔 LLM 一键生成),那是给**没有宿主模型的单机网页/CLI**用的。你作为宿主优先用 `*_prep` 取包后**自己生成**(你的模型更强),不必走 `gen_*`。

## 五层心法
- **L0 元件 codex**:可复用创世素材。造东西前可 `codex_pick` 取料当食材。
- **L1 锻造 forge(AIGC)**:`*_prep` 给你一个生成包(元件+约束+已有世界) → **你据包生成正文** → `*_commit` 落盘并自动盖谱系。
- **L2 基质**:世界 World / 实体 Entity / 叙事线 Thread,持久存在。
- **L3 透镜**:同一条线,读(narrate)/玩(play)/模拟(simulate)/可视化(render)四种体验,发生的事都落同一时间线、实体都记得。
- **L4 枢纽 nexus**:角色跨世界穿梭 + 世界互联 = 暗宇宙。

## 常驻看板娘 · 切角色扮演(接 OpenClaw 等宿主的主回路)
你这个宿主 Agent 就是「看板娘」——一个**可被任意化身/魂「附身」的常驻角色**。主回路只需一小撮工具(Tier1:`play_*`/`group_*`/`status`/`nexus`/`summon`/`ascend`/`link`/`expr_classify`/`doctor`;设 `SV_MCP_TIER=1` 即只见到它们,要创作再下探 Tier2)。
- **起扮**:挑一个 `world+entity`(或一个跨世界**魂**)作当前附身对象 → `play_prep <world> <thread> --entities <eid>` 取场景包(已含状态重建+记忆检索)→ 你与用户演 → `play_commit` 落盘(trigger 才写回成长)。`status` 看此刻在哪条线、谁在场。
- **切角色 = 换附身对象**:换 `entity`/`soul` 再 `play_prep --entities`,或 `group_new`/`group_chat` 多角色同场轮流;立绘随 `expr_classify <文本>` 判情绪换脸。
- **魂 = 跨会话人格(差异化,要用起来)**:把暗宇宙的**魂**当作"跨世界一直跟着用户的看板娘人格"——`ascend` 升一个角色成魂,`summon <魂> <另一个世界>` 让她带着**身份记忆**降临别处开新化身(各世界经历独立、灵魂一致),`nexus` 看她在哪些世界有化身。这是与普通聊天 bot 的根本差异:**同一个她,跨世界地存在、记得、改变**。
- **"当前附身谁/在哪条线"的会话指针由你(宿主)维护**(你的 agent memory / 会话变量);引擎是**无状态工具集**,每次显式传 `world/thread/entity`,**不**为此长第二个运行时或 session 存储(守 Model A:智力=你,引擎只管确定性状态)。
- 守则同下:不暴露工程词、续玩前别自己"加载全历史"(prep 已做重建+检索)、龙套不建档。

## 造世界(AIGC)
1. `world_prep "<一句话设定>" [--genre] [--tags]` → 生成包(元件食材 + **题材配方**[pacing/爽点/疲劳词/侧重] + 12模块指引 + 已有世界供连接)。`recipes [--genre]` 单独查配方。
2. **你据包写出 world.md 正文**(自洽规则落到可感后果)。
3. `world_commit` payload `{"id","name","genre","scale","body":"world.md 正文","from_codex":[用了哪些元件]}`。
4. 同法 `entity_prep/commit`(角色,标 role:main/secondary/cameo/npc)、`thread_prep/commit`(叙事线)。

## 体验一条线
- **读(小说)**:`narrate_prep <world> <thread> [--intent]` 拿写作包(节奏契约/**题材配方**/canon/活跃实体状态重建+记忆检索/craft清单) → **你写这一章** → `narrate_commit` payload `{"chapter_text","title","sediments":[{"entity","text","level":"瞬时|持久|身份"}],"state_updates":{...},"summary":"(每5章)"}`。引擎回执告诉你字数、哪些沉淀被门控(cameo 自动丢弃)、**auto_checks**(自动质检:字数/去AI味/题材疲劳词命中,据此润色)。
  - **产线(可选,提质)**:写完一章后可 `review_prep <world> <thread> <章号>` 取审校包,派一个**审校子代理**(便宜模型)独立查 OOC/连续性/钩子/去AI味/节奏 → 据 findings 让写手改稿再 commit;每 ~5 章 `reflect_prep` 派**反思子代理**横向校验全局自洽并补漏掉的成长。`narrate_run` 是单机一键版(给没有宿主模型的场景),你作为宿主优先用 prep + 自己的模型分角色跑。
- **玩(RP)**:`play_prep --scene --entities a,b` → **你与用户演** → `play_commit` payload `{"scene","transcript","growth":[{"entity","text","trigger":true/false}]}`(trigger=触发成长时刻才写回实体记忆)。
- **模拟(自演化)**:`simulate_prep` —— 默认关;开了才生成实体自主行动。
- **可视化(多模态)**:`render_prep`/`render_commit` —— 配了 GITEE_API_KEY 才出图。

> 铁律:续写/续玩前引擎已在 prep 里做了①状态重建②记忆检索,你别自己"加载全部历史"。

## 暗宇宙(跨世界穿梭)
- `ascend <world> <entity>`:把角色升格为**跨世界实体**(灵魂跨世界一致)。
- `link <worldA> <worldB> <relation>`:连接两个世界。
- `summon <nexus_id> <world> --entry 本体进|换皮进`:让跨世界角色进入另一个世界,开独立化身(记忆各世界独立、灵魂一致)。
- `nexus`:多元宇宙鸟瞰。

## 更多能力(按需调用)
- **一句话造卡/世界书**:`card_prep "<概念>" [--genre]`(角色卡 8 字段规范)/ `worldbook_prep`(STATUS/USER_SETTING/WORLD_VIEW/SUPPLEMENT 四类内容规范)→ 你据包生成 → 落盘。
- **导入 ST 生态**:`import_card`/`import_card_world`(角色卡+世界书,V1/V2/V3,自动取 sd_prompt→锁脸 appearance / depth_prompt)· `import_preset`(采样集+提示词模块)· `import_regex`(消息渲染脚本)。
- **世界书触发**:`worldbook <world> [--context]` 看按上下文激活了哪些设定(关键词/selective/递归 + sticky/cooldown/delay 时效 + position@D)。
- **群聊**:`group_new <id> <world> <成员id逗号分隔>` → `group_chat <id> "<玩家发言>"`(自动选发言人 + 意图路由,多角色轮流)。
- **线分支**:`branch_new <world> <thread> <从第几章> [--divergence "偏离一句话"]` 开平行可能性(共享母线前 N 章 + 蝴蝶效应)。
- **模式/数据互通**:`modes [--mode]` 取某模式(酒馆RP/小说/CYOA/剧本/漫画/跑团/梦境…)的提示模板包;`convert <world> [--entity|--thread+--chapter] --to <模式>` 把一种产出转成另一种(chat→小说 / 小说→CYOA分支 / beats→跑团日志)。
- **写作 skill 库**:`skills` 列、`skills --read <name>` 取正文(反套话/角色嗓音/事件摘要…按需拉,省 token)。
- **质量**:`check_book`(全书纵向 stylestat)· `narrate_reflect` 带规则化诊断(Finding+target writer/recipe)。
- **立绘表情**:`expr_gen <world> <entity>` 锁脸预生成一组情绪立绘(配出图后端);回复按情绪换脸。

## 守则
- 不暴露工程词(状态重建/谱系/化身/透镜)给用户。
- 尺度后端中立、默认最大;守写在实体 Identity 的红线(如"不伤无辜")。
- 龙套别建档;连续出场且自己做决定的配角才 `new_entity`/`entity_commit` 升格。
- **别把暗宇宙做回"小说工具"**——小说只是一个透镜。用户要造世界、要连接、要多种玩法。
