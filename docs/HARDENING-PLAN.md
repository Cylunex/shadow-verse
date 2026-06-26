# 加固计划 · 护栏 / 结构债 / 已知 bug / 文档对齐（交付 code 实施 / 审查依据）

> 缘起：CREATION-PLAN（C1–C4）与 FRONTEND-PLAN（T2.4/T3.1/T3.2）已落地后的一次全项目体检。本文只收**可代码化**的加固项；战略层（让一个作品真的活一次）不在此，见末尾「§五 范围外」。
> 定位：plan-level 工单，schema/实现细节留给 code。
> 总硬约束：① 不改引擎业务逻辑（除 §三 明确的 bug 修复）；② 全程测试常绿（以 `python -m sim.run_tests` 实际数为准，现 41 套）；③ 零依赖、零构建；④ 一任务一 commit，标题含任务号。

---

## 一、Tier 1 · 质量护栏空洞（补测试，最该先做）

有真实逻辑、却**零专测**的模块。按价值排：

### H1.1 `mcp_server` 契约测试（排第一 —— OpenClaw 路线的命脉）
- **做**：新增 `sim/test_mcp_server.py`，至少锁三件：① `tools/list` 返回的每个工具 `inputSchema` 合法、`required` ⊆ properties、名称无重复；② 选 3–4 个代表性工具做 `tools/call` round-trip（`codex_seed` 无参 / 一个 `*_prep` 取包 / 一个带 `payload` 的 `*_commit`），验证 argv 映射、payload 注入、回执结构；③ 未知工具 / 缺必填参数 → 返回结构化 `isError`，不崩。
- **验收**：OpenClaw 接入前，mcp_server 的工具面有回归护栏；改 `TOOLS` 漏字段会被测出。

### H1.2 差异化 / 常用功能补专测
- **做**：补 `test_convert`（一稿多吃：chat→小说 / 章→cyoa / beats→剧本，各跑一条断言产物结构）、`test_macros`（`{{roll::NdM}}` 骰子 + getvar 内联宏）、`test_merge`（世界融合：角色/线/设定并入、不丢数据）、`test_provenance`（谱系盖章/血统链）、`test_export`（全书导出 md 结构）。
- **验收**：这 5 个模块各有一套最小回归；`run_tests` 数随之上升、全绿。
- **优先级**：`convert`（差异化）>`merge`（暗宇宙铺路）>`macros`/`export`/`provenance`。

> 注：`thread`/`entity`/`recipes` 等核心模块虽无**专**测，但被大量集成测试间接覆盖，本轮不强求补；若顺手可加。

---

## 二、Tier 2 · 结构债：拆 `webapp.py`

- **现状**：`sv/webapp.py` 已 **1053 行**，是全项目最大文件（>`skill_api` 683 / `chat` 680），违背 FRONTEND-PLAN 自定的「webapp.py 薄路由」原则——Phase 2 迁功能 + C3 组件 CRUD + render 端点把它堆胖了。
- **做**：照当初拆前端 JS（T1.3）的成功经验，把路由按域拆成 `sv/web_routes/`（或 `sv/routes/`）模块：如 `works / chat / companion / novel / components / render / import / soul / settings`，`webapp.py` 退回**薄分发器 + 静态服务 + 启动**。
- **约束**：**纯搬运、零行为变化**（同 T1.3 纪律）；所有现有端点路径/返回逐一不变；安全写法（`/static`、`/img` 的防穿越）保留。
- **验收**：`test_webproj`/`test_manage` 等仍绿；逐条核对端点无回归；`webapp.py` 回到几百行以内。

---

## 三、Tier 3 · 已知 bug：删世界不清孤儿魂

- **实锤**：`nexus.purge_world` 只清旧 `NexusEntity` 树（连接 + 化身目录），**完全没碰新的 `universe/souls/`**。删一个世界 → 它升格过的魂成孤儿泄漏（CHAOS-TAVERN §五.3 早标，仍在）。
- **做**：在删世界的清理路径里补魂的处置——扫该世界中带 `soul_id` 的实体；把本世界从对应魂的化身指针/索引里摘掉；**若某魂再无任何化身**，按策略处置（默认**清理孤儿魂目录**避免泄漏；或标 dormant 待回收——策略由 code 定并写注释）。
- **约束**：只动删除清理路径；不碰魂的正常读写；保持「魂 opt-in、普通角色字节等价」。
- **验收**：新增断言（并入 `test_soul` 或 `test_ascension`）——建世界→升格魂→删世界→`universe/souls/` 无孤儿残留；魂仍有其它化身时**不**误删。

---

## 四、Tier 4 · 文档对齐（单一事实源回真）

- **现状漂移**：README/ARCHITECTURE 写「35 套 / 37 模块 / 59 MCP」；CHAOS-TAVERN 写「39/39」；**本批新 plan（CREATION/OPENCLAW）也已 stale（写 39/39，现 41）**。号称单一事实源却互相打架。
- **做**：① 把 README/ARCHITECTURE/VISION-MAP/CHAOS-TAVERN 里**写死的计数**改成当前真实值，或更好——改成「以 `python -m sim.run_tests` / `doctor` 实际输出为准」的活引用，**少写死数字**；② 可选：给 `skill_api doctor` 增一行权威计数（模块数/测试套数/MCP 工具数），让文档引用它而非各自硬写。
- **约束**：纯文档（+可选 doctor 一行），不碰引擎。
- **验收**：全仓 `grep "35 套\|37 模块\|39/39"` 不再有过时硬数字；新人读任一文档不会被旧数误导。

---

## 五、范围外（非代码，但更重要 —— 单独对待）

- **战略 #1：先让一个作品真的活一次。** REDESIGN 自己列的头号事项至今没做：能力已过剩，但「有没有一个值得回去见的角色」始终没正面回答（v1 沉船处）。**这不是写代码，是坐下来用最强模型 + 一套好预设把苏屿端到端跑几轮，只看"你还想不想接着看"。** 别让"再加固/再完善一轮系统"又盖过它。
- **backlog 减负**：`MCP↔SSE 桥` 已被 OpenClaw 方向化解（agent loop 即是），可从 ARCHITECTURE backlog **划掉**。
- **其余 backlog**（回溯 snapshot/rollback、PDF/EPUB、音频、向量记忆全量版、小说→世界书）保持规模/需求驱动，不在本轮。

---

## 六、建议落地顺序

1. **H1.1 mcp_server 契约测试**（接 OpenClaw 前必须，且最小）。
2. **H3 孤儿魂修复**（数据正确性，改动小）。
3. **H1.2 convert/merge/macros… 补测**（差异化优先）。
4. **H4 文档对齐**（顺手，低风险）。
5. **H2 webapp 拆分**（纯搬运、收益大但最费工，放后面整段做）。

> 实施完成后，请把「每项做了什么 + 自测结果（新增几套测试 / `run_tests` 现数）」列一份交接，按本文件逐条审查。
