# 前端落地·收尾工单（交付 code 实施 / 审查依据）

> 依据：对 P5–P8 落地的审查。新前端质量高、测试 39/39 全绿、安全过关；本工单只补**缺口**与**结构债**，不改引擎、不做魅力验证。
> 配套：`REDESIGN.md`（产品方向）、`docs/ui-prototype.html`（视觉参照）、`sv/web/index.html`（现状）。

## 全局硬约束（每个任务都必须守）

1. **不改引擎逻辑**：只在 `sv/webapp.py`（薄路由）和 `sv/web/*` 动；`world/entity/thread/memory/nexus/...` 等核心模块不动。
2. **测试常绿**：`python -m sim.run_tests` 必须保持 39/39（动了后端就补/跑测试）。
3. **零依赖、零构建**：不引入任何 npm/CDN/打包工具。允许用浏览器原生 ES module。
4. **安全不退步**：所有插值过 `esc()`；模型 HTML 只进 `sandbox="allow-scripts"`（不带 same-origin）的 iframe；新静态服务要防目录穿越。
5. **`/legacy` 必须始终可用**（旧控制台是兜底，不能弄坏）。
6. 每个任务**独立成一个 commit**，信息写清楚改了什么、验收点。

---

## Phase 0 · 方向已定（必读）

> **legacy = 底层 / 组件 / 调试层（开发者面向）。所有"用户向"功能都迁进新 UI——任何普通用户的动作都不应再需要打开 legacy。**

- **新 UI**：承载**全部用户功能**（创作世界/角色/小说、暗宇宙跨世界、导入导出、资源、质量/反思……）。因为它要吸收所有功能、且方向是"更组件化"，**JS 必须模块化**（见 T1.3，已从可选升为必做）。
- **legacy**：继续往"更底层、更组件化"走（延续 P7：组件层 / 补原语 / 去 eval）——只留**低层 / 调试 / 原语 / 组件试验台**用途，不再承担任何用户向创作；**从用户导航里撤掉，仅保留一个开发者入口**。
- 归属判断标准：**"用户为了用产品要做的事" → 新 UI；"开发者为了调引擎要做的事" → legacy。**

---

## Phase 1 · 卫生与结构债（低风险，先做）

### T1.1 归档原型、清理 repo 根
- **做**：把 `ui-prototype.html` 移到 `docs/ui-prototype.html`（它是一次性视觉原型，不该躺在 repo 根）。
- **验收**：repo 根不再有 `ui-prototype.html`；`docs/` 下能打开；README/文档里若有引用同步改路径。

### T1.2 抽出 CSS（拆 index 的第一步，最大收益最低风险）
- **做**：把 `sv/web/index.html` 里整段 `<style>` 抽到 `sv/web/static/app.css`，页面用 `<link rel="stylesheet" href="/static/app.css">` 引入。
- **配套**：`sv/webapp.py` 的 `do_GET` 增加 `/static/` 静态服务（参照现有 `/img/` 的写法：`resolve()` + 限定在 `WEB_DIR/static` 内 + 后缀白名单 `.css/.js`，防目录穿越；返回正确 `Content-Type`）。
- **验收**：页面外观/功能与改前**像素级一致**；直接访问 `/static/app.css` 能拿到、`/static/../webapp.py` 之类越权访问返回 404。

### T1.3 （必做，中风险）JS 按视图拆模块
> Phase 0 决定新 UI 吸收全部功能，单文件必然爆掉；且你要"更组件化"。所以这条是地基，**先于 Phase 2 做**。
- **做**：用原生 ES module 把 `index.html` 内联 JS 拆成 `sv/web/static/`：`api.js`（api/post/esc/md/toast 等原语）、`router.js`（路由表 + renderNav）、`components.js`（bubbleHtml/_hudIframe/modal/renderTrace 等可复用组件）、`views/{works,chat,companion,novel,worldbook,presets,settings,assets,chars}.js`。入口 `<script type="module" src="/static/main.js">`。
- **约束**：**纯搬运、零行为变化**；所有 hash 路由、弹窗、对话流式、swipe、HUD、溯源都要照常工作。Phase 2 的新功能一律以"新增 view 模块 / 复用 components"的方式加，不再回到单文件。
- **验收**：逐条手动走查每个页面与交互无回归；`index.html` 主体回到几百行以内（只剩骨架 + 模块引入）。

---

## Phase 2 · 把全部用户功能迁进新 UI（依 Phase 0）

> 目标：**任何用户向动作都不再跳 legacy。** 后端端点多数已存在（核对名称即可），主要缺新 UI 的入口/表单/视图。逐项做完后用 T2.9 总检：全站搜 `legacy` 不应再有"用户向"跳转。
> 先决条件：T1.3（模块化）已完成，新功能一律以"新增 view 模块 / 复用 components"方式加。

### T2.1 新建作品 / 世界（作品页）
- **做**：「＋ 新建作品」「✨ AI 制作」接 `/world/create`（AI 走 `/gen/world` 取正文→人审→落盘）。表单：id/名称/题材/一句话设定。
- **验收**：新 UI 从零建出世界并出现在画廊；不跳 legacy。

### T2.2 新建世界线 / 写一章（小说页）
- **做**：接 `/thread/create` 新建线；「写下一章」用 `/narrate/run`（配 provider 一键写→审→落）或「取写作包→回填→`/narrate/commit`」人在环流程，替换 `actWriteChapter()→window.open('/legacy')`。
- **验收**：新 UI 给一条线落一章并看到字数/质检回执；不跳 legacy。

### T2.3 新建 / 编辑角色（角色页 & 陪伴页）
- **做**：「新建角色」接 `/entity/create`（AI 走 `/gen/entity`）；右栏/陪伴页「资料」从 `window.open('/legacy')` 改为站内查看 + 基础编辑（名称/role/profile/appearance）。
- **验收**：新 UI 建角色、改基础字段并落盘；不跳 legacy。

### T2.4 暗宇宙 · 跨世界（差异化，必须在新 UI）
- **做**：把"提取为魂 / 召唤进别的世界 / 世界互联"做全：`/extract`、`/summon-soul`（已部分接）、`/link`（世界互联）、化身对照视图。配合 §五 的「离别」场景。
- **验收**：能在新 UI 完成"把角色带出一个世界 → 召唤进另一个 → 看两边化身"，全程不跳 legacy。

### T2.5 资源 · 导入 / 导出 / 融合
- **做**：导入角色卡/世界书/预设/正则（`/import/card`(-world)/`/import/preset`/`/import/regex`）+ 撤销导入（`/import/undo`）；导出全书（`/export/thread`，md，EPUB 后续）；世界融合（`/world/merge`）。归到「资源」/作品页。
- **验收**：导入一张 ST 卡、导出一本书、融合两个世界都在新 UI 完成。

### T2.6 质量 · 反思
- **做**：反思报告（`/narrate/reflect`）+ 全书质检（`/checks`，已接）以可读视图呈现到小说页/作品页。
- **验收**：能在新 UI 跑反思并看到 findings/overdue；不跳 legacy。

### T2.7 元件 / 素材
- **做**：素材库接 `/codex`、`/codex/create`、`/codex/seed`、`/delete/codex`——浏览/新建/编辑/灌种元件，替换"元件详情在 legacy 更完整"。
- **验收**：元件全生命周期在素材库内完成。

### T2.8 设置 · 数据管理
- **做**：设置页补上数据管理（导入/导出/备份提示、provider 配置已在），把"完整数据管理在 legacy"那段替换为站内可达。
- **验收**：常规设置与数据动作不跳 legacy。

### T2.9 legacy 退出用户导航（收口总检）
- **做**：T2.1–T2.8 覆盖后，把 legacy 从用户导航/各页"去控制台…"全部撤掉，仅在设置页留一个明确的「开发者 / 底层控制台」入口。
- **验收**：`grep -rn legacy sv/web/index.html`（及拆出的模块）只剩**那一个开发者入口**；常规用户闭环（建世界→建角色→写/玩→沉淀→跨世界→导出）全程在新 UI 内完成。

---

## Phase 3 · 露出"待接入"的引擎能力

### T3.1 Desire 层只读投影端点 + 前端接上
- **做**：后端加 `GET /api/drives/<wid>/<eid>`——只读投影出角色"此刻最想做的 N 件事"。**先用已有信号拼**（`anchors` + 最近经历/目标，参考 `lenses.py` 里 `desire_hint`），不调模型、0 token；前端把陪伴页/右栏那条"待接入"换成真数据。
- **约束**：是**投影**不是新存储；引擎其他部分不动。
- **验收**：陪伴页"当前驱动"显示来自接口的真实条目；断网/无数据时优雅兜底。

### T3.2 真封面（接 render 管线）
- **做**：作品/角色封面从 CSS 渐变占位，改为可选调用 `/render/*` 生成并落盘、页面引用真图；未配 `SV_RENDER` 时回退到现在的渐变占位（不报错）。
- **验收**：配了出图后端时作品卡显示真实封面；没配时与现状一致。

---

## Phase 4 · 顺手的加固（防御性，低优先）

### T4.1 路径 id 加固
- **做**：`World.load` / `LocalEntity.load`（及同类）对 id 套 `util.safe_name`，挡住 POST body 里的 `../` 之类。localhost 单机风险低，但属一次性防御。
- **验收**：构造 `{"world":"../x"}` 的 POST 不会写/读到 `WORLDS_DIR` 之外；正常 id 不受影响；测试仍绿。

### T4.2 内联事件 → 数据属性（可选）
- **做**：`charcard` 等把 id 拼进 `onclick` 的地方，改用 `data-*` + 事件委托，免 id 含特殊字符时断属性。
- **验收**：点卡片行为不变；源码无 `onclick="...${id}..."` 直插。

---

## 总验收（Definition of Done）

- `python -m sim.run_tests` = 39/39 全绿。
- 新前端外观/交互无回归；`/legacy` 仍可用。
- 无新依赖、无构建步骤；新增静态服务防穿越。
- 常规创作闭环可在新 UI 内完成（Phase 2 后）。
- 每个 T 一个 commit，标题含任务号。

> 实施完成后，请把"每个任务做了什么 + 自测结果"列一份交接，我按本文件逐条审查。
