# 混沌酒馆 · 重设计蓝图与交接(Chaos Tavern)

> 本文是 shadow-verse「大重设计」的**单一事实源 + 续作交接**。新会话从这里冷启动:读本文 + 项目记忆,跑 `python -m sim.run_tests`(全绿),起 `python -m sv.webapp`(→ http://127.0.0.1:8787)。
> 缘起:用户 2026-06-22「感觉项目不对了,挖本质重新设计」+「前端太普通没感觉」;后定调为下方愿景。

---

## 一、北极星愿景:混沌酒馆

一座以「混沌生成」为底层逻辑的**多世界叙事与互动系统**,以酒馆为所有世界的交汇枢纽,把小说创作、跑团规则、游戏机制、虚拟角色互动与 AIGC 生成统一起来。

- **底层 · 混沌规则**:不断演化的生成规则,世界可被 生成 / 分裂 / 重构 / **回溯**。
- **中层 · 三千世界**:由规则衍生,每个世界 = 独立的小说宇宙 / 跑团副本 / 游戏关卡 / 情感场景,各有逻辑与角色。
- **顶层 · 混沌酒馆**:既是入口也是中枢,连接、调度、记录所有世界的运行状态。
- **多重身份入座**:创作者(写小说/世界观)· 冒险者(进副本跑团)· 玩家(游戏化成长/任务)· 与具备**持续记忆 + 跨世界存在**的虚拟角色建立长期情感/剧情关系。
- **本质**:不是单一故事,而是一台**持续运转的 AI 叙事引擎**——内容在「规则驱动 + 生成式模型」共同作用下无限扩展,形成可无限延展、可交互、可游玩的多世界内容宇宙。

优先级(用户定):**RP / 陪伴(虚拟女友)= 现在;小说 = 其次;跑团 / 游戏 / 更多 AIGC = 之后。** 魂与世界**同等重要**,不放弃世界线。

### 求同存异(核心架构准则)
> 「底层用同一个,大部分是组件;思想可以各自发展,没必要强求。混沌种青莲,三千世界,各表一枝。」

- **同(共享底层 + 组件)**:混沌规则 / 一条时间线 / 一个魂 / 通用数值 / 组件(craft 写作技巧、recipes 题材配方、skills、参考资料)。任何世界、任何镜头都可取用。
- **异(各表一枝)**:每个镜头/世界的「思想」自行生长——小说有小说的章法,跑团有跑团的规则,游戏有游戏的机制,陪伴有关系的逻辑。**不要把上层强行塞进一个僵硬的统一契约**;它们共享底座与组件,但各表一枝。
- 工程含义:`Lens` 契约保持**最小**(只约定"提交落到同一基质"这一个触点 = `commit_core`),不强求各镜头形态一致。

---

## 二、形而上 ↔ 引擎(玄学有实质,不是装饰)

| 形而上 | 含义 | 引擎机制(已建/规划) |
|---|---|---|
| **混沌** | 生成之源,万物所出 | `forge`(L1 锻造)+ 宿主 LLM(Model A)+ substrate |
| **规则 / 道** | 混沌里的序,因果与守恒 | `commit_core`(唯一写入口=一条时间线)· `memory` 铁律 rebuild≠retrieve · 钩子账本(因果:plant→payoff)· `checks`(守恒/质检,0 token) |
| **青莲 / 心灯(魂)** | 混沌种青莲:跨世界不变量的"我" | `sv/soul.py`:`universe/souls/<id>/`(anchors 唯一真相 + identity.jsonl 身份记忆,指针非快照)|
| **三千世界** | 一花一世界,各表一枝 | `world` + `thread`(世界线)+ 各镜头(lenses) |
| **业 / 回溯** | 因果不虚,可回溯重演 | 钩子账本 + `beats.jsonl`(业/事件日志)+ `branch`(分裂)+ **回溯=待建** |
| **酒馆** | 众生交汇的窗口与中枢 | 枢纽 nexus + 网页主屏(待做成混沌酒馆) |

---

## 三、架构:一魂 · 多门 · 一条时间线

**核心对象**
- **World**(`sv/world.py`)= 三千世界之一的舞台:canon/设定 + entities/ + threads/。
- **Thread**(`sv/thread.py`)= 世界线:`beats.jsonl`(跨镜头事件日志,带 `lens` 标签)+ `hooks.json`(因果账本)+ chapters/sessions/renders。**一个世界可有多条线(多副本/书)。**
- **Entity / 化身**(`sv/entity.py`)= 某世界里的角色;`card.soul_id` 存在=某魂的一具化身(本地 state/经历/关系),否则=独立角色(行为同今天)。
- **Soul / 魂**(`sv/soul.py`)= 跨世界不变量(opt-in):`anchors.md`(唯一真相)+ `identity.jsonl`(身份记忆,跨化身/跨镜头共享)。**只存不变量,不存 state/episodic。**
- **Lens / 门**(`sv/lens.py`)= 一扇体验之门的最小契约(`prep` 只读组包 / `commit` 经 `commit_core` 唯一写盘)。标签闭合集 `LENS_TAGS`=narrate/play/companion/simulate/render/cross。
- **数值面板**(`sv/attrs.py`)= 多维「攻略式」状态卡(lens 无关,酒馆/陪伴/跑团共用),落 `varstate` 三段式。

**核心循环**:`prep(读基质)` → 宿主模型生成(Model A)→ `commit_core`(角色门控沉淀 + 写回状态 + 落 beat 到世界线 + 标记镜头)。**commit_core 是唯一写入口**——任何门的事件都落同一条 `beats.jsonl`,无孤岛。

**魂的三层(各有唯一属主,指针非快照)**:
- 不变量(per 魂):anchors + identity.jsonl(身份级)。grow 一次,所有化身/镜头可见。
- 化身(per 世界):state.json(此刻)+ experiences.jsonl(瞬时/持久)+ vars.json(数值/关系)。episodic 世界本地隔离。
- 镜头视图(无存储):prep 临时组的上下文包。

**两条升华路径(opt-in,普通角色不升华)**:① **提取** `ascension.extract`(就地抽魂,搬身份记忆进魂,落数值卡)② **创造** `ascension.create_soul`(一出生就是魂)。**跨世界召唤** `ascension.summon`:真化身 + 出生绑魂(身份即刻共享)+ 受链接约束(无门记「无门强召」)+ **在目标世界线落 cross beat(魂降临是那个世界的事件——世界有后果)**。

---

## 四、已落地(全绿,逐步 commit,CLI/浏览器端到端实测)

| 阶段 | 内容 | 关键文件 |
|---|---|---|
| **P0** | `commit_core` 统一写入口 + `Lens` 协议 + 闭合标签;narrate/play 走它(字节等价) | `sv/lens.py` |
| **数值** | 多维攻略卡 + **galgame 关系攻略板**(REL_AXES 9轴:好感/心动/信任/依赖/亲密/默契/安全感/心防逆/占有欲 + 阶段/称呼/里程碑/隐藏真心话);lens 无关 | `sv/attrs.py` |
| **P1** | 魂薄核心(dormant:无 soul_id 字节等价);anchors/retrieve/sediment 走魂指针;`retrieve_soul` union;`append_identity` | `sv/soul.py` `sv/memory.py` `sv/entity.py` |
| **P2** | RP → 世界线(门控 `SV_RP_COMMIT`,关=旧行为):每轮 RP 落 beat 到 thread | `sv/chat.py` |
| **P3** | 多元宇宙变真:extract/create_soul/summon(世界有后果)+ **命令面**(CLI `extract`/`create-soul`/`summon-soul` + MCP 自动派生 + webapp `/api/extract|create-soul|summon-soul`、`/api/soul/<id>`)+ 实体页按钮「✨提取为魂」「✦召唤」「🜂魂」徽标 | `sv/ascension.py` `sv/skill_api.py` `sv/webapp.py` `sv/web/index.html` |

**测试**:`sim/test_lenses`(commit_core 契约)、`test_attrs`(数值+galgame关系)、`test_soul`(魂/共享/隔离)、`test_rp_commit`(RP→世界线/字节等价)、`test_ascension`(升华/召唤/世界后果)。全部进 `sim/run_tests.py`。

**重设计 commits(在 HEAD 一串)**:P0 commit_core / 数值地基 / P1 魂核 / P2 RP世界线 / P3核 多元宇宙 / P3命令面 / P3前端钩。

---

## 五、待续(都是稳底座上的「各表一枝 + 整合」,不重写底层)

1. **P5 · 混沌酒馆前端(最大、用户最在意)**:网页主屏 = 混沌酒馆(梦幻/玄学/高级,非暗黑战情室);三千世界漂浮可入;魂如心灯穿行;**galgame 关系攻略板 HUD 渲染**(`attrs` 的 `vis:rel` 现在还没专门渲染,陪伴板只在 mockup);镜头切换;extract/summon 已有按钮。参考会话里给过的几张 mockup(无限世界主屏 / 轮回者攻略面板 / galgame 关系板 / 混沌酒馆宇宙观)。
2. **P4 · 陪伴透镜 + Doll 合回**:陪伴 = 魂 + 关系攻略板(HUD 主角)+ chat(已能跑,差前端抬板)。**决定:代码新长 `CompanionLens`(~150行,复用 RP+关系schema+魂绑定),数据合回 Doll**(隔离导入器把 Doll 灵魂迁进 `souls/`;**需 Doll 实际数据文件**)。不搬 Doll 运行时(避免第二引擎)。
3. **P3b · 退役 legacy**:旧 `nexus.py`(NexusEntity 平行树)迁到新魂、overview/枢纽页显示魂(现在新魂不进 overview 的 nexus.entities);**`purge_world` 要清 `universe/souls/` 下的孤儿魂**(已知:删世界不清魂)。
4. **回溯 / 分裂(混沌规则的形而上能力)**:世界状态/世界线可回溯重演(快照+回滚);分裂=已有 `branch.py` 可接。
5. **承重墙验证**:会话里那个对抗式审查(P0+attrs+P1)卡在 0 字节疑似挂了;靠 39 测试 + 端到端兜住。可重跑一遍专审魂层/字节等价。
6. **跑团 / 游戏镜头**:各表一枝,后期接(跑团规则 = 一个 Lens 实现 + 自己的思想/数值)。

---

## 六、关键决策 & 坑(给续作的你)

- **魂是 opt-in**:只有「提取/创造」才升华;普通角色只活自己世界(`soul_id` 缺省=字节等价今天)。绝不默认全升华。
- **数值化初期厚、像攻略**(用户要),后期可精简(调 `meta.vis`=hidden 或删维度,不动结构)。与「你」的关系最厚(galgame)。
- **dormant / gated 迁移**:每步可回退、绝不重写绿底层;新行为默认关(`SV_RP_COMMIT` 等)→ 旧测试字节等价。
- **求同存异**:`Lens` 契约保持最小,别把各镜头思想强行统一。
- **环境坑**:Windows 上 `pkill -f` 杀不掉 webapp(WindowsApps python 启动壳);用 `Get-CimInstance ... sv.webapp | Stop-Process`。preview 基建会抓 8601(aiagents-stock),要 eval 跳到 8787。LF→CRLF 警告无害。
- **运行**:`PYTHONUTF8=1 python -m sim.run_tests`(全绿)· `PYTHONUTF8=1 python -m sv.webapp` · CLI `python -m sv.skill_api extract <world> <entity>` / `create-soul` / `summon-soul`。

---

*一灯能传三千世界,各表一枝。混沌酒馆,生生不息。*
