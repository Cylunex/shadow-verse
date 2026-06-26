# 创作系统组件化 · 落地计划（交付 code 实施 / 审查依据）

> 依据：`ShadowVerse/创作组件化.md`（33 组件「叙事 OS」设计稿）× shadow-verse 引擎现状盘点（2026-06-26）。
> 配套：`REDESIGN.md`（产品方向 / 红线）、`docs/FRONTEND-PLAN.md`（前端归属准则）、`ARCHITECTURE.md`（引擎地基）。
> 定位：回答「怎么把创作组件化体系融入系统」。**不照搬 33 组件、不深化引擎、不与 RP/陪伴优先级抢身位。**

---

## 〇、先对齐三条判断（必读）

1. **不照搬 maximalist 模拟引擎。** `创作组件化.md` 的灵魂落点是「可叙事的世界模拟系统」——一个 maximalist 模拟引擎愿景，和北极星正面冲突（REDESIGN：「别再深化引擎=重蹈 v1」「手艺 > 架构」；CHAOS-TAVERN 优先级：RP/陪伴=现在，小说=其次）。本文只取它的 **组件清单 / taxonomy** 价值：挑零依赖纯数据的少数补，重型模拟（经济流动 / 势力 AI / NPC 自驱 / 战争 / 时间自走 / 随机事件生成器）**一律不做**（`simulate` 透镜 + `pulse.md` 已休眠覆盖）。

2. **组件库归 legacy 维护，新 UI 只消费（用户定）。** legacy = 组件库的「工厂 / 仓库」：定义 / 新增 / 编辑 / 灌种 / 调试创作组件；新 UI = 消费端：写章 / 对话时把已定义组件作为可勾选项用。完全符合 FRONTEND-PLAN Phase 0 归属准则（「调引擎 / 养组件」→ legacy，「用产品」→ 新 UI）。

3. **「组件化」的工程实质 = 把硬编码工艺外化成可编辑数据。** 现状盘点：`codex` 已是「数据 + CRUD + legacy UI」现成范本；`skills` 已数据化（SKILL.md）。但 **`craft.py`（钩13式 / 引子7式 / 扩充6技法 / 防注水4问 / 三层弧 / PLAY 协议）是纯代码常量、零落盘**，`recipes.py` 是代码内 `dict`、只读暴露。它们要「可新增编辑」，**必须先从硬编码外化成组件数据**。这是本计划的脊柱。

---

## 一、组件库 = 什么（统一概念）

把散落的创作原料统一成「创作组件库」，每个组件 = 一条可取用 / 可组合 / 可勾选的数据：

| 组件族 | 现状 | 存储 | 处置 |
|---|---|---|---|
| 元件 codex | ✅ 数据 + CRUD + legacy UI | `universe/codex/` | **范本，照它做** |
| 写作技巧 craft（钩13式 / 引子7式 / 扩充6技法 / 防注水 / 三层弧 / PLAY 协议） | 🟡 纯代码常量、零落盘 | `craft.py` | **外化为数据组件** |
| 题材配方 recipes（pacing / 爽点 / 疲劳词 / 钩型 / 审校维度） | 🟡 代码内 dict、只读暴露 | `recipes.py` | **外化为数据组件** |
| 写作 skills（SKILL.md 知识包） | ✅ 数据化、有 add/seed | `universe/skills/` | 接进 legacy CRUD |
| 名词库 glossary | 🔵 空白 | — | **新建数据组件** |
| 多级大纲模板 outline | 🔵 空白（`thread.md` 仅单层大纲） | — | **新建数据组件** |
| 预设 preset | ✅ 导入已支持 | `universe/presets/` | 已有，纳入管理台 |

> 判断标准：进组件库的，是「**跨世界 / 跨作品可复用的创作原料与工艺**」；某个具体世界 / 角色 / 线的内容（world.md、card、thread.md 正文）**不是组件**，仍归各自基质，不搬进来。

---

## 二、三阶段工单（交付 code）

### 全局硬约束（每条都守）

1. **不重写绿底层。** 外化走「dormant / 字节等价」：组件数据缺省即**播种自现有常量**，缺数据时行为与今天逐字节一致，`python -m sim.run_tests` 保持 **39/39**。
2. **零依赖、零构建**（沿用 FRONTEND-PLAN：浏览器原生 ES module，无 npm/CDN）。
3. **组件库 CRUD 只进 legacy；新 UI 不得出现组件「管理」入口**（消费 / 勾选可以）。
4. **一任务一 commit**，标题含任务号，写清改了什么 + 验收点。

---

### Phase C1 · 工艺外化（引擎，最该先做）

把 `craft` / `recipes` 的硬编码常量外化成「组件数据 + 默认种子」，行为字节等价。

- **做**：复用 codex 数据范式，新增组件存储（建议 `universe/components/{craft,recipes}/`，或扩 codex 的 category——由 code 定，但须与 codex 一致）。`craft.py` / `recipes.py` 改为「**先读组件数据、缺省回退到内置常量种子**」。
- **配套**：`craft-seed` / `recipes-seed`（把现有常量写成可编辑数据，一键灌种）。
- **验收**：① 不灌种时，narrate 产线注入与今天**逐字节一致**，39/39 全绿；② 灌种后改一条 craft 技巧 / recipes 字段 → 下次写章注入随之变。

### Phase C2 · 补两个真空白组件（引擎，纯数据零依赖）

> 这两件直接解决「写长篇不崩」，是 `创作组件化.md` #4–8 / #12–14 / #23 的核心，也补 ARCHITECTURE backlog 那条「章节蓝图六元数据（待做·基建已备）」。

- **glossary 名词库**：世界级 `universe/worlds/<w>/glossary.json`（人名 / 地名 / 技能名 / 组织名 + 别名）。**复用 `dedup` 防别名漂移、`worldbook` 触发引擎做在场注入**；写章 / 审校注入「命名一致」校验。
- **多级大纲脊柱**：`thread` 扩 `outline.json` —— 三级：**卷大纲 → 节点 beat outline（转折 / 爆点 / 信息点）→ 章节细纲六元数据（目标 / 冲突 / 钩子 / 信息披露 / 出场角色 / 目标字数）**。`forge` prep 注入、`checks` 加「偏离大纲」诊断（与现有 `reflect_diagnose` 同构，输出 Finding）。
- **验收**：给一个世界建名词库、给一条线建三级大纲；写章时被注入，审校能查出「命名漂移 / 偏离细纲」。

### Phase C3 · legacy 组件库管理台（开发者面向 CRUD，**重做好看好维护**）

> ⚠ 用户明确反馈：**现在的 legacy 看不懂、没法维护。** 组件库管理台**不沿用现 legacy 的密文风格**，要做成清晰可读、好维护的新区。

- **做**：在 legacy（开发者入口下）新建「**创作组件库**」区，统一管理全部组件族（codex / craft / recipes / skills / glossary / outline / preset）：浏览 / 新增 / 编辑 / 灌种 / 删除 / 组合预览。
- **UX 要求（一等，非可选）**：
  - **左侧组件族导航 + 右侧卡片列表**，每条组件一张卡（标题 + 摘要 + 标签 + 编辑/删除），不是一堵 JSON 墙。
  - **新增 / 编辑用结构化表单**（字段化），不是手填裸 JSON。
  - 命名、分组、空状态、保存回执都要清楚；中文标签，少工程黑话。
  - **可维护**：复用 codex 端点范式（`create` / `seed` / `delete`）+ 统一组件 schema；新组件族走同一套渲染，别再每块各写一套。
- **配套**：为 craft / recipes / glossary / outline 各补一组薄路由 CRUD 端点（调引擎，防目录穿越，沿用 `/static` 安全写法）。
- **验收**：在管理台能增删改一条 craft 技巧 / recipes 配方 / glossary 词条 / outline 模板并落盘生效；**页面一眼能看懂、加一个新组件族不用重写整页**；新 UI 不受影响、39/39 不变。

### Phase C4 ·（可选 / 后置）新 UI 消费端

写章 / 对话页把「已定义组件」暴露成可勾选开关（活人感 / 对白优化 / 文风·五感 / 去 AI 味 / 某钩型 / 某文风预设）——对齐 REDESIGN 点名的 VisionTale 赢点。

- **仅暴露勾选，不做管理。** 先决：C1–C3 完成。受「表面别超实质」约束，最小化、**压在验收闸之后**再做。

---

## 三、红线 / 不做

- ❌ **重型模拟**（经济流动 / 势力 AI / NPC 自驱 / 战争影响 / 时间自走 / 随机事件生成器）——`simulate` 休眠已覆盖，别上。
- ❌ 别把小说产线做成主轴喧宾夺主（小说是其次，RP/陪伴优先）。
- ❌ 组件「管理」别糊进新 UI 沉浸界面（只在 legacy）。
- ⚠ 外化必须**字节等价兜底**，绝不重写绿底层。

---

## 四、总验收（Definition of Done）

- `python -m sim.run_tests` = **39/39 全绿**（外化字节等价）。
- 组件库在 legacy 可增删改、落盘生效；**管理页清晰可读、可维护**；新 UI 无组件管理入口。
- **真作品闸（最重要）**：拿样例作品（《夜行动物》/ 苏屿），用新组件（三级大纲 + 名词库 + 至少一个外化工艺开关）写 2 章，标准只有一条——**它有没有更不崩、更有手艺，你还想不想接着看。** 组件齐不齐不是目标。

> 实施完成后，请把「每个任务做了什么 + 自测结果」列一份交接，按本文件逐条审查。

---

# 附录 A · Phase C1「工艺外化」详规（code 可直接照写）

> 目标：把 `craft.py` / `recipes.py` 的硬编码常量外化成「可编辑组件数据」，**缺数据时与今天逐字节一致**。
> 铁律：先读数据、缺省回退内置种子；旧测试不动。

## A.0 存储与配置

`config.py` 加一行（与 `CODEX_DIR` 并列）：

```python
COMPONENTS_DIR = UNIVERSE / "components"   # 创作组件库(工艺/配方,全局可复用)
```

目录布局（每个 group 一个 JSON 文件，统一外壳）：

```
universe/components/
  craft/
    hook_techniques.json  chapter_openers.json  writer_checklist.json  reviewer_rubric.json
    reflector_focus.json  expansion.json  dialogue.json  anti_water.json  hook_arcs.json
    play_protocol.json  output_self_check.json  consistency_checks.json
    reviewer_discipline.json  growth_triggers.json  suspense_curve.json  var_update_protocol.json
  recipes/
    genres.json           # RECIPES + AUDIT_DIMS 合一(每条=一个题材)
    profiles.json         # 量化 PROFILES
    hook_taxonomy.json     # 追读力钩型
```

统一外壳：

```json
{ "group": "hook_techniques", "kind": "menu", "title": "悬念钩十三式",
  "entries": [ {"key":"突然揭示", "desc":"章末抛一个改变全局认知的事实。", "order":0, "enabled":true, "builtin":true}, ... ] }
```

每条 entry 都带 `order`（排序）、`enabled`（停用不删）、`builtin`（种子来的=true，用户新增=false）。

## A.1 组件 kind（4 类 → 决定 entry schema + C3 渲染模板）

| kind | 原始形态 | entry schema | 涉及 group |
|---|---|---|---|
| `menu` | dict{名:释} | `{key, desc}` | hook_techniques、chapter_openers、hook_taxonomy（扩 `when/fit/misuse`）|
| `list` | list[str] | `{id, text}` | writer_checklist、reviewer_rubric、reflector_focus、expansion、dialogue、anti_water、hook_arcs、play_protocol、output_self_check、consistency_checks |
| `note` | 单条 str | `{text}`（单 entry）| reviewer_discipline、growth_triggers、suspense_curve、var_update_protocol |
| `record` | dict{键:字段} | keyed 字段 | recipes/genres（pacing/climax/tropes[]/forbidden[]/emphasis[]/audit_dimensions[]）、recipes/profiles（hook_strength/coolpoint_per_chapter/stall_max/romance_gap_max/transition_max）|

> **group 是闭集**：新增「一条 entry」支持；新增「一个 group」=改引擎（不在 C3 管理台范围，要在 UI 写清，免得用户误期望"加组"）。

## A.2 引擎读取改造（字节等价是铁律）

**新增 `sv/components.py`**（薄数据层，复用 `config.load_json/save_json`）：

```
load_group(family, group, seed)  → 有文件返回其 entries；无文件返回 seed(内置常量)。← 缺数据=字节等价
upsert(family, group, entry)     → 新增/编辑一条(按 kind 校验)
delete(family, group, key_or_id) → 删一条
seed_all()                       → 幂等把内置 _SEED_* 写成 group 文件(已存在跳过)
list_groups()                    → 列所有 group(family/kind/title/count) 供管理台
```

**`recipes.py`（零消费点改动，最省）**：把 `RECIPES/AUDIT_DIMS/PROFILES/HOOK_TAXONOMY` 留作 `_SEED`，把 `get()/get_profile()/genres()/forbidden_words()` 内部改成 `load_group(...)` + 合成。所有消费点（checks/forge/lenses/modes/skill_api/webapp）都走这几个函数，**无需改动**。

**`craft.py`（消费点集中在 lenses，可控）**：常量留作 `_SEED_*`，加同名小写访问器（`writer_checklist()`、`hook_techniques()` …），`hook_menu()` 改调访问器。

要改的消费点（共两文件、约 20 处）：

- `sv/lenses.py`：L62/64/65/66、82、94、159/160、176/177、196、210、230/232、287/288/289（`craft.WRITER_CHECKLIST` → `craft.writer_checklist()` 等）。
- `sv/modes.py`：L99（recipes，无需改）、L100（`craft.WRITER_CHECKLIST`/`PLAY_PROTOCOL` → 访问器）。
- 备选：用模块 `__getattr__`（PEP 562）保留大写常量名透明回退 = **零 diff**，但显式访问器更好维护，二选一由 code 定。

## A.3 种子（seed）

`components.seed_all()` 幂等：把 `_SEED_*` 写成 group 文件（同 group 已存在则跳过，写入标 `builtin:true`）。挂到 CLI `components-seed` + MCP 自动派生 + webapp `POST /api/components/seed`。

**缺省不灌种**：首次运行无 `universe/components/` → `load_group` 回退种子 → 与今天字节等价。灌种只发生在「想编辑组件」时。

## A.4 端点（薄路由，镜像 codex 写法）

| 方法 | 路径 | 作用 |
|---|---|---|
| GET | `/api/components` | 列所有 group（family/kind/title/count）|
| GET | `/api/components/<family>/<group>` | 取一组 entries |
| POST | `/api/components/<family>/<group>/upsert` | 新增 / 编辑一条 |
| POST | `/api/components/<family>/<group>/delete` | 删一条 |
| POST | `/api/components/seed` | 幂等灌种 |

安全：`family`/`group` 走**已注册白名单**（只认闭集内的 group），entry 字段按 `kind` 校验；沿用 `/static` 的防目录穿越写法。

## A.5 验收

- **字节等价**：不灌种时 `python -m sim.run_tests` 全绿；narrate/review/reflect/play 的 prep 包与改造前逐字节一致。建议**新增 `sim/test_components.py`** 锁两条：① 无文件时 `load_group == _SEED`；② 灌种后 upsert 一条 → 读取可见（→ 测试集 39 升 40，全绿）。
- **可编辑生效**：改 `hook_techniques` 一条 `desc` → 下次 narrate prep 的钩子技法库随之变；给 `recipes/genres` 玄幻 `forbidden` 加一词 → `checks` 疲劳词命中随之变；删一条 `writer_checklist` → 写手系统提示少一条。
- **不越界**：新 UI 无任何组件管理入口；改造只动 `config.py`/`components.py`(新)/`craft.py`/`recipes.py`/`lenses.py`/`modes.py`/`webapp.py`(薄路由)/`skill_api.py`(CLI)，引擎其它模块不动。

> C1 落地后，C2（glossary/outline）复用 `components.py` 同一套读取-回退-CRUD 范式；C3 管理台按 4 个 kind 各做一个渲染模板即可覆盖全部 group。
