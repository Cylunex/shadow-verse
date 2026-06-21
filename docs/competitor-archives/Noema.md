# Noema — 桌面 AI 陪伴（JARVIS 雏形）

> 存档 2026-06-18 · 对照 shadow-verse

## 定位
把「会说话、有性格、有记忆、能干活」的灵魂塞进桌面的 Electron 语音陪伴体,三层运行时(情感/工作/交互+输出)+通用插件 hook 系统。

## 技术栈 / 规模
外壳:Electron monorepo(pnpm+turbo),`packages/sdk`(纯 TS 运行时核)+`apps/desktop`(主进程/渲染层/Three.js 玻璃球 orb+Live2D)。能力栈:流式 ASR(Qwen)+VAD+Fish Audio S2 TTS;四模型槽(Dialogue/Task/TTS/ASR profile 切换);SQLite 记忆。SDK 20+ 子系统;role 仅 `eva.yaml`(55 行)。AGPL-3.0。

## 核心机制剖析

**1. role YAML 字段**(`personality-loader.ts:5`、`role/eva.yaml`):loadPersonalityFromFile 用 yaml.parse 读→validatePersonality 校验(name 必填、relationship.type∈companion/assistant/friend)。三块:character(name/personalityTraits[]/values[]/speakingStyle/behaviorRules[]/coreMemories[]/worldview)、relationship(type/**intimacy 0~1/trust 0~1/dynamic**,默认 0.5)、language。关系是**标量数值**——和 Doll「关系是原子」、暗宇宙变量卡同构。

**2. plugin.json hook 分类**(`plugins/index.ts:231` SDKPlugin)— ★AGENTS.md 明令「用通用 hook,不加插件专用 hook」:
- **context-provider 类**:resolveTaskContext(注入 skill/policy/memory/browser/mcp 上下文,PluginManager 带去重+配额裁剪 `:383`)、extendPrompt(按 phase=reply/task_progress/task_result 追加)。
- **tool 类**:registerTools/registerTaskRuntimes/wrapTaskLLM(LLM 中间件链式包裹)。
- **admin 类**:getAdminState/handleAdminAction。
- **transform/expression 类**:transformText(text,{target})(target=tts_input/display/memory/interrupted_assistant,reduce 链式)、selectExpression(情绪→表情帧)。
- 生命周期:onConversationTurn/onTask* 全 try/catch 不让单插件崩整链。
- 权限模型(`:12`):tools.register/filesystem/shell/network/browser.control/desktop.control/secrets/memory/admin.custom,manifest 声明 loader 注入。
- manifest 还声明 configSchema(六类字段带 i18n)+uiSurfaces(main-view/task-panel 槽位嵌 HTML)。

**3. sticker-expression 情绪贴图**(对立绘表情切换):LLM 每条回复产 emotionTag,`DialogueEngine.emitExpression()`(`dialogue/index.ts:895`)把 {phase,replyText,emotionTag} 喂 selectExpression(),插件返 ExpressionFrame `{type,id,emotion,assetPath,durationMs,priority}` 推渲染层切立绘。**文字情绪标签→表情资产路径的解耦层**:LLM 只吐 tag,映射在插件可换贴纸包。

**4. fish-s2-emotion 插件**(唯一落地样例,hook 范式活样本):只实现 extendPrompt(注 TTS 语音标记规则)+transformText(target=tts_input 归一标签进 TTS;其他 target **剥光标签**让展示/记忆看不到 TTS 控制标签)。**同一段文本对不同消费端(TTS/屏幕/记忆)走不同 transform**。

## 借鉴清单

| # | 借鉴点 | 对应能力 | 状态 | 移植 | 优先级 |
|---|---|---|---|---|---|
| 1 | **通用 hook 插件协议**(context-provider/tool/admin/transform/expression/lifecycle 全靠一组通用 hook) | 可插拔 LLM/render 有雏形,缺统一插件生命周期总线 | 🔵仍可借 | 仅思路(Python 重写 hook 注册表/去重/配额/try-catch 隔离) | 中 |
| 2 | transformText(target=tts/display/memory)同文本多消费端归一 | narrate+render+记忆写入 | 🔵仍可借 | 直接移植思路 | 中 |
| 3 | emotionTag→ExpressionFrame 解耦 | 已有立绘表情切换 | ✅已吸收(可对照其 priority/durationMs 补强) | 仅思路 | 低 |
| 4 | role YAML 关系标量(intimacy/trust 0~1) | 变量卡/长期记忆 | ✅已吸收 | 仅思路 | 低 |
| 5 | 四模型槽+编号 profile 切换 | 可插拔 LLM | 🔵仍可借(多 profile 命名约定) | 直接移植思路 | 低 |
| 6 | manifest configSchema 六类+i18n+uiSurfaces 槽位 | 控制台插件配置面板 | ⚪以后可能用 | 仅思路 | 低 |
| 7 | 三层运行时切分(情感层只接话不编故事事实) | narrate/群聊编排 | ⚪以后可能用 | 仅思路 | 低 |

## 不值得碰
Electron+Three.js orb+Live2D+monorepo(turbo/pnpm)重型桌面外壳违背零依赖(仅「桌面常驻陪伴」形态本身作灵感);语音管线(ASR/VAD/Fish S2)依赖云服务+大量 npm。

## 存档备忘(以后可能用)
- hook 接口全表 `plugins/index.ts:231-255` 是设计 Python 插件协议的现成清单。
- `PluginManager.resolveTaskContextInjections`(`:383`)「去重 key=type:path|id|name + 配额递减」是上下文注入器好模板。
