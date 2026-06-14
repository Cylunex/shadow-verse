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
| L1 | `forge.py` | 世界/实体/线生成器;每个 `*_prep`(取料组装)+ `*_commit`(落盘盖 provenance) |
| L1 | `recipes.py` | 题材配方(pacing/爽点/疲劳词/侧重),注入锻造包与写作包,提升 AIGC 质量 |
| L2 | `world.py` / `entity.py` / `thread.py` | 持久基质;`provenance.py` 记谱系;`memory.py` 管记忆 |
| L3 | `lenses.py` | narrate / play / simulate / render 四透镜,各 `*_prep` + `*_commit` |
| L4 | `nexus.py` | `ascend`(升格)/`summon`(召唤化身,跨世界穿梭)/`link_worlds`(世界互联)/`render_map` |

---

## 数据契约(暗宇宙唯一真相 · `universe/`)

人类创作内容用 **Markdown**;引擎结构态用 **JSON/JSONL**(可靠解析、可检索、可 fork)。

```
universe/
├── codex/<category>/<id>.md + index.json   # L0 元件(worlds/mechanics/characters/conflicts/organizations/scenes/themes)
├── worlds/<world-id>/
│   ├── world.md          # 12 模块设定 + 与其它世界的连接 + 世界契约
│   ├── meta.json         # genre/scale/contract/links/provenance        引擎管
│   ├── canon.md · pulse.md
│   ├── entities/<id>/    # 本地实体:card.json(role) + profile.md + state.json + experiences.jsonl
│   └── threads/<id>/     # 叙事线(被透镜体验)
│       ├── meta.json     # genre/scale/pacing/lenses[]/chapter_count/provenance
│       ├── thread.md     # 立意+节奏契约+大纲
│       ├── beats.jsonl   # 跨透镜事件日志(读/玩/模拟 发生的事都落这)  引擎管
│       ├── chapters/NNN.md  # narrate 产出
│       ├── sessions/<s>.md   # play 产出
│       └── renders/*.png     # render 产出(多模态)
└── nexus/                # L4 枢纽
    ├── nexus.json / nexus.md   # 多元宇宙索引(鸟瞰)
    ├── links.json              # 世界互联边(暗宇宙拓扑)
    └── entities/<id>/          # 跨世界实体
        ├── soul.md · meta.json(anchors/incarnations/origin/provenance)
        └── incarnations/<world-id>/  # 各世界化身:state.json/experiences.jsonl/growth.md/summary.md
```

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
- **确定性质检** `sv/checks.py`(`check_text` 可审未落盘的草稿):字数/题材疲劳词/括号旁白。审校与落章回执都带。

## 自演化(simulate 透镜)· 多模态(render 透镜)

- **simulate(自演化)**:世界 pulse 推进 + 实体按欲望自主行动生成 beat。**能力已建,默认关**(`SV_SIMULATE=off`)。开启即"世界你不在时自己长"。
- **render(多模态)**:角色立绘(用实体 `appearance` 固定外貌词锁脸保持同一人)+ 叙事线场景图(Gitee z-image,零依赖 urllib,带空白图重试,同 Doll)。已接进 CLI(`render-entity`/`render-scene`)+ 网页(出图按钮 + 图库,`/img/` 路由防目录穿越服务 PNG)。**可插拔,未配 `SV_RENDER=gitee + GITEE_API_KEY` 则休眠**。
- 二者都是"留接口、规模/需求到了点亮",不挡当下。

---

## 接口形态(Model A)

- **`sv/skill_api.py`** CLI:`codex-*` · `world/entity/thread-prep|commit`(锻造)· `new-world/entity/thread`(手建)· `narrate/play/simulate/render-prep|commit`(透镜)· `ascend/summon/link/nexus`(枢纽)· `check/status/show/doctor`。
- **`sv/mcp_server.py`** 零依赖 stdio MCP(22 个 typed 工具,翻译成 CLI argv 复用,零回归)。
- 配置走项目根 **`sv.conf`**(KEY=VALUE,免环境变量)。

---

## 演进阶梯

| 阶段 | 做什么 | 标志 |
|------|--------|------|
| **Phase 0 地基(本次)** | 五层贯通:元件→锻造→基质→读/玩透镜→枢纽(升格/召唤/互联);模拟&渲染留接口 | 能造世界/角色/线、多种体验、角色跨世界穿梭(冒烟 21/21) |
| **Phase 1 生成深化** | 锻造器配方化、批量造世界、元件库充实;narrate 子代理产线(写→审→反思) | 一句话/一个 IP 批量长出自洽世界 |
| **Phase 2 自演化 + 多模态** | 开 simulate(世界自己跑)、render 立绘/地图、向量记忆 | 世界你不在时自己长、看得见 |
| **Phase 3 暗宇宙生态** | 跨世界事件传导、世界自演化拓扑、app 视图层(多元宇宙地图/世界市场) | 自演化的连接宇宙 |

接口都留好不挡路。**当下最大杠杆 = 最强宿主模型 + 已建工艺 + 取料组合。**

## 坚决不做 / 已判过
- ❌ 引擎内置生成/写作模型 / 限尺度(智力=宿主模型,后端中立)。
- ❌ 现在就上向量库/数据库(规模驱动才上,接口已留)。
- ❌ 把暗宇宙做回"小说产线"——小说只是一个透镜,别让它喧宾夺主。
- ⚠ 别为远期基建,牺牲"先用最强模型把世界造好、体验做爽"这件当下最重要的事。
