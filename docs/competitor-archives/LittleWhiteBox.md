# LittleWhiteBox（小白盒）— 巨型 ST 扩展（向量记忆金矿）

> 存档 2026-06-18 · 对照 shadow-verse · **vector 子系统 = shadow-verse「向量记忆 backlog」的完整生产级蓝图**

## 定位
面向 SillyTavern 的巨型多功能扩展,最大价值是一套生产级「叙事长期记忆 RAG 引擎」(L0-L3 锚点 + Dense/Lexical/RRF/MMR/PPR 图扩散),外加可视化出图 scene-planner、Agent 助手、变量系统、iframe 渲染、电子书。

## 技术栈 / 规模
纯前端 ESM JS(ST 扩展);IndexedDB(Dexie)向量持久化;Web Worker 打分卸载;外部 Embedding(硅基流动 BGE-M3 1024维)+ Reranker(bge-reranker-v2-m3);jieba-wasm 中文分词。manifest 2.6.3,作者 biex。仅 `story-summary/vector/` 一个子系统就 ~13,100 行(recall.js 1664、diffusion.js 959)。

## 核心机制剖析(vector 子系统)

**1. 五层存储 L0-L3**(`vector/storage/state-store.js`、`atom-extraction.js`)
- **L0=StateAtom(场景锚点)**:每楼 LLM 抽 1-2 个「60-100字场景摘要+关系三元组」。schema `{atomId, floor, scene/semantic(自然语言), edges:[{s施事,t受事,r互动}], where}`。依据(`atom-extraction.js:1-9`):BGE-M3 检索精度最高→semantic 用纯自然语言;TransE→s/t/r 方向性三元组。
- L0 抽取 prompt 极讲究(`:43-95`):强制「高召回场景卡片」非「好看概括」,禁抽象同义词改写(昵称/道具/暗号/羞辱动作保原词),禁空泛("关系升温"),r 用「动作+对象」短语(6-12字)。
- 存储分离:StateAtom 存 chat_metadata(可导出),StateVector 存 IndexedDB(可从 atom 重建);state-store.js 用 dirty-flag+防抖+快慢重试解决 ST metadata 保存竞态。
- L1=Chunk(~200token/块,中文 1字≈1token);L2=Event(带 `(#X-Y)` 楼层范围+因果链);L3=Fact。

**2. 召回主管线 9 阶段**(`vector/retrieval/recall.js`,1664 行,头部 `:15-26` 是文档)
①Query Build(取最后3条对齐 L0)②R1 Dense(切多段 batch embed 后**加权平均**,focus 段 clampMinNormalizedWeight 保底防长上下文稀释焦点)③Query Refinement(用 R1 命中产 hints)④R2 Dense⑤Lexical+Dense-Gated Event Merge(词法召回事件但合并前验 dense≥0.60)⑥**Floor W-RRF Fusion**(floor 粒度融合 dense/lexical 排名,`score=wD/(k+rank_d)+wL/(k+rank_l)`,k=60/wD=1.0/wL=0.9,+must-keep floors 护栏)+Rerank+L1 配对⑦L1 配对组装⑦.5 **PPR Diffusion**⑧L0→L2 反查⑨Causation Trace(因果链,深度≤10)。
- **MMR**(`:237`):候选100→选50,λ=0.72;Entity Bypass(精确命中 sim≥0.70 放行)。

**3. PPR 图扩散 diffusion.js**(959 行)— ★整个调研技术含量最高的单点
把「同角色/同地点但语义距离远」的记忆通过图结构捞回。`:1-31` 列 7 篇论文引用(Page 1998/Haveliwala 2003/GraftNet 2018…)并声明与 NetworkX `pagerank_alg.py` 对齐。
- 建图(`:266`):对全体 L0 建无向加权图。候选边由 WHAT 通道(互动 pair 倒排索引,方向不敏感)+ R 语义通道(edges.r 向量 top-k,sim≥0.62);WHO/WHERE 仅 reweight 不产边。floor 窗口≤80 内枚举防 O(N²)。
- 边权(`:374`):`0.40·WHAT(Overlap系数)+0.40·rSem+0.10·WHO(jaccard)+0.05·WHERE+0.05·time`。WHAT 用 Overlap 而非 Jaccard(小集合避免过度惩罚)。
- 种子向量(`:439`):seeds 按 rerankScore 加权 L1 归一(Haveliwala topic-sensitive)。
- Power Iteration(`:525`):α=0.15 重启,ε=1e-5,max 50 轮(通常 15-25 收敛),悬挂节点质量重分配到个性化向量。
- 后验门控(`:608`):非种子节点 cosine(query,state)≥0.46,`finalScore=PPR_norm×cosine≥0.10`(CombMNZ:图结构相关×语义相关双满足),top-100 截断。

**4. 出图 scene-planner**(`modules/draw/shared/scene-planner.js`,550 行):LLM 读世界书+角色卡+最近消息→输出 **YAML** 多图任务,每图 scene+characters[{name/danbooru/costume/action/interact/uc/center}]。costume 让 LLM 按剧情改写(破损/敞开/湿透)。providers 支持 comfyui/novelai/sd-webui。

## 借鉴清单

| # | 借鉴点 | 对应能力 | 状态 | 移植 | 优先级 |
|---|---|---|---|---|---|
| 1 | **L0-L3 分层存储**(场景锚点+三元组/Chunk/Event/Fact) | memory.py(扁平) | 🔵仍可借 重点 | 仅思路(Python 重写,蓝图) | P0 |
| 2 | **L0 抽取 prompt 工程**(高召回场景卡片、禁抽象、r 动作模板、保原词) | 记忆抽取/工艺库 | 🔵仍可借 | **直接移植 prompt 文本** | P0 |
| 3 | Dense+Lexical 混合召回+W-RRF 融合 | 向量召回(bigram 单路) | ⚪以后可能用 | 仅思路(RRF 公式 ~30 行) | P1 |
| 4 | **PPR 图扩散 diffusion.js**(实体共现图+topic-sensitive PageRank+cosine 门控) | 「同角色但语义远」关联记忆,长篇人物线追踪 | ⚪以后可能用 单列存档 | 仅思路(纯算法,numpy 重写 ~200 行,论文现成) | P1 |
| 5 | MMR 多样性(λ=0.72)+Entity Bypass | 召回去冗余 | ⚪以后可能用 | 仅思路 | P2 |
| 6 | 加权平均 query+focus 保底(治长上下文稀释焦点) | 查询构造 | ⚪以后可能用 | 仅思路 | P2 |
| 7 | StateAtom 存 metadata + Vector 存 IndexedDB 的「持久化/可重建」分离 | memory 持久化 | 🔵仍可借 | 仅思路(锚点存档/向量缓存可重建) | P1 |
| 8 | scene-planner YAML 多图任务+costume 按剧情改写 | 立绘/出图 | ⚪以后可能用 | 仅思路 | P2 |

## 不值得碰
Agent 助手/assistant 子系统(自带 coding agent,重复造轮子,强耦合 ST/浏览器)、pixi/dexie/jieba-wasm/minisearch 浏览器库、变量系统/模板/TTS/电子书/第四面墙、硅基流动硬编码 embedding(要保持可插拔)。

## 存档备忘(以后可能用)
- **diffusion.js 整段算法**:PPR 实体图扩散是纯算法(不依赖 ST)。未来做「人物关系记忆图谱」直接照搬:建图(WHAT 倒排+R 语义 top-k)→topic-sensitive power iteration(α=0.15)→cosine×PPR 双门控。论文清单 `diffusion.js:20-30`。
- **metrics.js(828 行)**:召回可观测性指标体系,调向量参数时的评测框架。
- **stopwords-base.js(2231 行)/tokenizer.js(740 行)**:中文停用词表+分词,lexical 召回做中文的现成语料。
