# MimirLink — QQ/OneBot 场景的 ST 卡运行时

> 存档 2026-06-18 · 对照 shadow-verse · 引擎核心更弱,但 IM 多说话人适配范式稀缺

## 定位
把 SillyTavern 角色卡运行时**服务端化**并嫁接到 QQ/OneBot IM 的 Node.js 守护进程。与 shadow-verse 同源异构(都做「ST卡运行时+记忆+变量+预设+MCP」),但**透镜押在 IM 多人群聊**、且**重依赖**(better-sqlite3/express/ws/@modelcontextprotocol/sdk)。`routes.js` 337K 行+`index.js` 150K 行是单文件巨石反面教材。

## 技术栈 / 架构
Node≥22.5 ESM。分层:接入(onebot.js WS/HTTP)→标准化(standard-event.js OneBot→StandardEvent)+意图路由(current-message-focus.js)→调度(runtime.js 去重+缓冲+每会话串行+信号量并发)→编排(prompt.js 预设分区+世界书+记忆+trace,ai.js LLM+工具循环)→存储(session.js 单一 SQLite,记忆/变量/摘要/知识/档案全在 memory_entries 一张表)→桥接(variable-bridge/regex/worldbook/character)→外部(mcp.js 27 工具,security.js 反注入)。

## 核心机制剖析(引擎核心比 shadow-verse 更弱)
- **长期记忆**:纯 SQLite 关键词加权召回(无向量,理念同 memory.py,但摘要靠 LLM 非确定)。命名空间四元组 `(scope_type,scope_key,character,preset)` 隔离 + 一张表多 entry_type(variable/knowledge/profile/note)。recallMemory 确定性加权打分,每条带 recallReason(可解释)。
- **变量桥接**:**扁平 key-value,无 rules/meta 分层**,结算靠 LLM 在 `<UpdateVariable>` 里自己算 **JSONPatch**(op/path/value)。stat_data 前缀归一化兼容各种 ST 路径写法。**shadow-verse 的 rules 结算引擎反而更强,别倒退。**
- **预设**:injection_position/depth 四象限分区(preSystem/historyInjection/postHistory/assistantPrefill);多层来源优先级链;message trace 标来源。
- **MCP 27 工具**(`range_*` 前缀,定位「调教靶场」非「运行时」):range_test(伪造记忆测试)、range_analyze(质量评分)、range_get/update_character_card(写 PNG tEXt)、range_validate_worldbook/fix_format、range_batch_set_prompts、**range_trace_output(来源追踪)**。

## ★真正稀缺、值得吸收的(面向真人多说话人 IM)

| # | 借鉴点 | 对应能力 | 状态 | 移植 | 优先级 |
|---|---|---|---|---|---|
| 1 | **结构化消息头** `[群聊\|QQ:123\|昵称:张三\|isAtBot:true\|...] 内容`——一行文本携带说话人身份/路由元数据,让单 LLM 在线性历史里分辨「谁在说/对谁说/是否@我」 | 群聊+用户身份 | 🔵仍可借 | 仅思路(格式直接抄) | 高 |
| 2 | **current-message-focus 意图路由层**(意图分类 poke/reply/call_out/topic_shift+回复目标决策+策略提示+warnings) | 护栏+群聊 | 🔵仍可借 | **直接移植**(纯函数零依赖,几乎照搬 Python) | 高 |
| 3 | **trusted/untrusted 上下文信封**(buildObservationEnvelope:trusted_context/untrusted_user_inputs/system_generated_memory,prompt 层告诉 LLM 只有用户消息不可信)+反注入 14 正则 | 护栏 | 🔵仍可借 | 直接移植(纯 prompt 范式) | 中 |
| 4 | **外部文件安全三件套**:路径遍历过滤(`../`)、JSON 体积上限(卡5MB/世界书10MB 防 parse 炸弹)、日志脱敏(password/apiKey/token) | 导入器(读外部 ST 卡) | 🔵仍可借 | 直接移植(**即使单机本地也该做**,因为导入不可信 ST 卡) | 高 |
| 5 | range_trace_output 来源追踪+range_analyze 质量评分 | 50 工具 MCP | 🔵仍可借 | 仅思路(补「输出可观测/质检」) | 中 |
| 6 | 命名空间四元组隔离+一张表多 entry_type | memory.py scope | 🔵仍可借 | 仅思路 | 中 |
| 7 | JSONPatch 变量结算协议+stat_data 前缀归一化 | 变量 data 层 | 🔵仍可借 | 直接移植(协议+归一化) | 中 |

## IM(QQ/OneBot)接入是否值得做?
**值得作为未来独立可选适配器,不进核心、不破坏零依赖。** 理由:① 战略契合(暗宇宙角色在 QQ 群 RP,呼应 Doll 陪伴);② 真正有价值的是「把多人真人对话压成单角色可消费的线性上下文」的适配层(消息头+意图路由,纯函数零依赖,**即使不接 QQ 也能用于「单角色应对多用户」**);③ OneBot 接入需 WebSocket(Python 标准库无原生 ws),**正确做法是做成引擎外的独立薄适配进程,经 shadow-verse 零依赖 MCP 调引擎**,而非把 ws 塞进核心。

## 不值得碰
better-sqlite3/express/ws/multer 重依赖、337K/150K 行巨石文件、19.8K 行 vanilla SPA、OneBot WS 客户端本身、LLM 自算变量账(因放弃脚本运行时的妥协,shadow-verse rules 结算更强)、ELO 调教靶场。

## 存档备忘(以后可能用)
- IM 接入做成独立 MCP 客户端适配器时,`standard-event.js`+`current-message-focus.js` 是「真人多说话人→线性上下文」的现成纯函数实现。
- SECURITY_FIXES.md 的外部文件安全三件套即使本地单机也值得做。
