# 接入 OpenClaw 当看板娘 · 适配计划（交付 code 实施 / 审查依据）

> 缘起：把 shadow-verse 放进 OpenClaw（宿主 Agent），由 OpenClaw 充当「看板娘」——用它的 agent loop + 对话 UI + 工具调用机制来更方便地操作项目，并支持「切换不同角色扮演」。
> 配套：`deploy/README.md`（三步接入）、`deploy/skills/shadowverse/SKILL.md`（宿主手册）、`sv/mcp_server.py`（~60 typed 工具）、`REDESIGN.md`（红线）、`docs/FRONTEND-PLAN.md`（webapp 现状）。
> 定位：本文是 plan-level 工单，schema/代码细节留给 code 发挥。

---

## 〇、核心判断（必读）

1. **结构上几乎不用改。** shadow-verse 本就是「为宿主 Agent 设计的 MCP skill」（Model A：引擎管确定性状态，智力=宿主模型）。接 OpenClaw 是它的**原生形态**，不是改造。今天注册 MCP server 即可让 OpenClaw 调用全部 ~60 工具。
2. **「操作型看板娘」白拿。** 上一轮讨论里要自建的「B 级·能替你操作 app 的看板娘 + MCP↔SSE 桥」，由 OpenClaw 的 agent loop **直接提供**，不必自造桥。
3. **要做的是「换外壳 + 收敛工具面 + 补玩法」，不是动引擎核心。** 四点适配见下，全部不碰 `world/entity/thread/memory/nexus` 等核心模块。
4. **守 Model A 铁律：** 不在引擎里再造 agent runtime / 第二个模型；不做两套并行看板娘。

---

## 一、已经现成（即插即用，仅核对）

| 能力 | 现状 |
|---|---|
| MCP server | `python -m sv.mcp_server`，stdio JSON-RPC，~60 typed 工具，语义同 CLI |
| 接入指引 | `deploy/README.md` 三步（放项目 → 装 SKILL.md → 注册 MCP，附 JSON 配置）|
| 宿主手册 | `deploy/skills/shadowverse/SKILL.md`（五层心法 + prep/commit 流 + 暗宇宙 + 守则）|
| 数据/代码分离 | `SV_UNIVERSE_DIR` 指向数据区，更新代码不碰 `universe/` |

> 这部分**不需要新建**，适配时只核对注册命令与 OpenClaw 的 MCP 配置格式对齐即可。

---

## 二、四点适配（本计划的实体）

### A1 · 工具面收敛 / 分层（最该先做）

~60 个工具一股脑塞进 agent loop = 工具过载（context 占用 + 选择困难 + 误调）。按「看板娘的主回路 = RP/陪伴 + 切角色 + 导航」分层，建议：

- **Tier 1（常驻暴露，看板娘主回路）**：`play_prep`/`play_commit`、`group_new`/`group_chat`、`status`、`nexus`、`summon`、`ascend`、`link`、`expr_classify`、`doctor`。
- **Tier 2（创作/质量，按需）**：`world_prep`/`commit`、`entity_prep`/`commit`、`thread_prep`/`commit`、`narrate_prep`/`commit`、`review_prep`、`reflect_prep`、`hooks`/`hook_*`、`check`/`check_book`、`card_prep`、`worldbook_prep`、`worldbook`、`modes`、`convert`、`branch_*`、`skills`/`skills_seed`、import 系列、`merge_world`。
- **Tier 3（单机/休眠/调试，宿主一般不调）**：`gen_*`（单机一键，宿主自己写更强）、`render_*`（需出图后端）、`simulate_*`（默认关）、`codex_add`/`codex_seed`、`presets`。

落地方式由 code 定（任选其一，不改工具语义）：
- 在 `mcp_server.py` 给 `TOOLS` 加 `tier` 标记 + 环境变量/参数控制 `tools/list` 暴露层级；或
- 不动工具集，只在 SKILL.md 写清「决策树 / 常用路径 / 何时才下探 Tier 2-3」，让宿主少摸索。
- **验收**：OpenClaw 默认只见到 Tier 1 一小撮即可跑通「陪一个角色 + 切角色 + 看暗宇宙」；需要创作时按指引拉 Tier 2。

### A2 · SKILL.md 补「常驻看板娘 + 切角色扮演」玩法

现手册是「造世界/写小说/玩」的任务手册，缺一条**常驻陪伴 + 随时切换附身角色**的主线。补一节（提纲）：

- **看板娘 = 可被任意化身/魂「附身」的常驻角色**：开场如何挑一个 `world+entity` 或 `soul` 起扮。
- **切角色**：换附身对象 = 换 `entity`/`soul`，调 `play_prep --entities` / 群聊 `group_*`；立绘随 `expr_classify` 换脸。
- **魂作跨会话人格**：把暗宇宙的**魂**当作"跨世界跟着用户的看板娘人格"——`summon` 进不同世界、`nexus` 看化身；身份记忆共享、各世界经历独立。这是与普通聊天 bot 的差异点，要写进手册让宿主用起来。
- **守则延续**：不暴露工程词、续玩前别自己加载全历史（prep 已做状态重建+记忆检索）、龙套不建档。

### A3 · 「当前附身谁」的会话指针归宿主

引擎是**无状态工具集**（每次显式传 `world/thread/entity`）。"看板娘此刻扮谁、在哪条线"这个会话态：

- **建议由 OpenClaw 侧维护**（它的 agent memory / 会话变量），引擎**不**为此长第二个运行时或会话存储——守 Model A。
- 若确需引擎侧记一个"上次活跃指针"做便利，**上限是一个极薄的只读便利字段**（如扩 `player.json`），绝不做成 session 系统。默认走宿主维护。

### A4 · 对齐 stale 文档 / 计数

`deploy/README.md` 写「22 个 typed 工具」，实际 ~60；README/SKILL/VISION 各处计数不一。适配时顺手统一（以 `mcp_server.TOOLS` 实际长度为准），免得宿主被旧数字误导。

---

## 三、定位边界：OpenClaw = 驱动层，webapp = 呈现层

接 OpenClaw 后，与 `FRONTEND-PLAN` 的 webapp **分工**（避免两套并行看板娘）：

- **OpenClaw（驱动层）**：对话 / 操作 / agent loop / 看板娘 / 切角色扮演。用户的「做事」走这里。
- **webapp（呈现层）**：聊天 agent 做不好的**可视化与阅读**——星图、章节阅读器、关系攻略板 HUD、化身对照、离别仪式、legacy 组件库管理。用户的「看与读」走这里。
- **边界**：webapp 不再去抢"对话/操作"主入口（其内置看板娘星瞳降级为"打开 webapp 时的本地向导/仪表盘"，或与 OpenClaw 入口二选一）。暗宇宙差异化（星图/化身/离别）留在 webapp 当"被看见的表面"。

> 这条是**产品定位决策**，本计划按此推荐落；若评审改判（webapp 仍为主、OpenClaw 作 power-user shell），A1-A4 不变，只调本节边界。

---

## 四、红线 / 不做

- ❌ 不在引擎里再造 agent runtime / 内置第二个模型（智力=宿主，后端中立）。
- ❌ 不做两套并行看板娘（webapp 一套 + OpenClaw 一套抢同一职责）。
- ❌ 不因接 OpenClaw 而把工具语义/数据格式改得偏向某一宿主——保持平台中立（OpenClaw/Hermes/Claude 通吃）。
- ⚠ 切角色/附身的会话态默认归宿主，引擎别悄悄长 session 存储。

---

## 五、验收（Definition of Done）

- OpenClaw 注册 MCP 后，**默认 Tier 1 工具即可跑通**：挑一个角色起扮 → 切到另一个角色 → 看暗宇宙化身/星图——全程不需手动翻 60 个工具。
- SKILL.md 含「常驻看板娘 + 切角色 + 魂作跨会话人格」一节，宿主据此能直接用。
- `python -m sim.run_tests` 仍 **39/39**（适配只动 `mcp_server.py` 工具元数据 / SKILL.md / deploy 文档，不碰引擎核心）。
- webapp 与 OpenClaw 职责无重叠：操作走 OpenClaw、呈现走 webapp。
- 平台中立未退步：CLI 与其它宿主（Hermes/Claude）仍可用。

> 实施完成后，请把「每点适配做了什么 + 自测结果」列一份交接，按本文件逐条审查。
