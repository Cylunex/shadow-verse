# Novel-Auto-Generator — AI 续写 + txt 转世界书

> 存档 2026-06-18 · 对照 shadow-verse · UnionFind 别名合并 + LLM 输出归一化 = 纯算法金矿

## 定位
SillyTavern 扩展,双核:① AI 挂机自动续写长篇小说(断点续传/标签提取/多格式导出);② **TXT 转世界书**(整本 TXT→AI 提取角色/地点/组织→生成 ST 世界书,含章节分块/并行/别名 UnionFind 合并/JSON 容错)。

## 技术栈 / 规模
纯前端 ESM JS;高度模块化(txtToWorldbook ~90 文件,app/core/services/ui/infra 分层);IndexedDB;vitest 测试。manifest 1.8.1。根 index.js 60KB;txtToWorldbook ~19,000 行。

## 核心机制剖析(txt→世界书管线)

**1. 章节分块**(`txtToWorldbook/services/fileImportService.js:89-226`)— ★
切整本 TXT 成适合 LLM 单次处理的 chunk(默认 chunkSize,minChunkSize=max(chunkSize×0.3,5000)):
- 章节正则识别(`:94`):可配 chapterRegex 全局匹配,**带 5 秒超时熔断**(`:101` 防恶意正则)+空匹配防死循环(lastIndex++)。
- 章节装箱(`:124`):相邻小章合并(pendingChapter 累加近 chunkSize)。
- 超长章再切(`:154`):>chunkSize 按滑窗切,**优先段落 `\n\n` 断,其次句号 `。`(只在 >50% 位置认断点)**保语义完整。
- 无章节退化(`:204`)为纯长度滑窗(同样优先段落/句子边界);末尾小尾巴回填上一 chunk(`:192`)。

**2. 别名合并 UnionFind 管线**(`mergeService.js`,623 行)— ★最有料
解决「同一角色在不同章节抽成多条(全名/简称/昵称/代号)」:
- 候选粗筛(`findPotentialDuplicates:245`):三启发式任一命中即入嫌疑组——关键词集合有交集 / 名字互相包含 / checkShortNameMatch(取末2字或全名比对,`:234`)。
- 生成配对(`generatePairs:13`)组内两两配对。
- AI 精判(`verifyDuplicatesWithAI:329`):每对关键词+内容摘要(截300字)塞 prompt(`:368`),LLM 判 isSamePerson+选 mainName。**并发分批**(Semaphore 控并发,Promise.allSettled 容错单批,`:433`)。
- **LLM 输出归一三件套**(`:282-327`):`normalizeSameFlag`(把 true/"是"/"同一"/1 归一布尔)、`resolvePairIndex`(处理 LLM 返回 pair 编号错位/名字对不上号,全局/局部/双向匹配三重兜底)、`getAIResultsArray`(兼容 results/result/pairs/judgements 各种字段名)。
- **UnionFind**(`:23-64`):路径压缩+按秩合并;对 isSamePerson 的对 union;getGroups 返 size>1 连通分量。
- 主名选择(`:498`):优先 LLM 给的 mainName,否则取内容最长;合并去重关键词、内容用 `---` 拼接。

**3. JSON 容错四级管线**(`parserService.js`,279 行)— ★
`parseAIResponse`(`:235`)四级降级:①直接 parse(先 filterResponseContent 剥 `<thinking>`)②extractJsonCandidate(剥 ```json 围栏、中文引号→英文、删尾逗号、截首 `{` 到末 `}`)③parseLenientJson(`repairJsonUnescapedQuotes` 状态机逐字符判字符串内未转义 `"`,`:99` + `getMissingJsonClosers` 栈式补齐缺失 `}`/`]` 处理截断,`:179`)④正则兜底 `extractWorldbookDataByRegex`(`:23` 大括号配平逐 category/entry 抠「关键词」数组和「内容」)。

## 借鉴清单

| # | 借鉴点 | 对应能力 | 状态 | 移植 | 优先级 |
|---|---|---|---|---|---|
| 1 | **UnionFind 别名合并管线**(启发式粗筛→LLM 精判→并查集→主名选择) | 角色/实体管理、记忆去重 | 🔵仍可借 重点 | 仅思路(Python UnionFind ~30 行,启发式+prompt 可抄) | P0 |
| 2 | **LLM 输出归一化三件套**(normalizeSameFlag/resolvePairIndex/getAIResultsArray,容忍乱答字段名/编号错位/中文布尔) | 所有「LLM 返结构化结果」场景 | 🔵仍可借 高价值 | 直接移植思路 | P0 |
| 3 | JSON 容错四级(状态机修未转义引号/栈补截断括号/正则兜底) | **已有 jsonloose** | ✅已吸收(部分)/🔵仍可补 | 仅思路(`repairJsonUnescapedQuotes`/`getMissingJsonClosers` 两招可补强 jsonloose) | P1 |
| 4 | 章节分块(章节正则+超时熔断→小章合并→超长按段落/句子边界切→尾巴回填) | narrate/语料处理 | 🔵仍可借 | 仅思路(整理知轩藏书 7815 本时直接用) | P1 |
| 5 | 正则兜底抠 JSON(大括号配平+「下一非空白字符判字符串边界」) | jsonloose 极端兜底 | 🔵仍可补 | 仅思路 | P2 |
| 6 | 并发分批+Semaphore+Promise.allSettled 容错单批 | 批量 LLM 调用 | 🔵仍可借 | 仅思路 | P3 |

## 不值得碰
ui/ 层(~40 modal,纯 ST DOM)、挂机续写主循环+弹窗检测(强耦合 ST 事件,且 shadow-verse 有 narrate 产线)、memoryHistoryDB(IndexedDB)。

## 存档备忘(以后可能用)
- **mergeService.js 整段**:UnionFind 别名合并是 shadow-verse 实体/记忆去重的现成完整方案,强标记可移植。
- **parserService.js 整段**:作为 jsonloose 的「升级对照基线」,重点 `repairJsonUnescapedQuotes` 状态机 + `getMissingJsonClosers` 栈补齐(jsonloose 可能还没的招)。
