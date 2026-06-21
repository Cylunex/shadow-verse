# 竞品项目档案库 · 总索引

> `F:/Project/projects/Tavern` 下 20 个类酒馆/RP/小说项目 + 2 个 ST JSON 资源的完整解析存档。
> 存档 2026-06-18 · 对照 shadow-verse(零依赖 Python 暗宇宙引擎,32模块/50 MCP工具/26测试)。
> 高层借鉴路线图见 [`../../BORROW-ROADMAP.md`](../../BORROW-ROADMAP.md);本目录是逐项目的深度档案。
> 状态标注:✅已吸收 · 🔵仍可借 · ⚪以后可能用。

---

## 全项目一览

| 项目 | 定位 | 技术栈 | 最高价值一条 | 档案 |
|---|---|---|---|---|
| **Luker** | ST 生产化 fork | Node/Express 593 文件 | Skills(Anthropic 兼容)+24 中文RP写作skill;Memory Graph(PEDSA/NMF/FISTA/DPP) | [Luker.md](Luker.md) |
| **TauriTavern** | ST 套 Tauri,Rust 重写 | Rust 515 文件 | Agent=Workspace 编辑模型+Run Event Journal(可审计回滚) | [TauriTavern.md](TauriTavern.md) |
| **AI-Chat(Narratium)** | ST 现代化重写(停更) | Next.js+LangChain | 创作Agent:一句话→完整角色卡+世界书+四类世界书内容规范 | [AI-Chat-Narratium.md](AI-Chat-Narratium.md) |
| **LittleWhiteBox** | 巨型 ST 扩展 | 前端JS 1.3万行vector | 向量记忆 L0-L3+PPR图扩散 diffusion.js(向量记忆蓝图) | [LittleWhiteBox.md](LittleWhiteBox.md) |
| **Novel-Auto-Generator** | AI续写+txt转世界书 | 前端JS 1.9万行 | UnionFind 别名合并+LLM 输出归一化三件套 | [Novel-Auto-Generator.md](Novel-Auto-Generator.md) |
| **NikaForge** | 可视化AI游戏卡IDE | Bun/TS 3600行 | PNG 角色卡 chunk 纯字节读写(导出ST卡用) | [NikaForge.md](NikaForge.md) |
| **st-image-auto-generation** | 极简出图扩展 | 单文件JS 507行 | `<pic prompt>` 标签触发出图范式 | [st-image-auto-generation.md](st-image-auto-generation.md) |
| **infiplot** | 实时生成galgame | Next.js16 | Scene/Beat 分支图 schema(线分支)+五职能两阶段编排 | [infiplot.md](infiplot.md) |
| **infinite-canvas** | 画布工作台+本地Agent桥 | Next.js+canvas-agent | MCP↔SSE 桥(MCP 驱动网页)+Origin 锁定 | [infinite-canvas.md](infinite-canvas.md) |
| **Noema** | 桌面语音陪伴 | Electron monorepo | 通用 hook 插件协议+transformText 多消费端 | [Noema.md](Noema.md) |
| **Nika-Character-Studio** | 纯前端编卡器+mini酒馆 | 原生HTML 5.5万行 | 小说→世界书(章回检测+多编码)+Agent清单/peek/patch | [Nika-Character-Studio.md](Nika-Character-Studio.md) |
| **AI_NovelGenerator** | Python GUI小说生成器 | Python+langchain | 章节蓝图六元数据+角色状态树+一致性提示词 | [AI_NovelGenerator.md](AI_NovelGenerator.md) |
| **webnovel-writer** | Claude长篇连载插件 | skill+python | 题材Profile字段化(13题材阈值)+追读力钩型分类 | [webnovel-writer.md](webnovel-writer.md) |
| **ainovel-cli** | Go全自动长篇引擎 | Go | reflect规则化诊断diag+四维相关章节反查(零embedding召回) | [ainovel-cli.md](ainovel-cli.md) |
| **chinese-novelist-skill** | 中文写作工艺skill | 纯markdown | 钩13式/扩充6技法/对话/三层弧(大部分已进craft.py) | [chinese-novelist-skill.md](chinese-novelist-skill.md) |
| **interactive-novel** | 互动小说参与引擎 | 纯markdown | 蝴蝶效应分支数据模型+四层记忆+输出前自检 | [interactive-novel.md](interactive-novel.md) |
| **local-dream** | Android端侧SD | Kotlin+C++ QNN/MNN | 本地推理核子进程+SSE进度(未来本地出图范本) | [local-dream.md](local-dream.md) |
| **JS-Slash-Runner** | 酒馆iframe执行前端JS | Vue3 2.4万行 | HUD iframe 高度自适应5坑(已采纳进第2刀) | [JS-Slash-Runner.md](JS-Slash-Runner.md) |
| **MimirLink** | QQ/OneBot ST卡运行时 | Node+sqlite | 结构化消息头+意图路由+外部文件安全三件套 | [MimirLink.md](MimirLink.md) |
| **2个ST JSON** | 正则脚本+预设 | JSON | HUD主题继承范式+promptOnly两段后处理(已支持导入) | [_ST-json-samples.md](_ST-json-samples.md) |

---

## ✅ 已落地(2026-06-18 第二批吸收,33 套测试全绿)
第一/二档里零依赖可落地的 10 项**已全部实现**:① UnionFind别名合并+LLM归一化→`dedup.py` ② Skills格式+种子→`skills.py` ③ 外部文件安全三件套→`util`+importer ④ 输出前自检+一致性5校验→craft ⑤ 创作包(一句话→卡+四类世界书)→`forge.card_prep/worldbook_prep/gen_card` ⑥ Scene/Beat分支+蝴蝶效应→`branch.py` ⑦ reflect规则化诊断+四维章节反查→`checks.reflect_diagnose`+`thread.related_chapters` ⑧ 题材字段化+钩型分类+reviewer纪律→recipes+craft ⑨ 结构化消息头+意图路由→`group.analyze_focus` ⑪ Run Event Journal→`journal.py`+narrate_run。
**剩余(较重/规模驱动,未做)**:⑩ infinite-canvas MCP↔SSE桥(需Python SSE+前端) ⑫ 章节蓝图/角色状态树+小说→世界书对接知轩藏书(基建已就位) ⑬ TauriTavern完整Agent workspace化 · 第三档向量记忆(规模驱动)。

## 🔵 原「仍可借」清单(↑上方标注已落地的项)

### 第一档(最高 ROI,纯算法/纯文本,零依赖可直接落地)
1. **UnionFind 别名合并 + LLM 输出归一化三件套**(Novel-Auto-Generator)→ 实体/记忆去重。纯算法,Python ~30 行。**P0**
2. **Luker Skills 格式(Anthropic 兼容)+ 24 个中文 RP 写作 skill 内容** → narrate 工艺库。纯文本零依赖直接移植。**P0**
3. **MimirLink 外部文件安全三件套**(路径遍历/JSON 体积上限/日志脱敏)→ 导入器。即使单机也该做。**P0**
4. **interactive-novel 输出前强制自检清单**(6 项)→ 增补 craft.PLAY_PROTOCOL。纯提示词零成本。**P0**

### 第二档(填补 shadow-verse 明确空白,需设计)
5. **Narratium 创作 Agent + 四类世界书内容规范** → 填补「只能导入不能从零生成卡/世界书」空白。**高**
6. **infiplot Scene/Beat 分支图 schema** → 线分支 backlog 的现成数据模型。**高**
7. **ainovel-cli reflect 规则化诊断 diag + 四维相关章节反查** → reflect 升级 + 向量记忆零依赖先行版。**高**
8. **webnovel-writer 题材 Profile 字段化(13 题材实证阈值)+ reviewer 逐维只给证据** → recipes 字段化 + 审校纪律。**高**
9. **MimirLink 结构化消息头 + current-message-focus 意图路由层** → 群聊「真人多说话人→线性上下文」适配(纯函数零依赖,即使不接 QQ 也能用于单角色应对多用户)。**高**
10. **infinite-canvas MCP↔SSE 桥 + Origin 锁定** → 把已有 MCP(50工具)与网页控制台打通成「MCP 直接操控网页」。**中高**
11. **TauriTavern Run Event Journal(JSONL append-only)+ Agent 工具循环护栏** → narrate 升级为可审计可回滚 workspace。**中高**
12. **AI_NovelGenerator 章节蓝图六元数据 + 角色状态树**;**Nika/Novel-Auto 小说→世界书(章回+多编码)** → narrate 字段 + 对接知轩藏书 7815 本。**中**

### 第三档(向量记忆专题,规模驱动才上)
13. **LittleWhiteBox L0-L3 分层记忆 + L0 抽取 prompt** → memory.py 升级蓝图(P0 级蓝图,但落地是规模驱动)。
14. **LittleWhiteBox PPR 图扩散 diffusion.js + Dense/Lexical/RRF/MMR 混合召回** → 向量记忆完整算法(论文现成,numpy ~200 行)。
15. **Luker Memory Graph(PEDSA/NMF/FISTA/DPP 认知层)** → 检索质量天花板(遇召回过度集中/欠覆盖时)。

---

## ✅ 已吸收(如实标注,不重复造轮子)
- 世界书运行时触发引擎(关键词/selective/递归/position@D 分桶/probability/互斥组 + **sticky/cooldown/delay 时效**)—— 比 Narratium/AI-Chat 更全
- swipe 一楼多候选(Nika 仅截断重发雏形,shadow-verse 更强)
- 变量三段式 data/rules/meta + validate 护栏(MimirLink 仅扁平 LLM 自算账,shadow-verse 更强)
- HUD sandbox iframe(+JS-Slash-Runner 的 5 个高度自适应坑已采纳加固)
- 立绘表情切换(Noema emotionTag→ExpressionFrame 同构)
- 群聊发言人选择、preset 组装 promptkit、内联宏 getvar/roll、AI 建变量卡
- jsonloose 容错(可对照 Novel-Auto parserService 补 repairJsonUnescapedQuotes/getMissingJsonClosers)
- ST 卡 V1/V2/V3+世界书+预设+正则导入、中文写作工艺库(chinese-novelist-skill+stylestat 已进 craft.py/checks.py)、网页绑 127.0.0.1(可补 Origin 白名单)

---

## ⚪ 以后可能用(归档,暂不做)
- 本地/离线出图后端(local-dream 推理核子进程+SSE 范本)
- 导出标准 ST PNG 角色卡(NikaForge pngHelper.ts)
- 多端并发写护栏(Luker integrity UUID)、OAuth 多用户托管、WS 流断点续传
- React Flow / SVG 分支树可视化、对话分支树
- IM(QQ/OneBot)接入(独立适配器,经 MCP 调引擎)
- 生产级 Agent runtime(TauriTavern Agent 文档体系作蓝图)

---

## 零依赖红线(全程守)
不引入 js-yaml/tokenizer/向量库/React/Express/Electron/Rust;HUD 沙箱 `allow-scripts` 但**绝不 allow-same-origin**;embedding 接口保持可插拔本地;重型外壳(Next.js/Vue/Tauri/monorepo)一律只借思路不移植代码。
