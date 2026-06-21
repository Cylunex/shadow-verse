# Luker — SillyTavern 生产化 fork

> 存档 2026-06-18 · 对照 shadow-verse 零依赖 Python 暗宇宙引擎

## 定位
SillyTavern 的「生产级硬化」下游 fork：把酒馆从前端单机玩具改造成「后端拥有生成生命周期 + 增量持久化 + 强插件生态 + 内置多智能体/图记忆」的可托管平台，严守上游兼容。

## 技术栈 / 规模
Node.js/Express 服务端 + 原生 JS 前端(沿用 ST `public/scripts`)。约 **593 个 JS 文件**；含 Android(WebView 跑 127.0.0.1)/Docker/Colab/Electron 多形态;完整 VitePress 文档站(中英繁三语)。AGPL-3.0。**重依赖,价值在设计与算法不在代码移植**。

## 核心机制剖析

**1. 增量同步 + integrity 并发护栏**(`docs/improvements/incremental-sync.md`/`backend-storage.md`)
- `append`(O(1) 追加到 jsonl 尾,末条去重防重试重复)/`patch`(行级补丁,幂等跳过已应用)/`patch-metadata`(deep merge)。
- **integrity UUID**:每次写后生成新 UUID 存独立 `{chat}.luker-state.chat_sync.json`(与聊天文件分离);前端写请求带 UUID,不匹配返 **409 Conflict** → 拉取最新重试。解决多 tab/多设备并发覆盖。
- Generation Acknowledge:落盘后才返回响应,前端崩溃不丢数据。

**2. 状态系统 + Floor State**(`docs/features/state-system.md`)
- character/chat/preset 三宿主可挂 namespace 隔离状态文件,随宿主重命名/删除联动,插件不用管 IO。
- **Floor State**:写入按 floor index + swipe id 记录,聊天结构变化(swipe/删/切)时**自动重放**,插件状态自动跟随当前 swipe 路径,免手动 reconcile。

**3. Memory Graph 图记忆**(`docs/features/memory-graph.md`)— ★全档最有料
- 结构:语义层节点(character_sheet/location_state,可合并)+ 事件层节点(event,永不合并)。schema 可定制,每类型带「Extraction Instructions」+「Extract Every N Floors」节流。
- **召回 8 阶段混合管线**:向量预筛→实体锚定→构 seeds→两层邻接表→**PEDSA 图扩散**(Personalized Efficient Diffusion,能量沿边多轮传播+teleport,PageRank式,找间接关联)→混合打分(向量+扩散能量+词法+锚点+recency)→**认知层 NMF/FISTA/DPP**(NMF 主题再平衡补欠表示/FISTA 残差发现未覆盖方向/DPP 行列式点过程选高质量且互相多样的子集,避免召回过度集中)→可选 rerank。
- 注入两通道:persistent(常驻,世界律)vs recall(动态)。底层都**投影成世界书条目**复用关键词扫描/depth 排序。
- 编辑/删/swipe 时完整回滚记忆;同楼层 swipe 复用上次召回省 LLM;向量增量更新(hash 比对只重嵌变更节点)。

**4. Orchestrator 多智能体编排**(`docs/features/orchestrator/`)
- 主回复前派小队跑工作流,把保持人设/回忆/守规则/规划/写文字拆给不同 agent,打包成 capsule 注入主 prompt。**5 模式**:Spec(固定 DAG)/Single/Agenda(Planner 动态派发)/**Loop**(单 agent 多轮调工具直到 finalize,单 preset 全程、prompt cache 命中高、上下文连续)/**Director**(主+子 agent 直接写正文,长篇高质量 RP,内置 24 skill)。
- capsule 绑触发它的 user-floor,同楼层 swipe 复用;配置可绑角色卡随卡导出;节点级 model/preset override(贵模型主聊、Haiku 编排省 70%+)。

**5. Skills 知识包**(`docs/features/skills/`、`src/skills/*.js`)— ★
- **与 Anthropic Claude Skills 格式完全兼容**(SKILL.md + YAML frontmatter + references/examples/assets),与 Claude Code skill **双向无损 round-trip**。
- 三 scope + later-wins:`global < preset < character`(角色卡加载时同名覆盖,切卡复原);引用只按 name(无 scope 前缀),跨 scope 移动不破引用。
- preset skill 打进 preset JSON、character skill 打进卡 PNG metadata——发卡即发其写作规则。
- 运行时:按 policy 过滤物理清单 → 注入 `<available_skills>` 短目录 → 给 skill_list/read/search 三工具。`frontmatter-parser.js`/`scope.js`(黑名单防路径穿越、允许 CJK)零依赖可照搬。
- 内置 **24 个 director 中文 RP 写作 skill**:`director-anti-cliche-zh`("data-person prose" 失败模式 + 冷观察动词族/数据词汇/契约词族/升华套话黑名单)、`director-character-voice-zh`、`event-summary-rules-zh` 等。

**6. 其它生产化基建**:Unified Generation Layer(多后端统一 token 计量/SSE 解析/错误归一)、Function Call plain-text 模式(不支持原生 FC 的模型,system prompt 注协议+正则抽取)、Preset Decoupling(连接 vs 生成参数按 isConnection 拆)、Card-Bound preset 自动剥离连接字段、WS Proxy(单次票据握手绕过浏览器 WS 不能设 header)。

## 借鉴清单

| # | 借鉴点 | 对应能力 | 状态 | 移植 | 优先级 |
|---|---|---|---|---|---|
| 1 | Skills 格式(Anthropic 兼容+三scope+name引用+随卡分发) | narrate 工艺库+AI建卡 | 🔵仍可借 | **直接移植格式**(纯文本,scope.js/frontmatter-parser.js 零依赖) | 高 |
| 2 | 24 个 director 中文 RP 写作 skill | 中文写作工艺库/narrate审改 | 🔵仍可借 | **直接移植内容**(纯 md 规则) | 高 |
| 3 | Memory Graph 召回(PEDSA 扩散+NMF/FISTA/DPP 认知层) | memory.py(线性加权,无图扩散/去重) | 🔵仍可借 | 仅思路(纯 Python 可实现,工程量大) | 高 |
| 4 | 记忆双层+类型可定制 schema+每类型抽取节流+persistent/recall 互斥注入 | memory.py+变量三段式 | 🔵仍可借 | 仅思路 | 高 |
| 5 | 记忆投影成世界书条目(统一注入底座) | 世界书引擎+memory.py | ⚪以后可能用 | 仅思路 | 中 |
| 6 | Orchestrator 5 模式(尤其 Loop/Director/capsule 绑楼层) | narrate 产线 | 🔵仍可借 | 仅思路 | 中 |
| 7 | Floor State 自动重放(写入按 floor+swipe,结构变化自动 reconcile) | swipe+变量三段式 | 🔵仍可借 | 仅思路(swipe 后变量自动跟随候选路径) | 中 |
| 8 | Function Call plain-text 模式 | 可插拔 LLM+内联宏 | 🔵仍可借 | 直接移植(纯文本协议+正则) | 中 |
| 9 | integrity UUID 并发护栏+增量 append/patch | 扮演页/变量持久化 | ⚪以后可能用 | 仅思路(多端并发写时) | 低 |
| 10 | Preset Decoupling(isConnection 分类)/Unified Generation Layer | 已有 preset/可插拔 LLM | ✅部分已吸收 | 仅思路 | 低 |

## 不值得碰
Express 全套端点+npm 依赖、Electron/Android WebView 壳、OAuth/配额/多用户托管、WS Proxy 票据握手(解决浏览器 WS header 限制,shadow-verse 无此问题)、向量后端集成(依赖外部 embedding)。Node 生产托管专属,违背零依赖。

## 存档备忘(以后可能用)
- OAuth(GitHub/Discord)+存储配额多用户:若做共享部署时的现成参考。
- WS Proxy 流偏移断点续传:长文本生成+不稳定网络场景。
- Request Inspector:调试「发了什么给 API」+token 全生命周期统计。
- 自动 schema 迁移管线(幂等、失败不改原数据):记忆/变量格式升级范式。
- **PEDSA/NMF/FISTA/DPP** 四算法名是检索质量天花板关键词,memory.py 检索遇「召回过度集中/欠覆盖」瓶颈时按此查论文。
