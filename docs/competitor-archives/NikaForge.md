# NikaForge（妮卡工坊）— 可视化 AI 游戏卡 IDE

> 存档 2026-06-18 · 对照 shadow-verse

## 定位
依附 SillyTavern 的「浏览器内可视化 AI 游戏卡 IDE」——左侧文件树/中间实时预览/右侧 AI 助手,让创作者「说人话」就能让 AI 改角色卡内嵌的全屏 HTML 游戏卡代码,一键物理打包回 PNG 角色卡。

## 技术栈 / 规模
前端单个 624KB `NikaForge.html`(全屏 iframe IDE)+ 薄 `index.js`(ST 扩展侧);后端 **Bun**(TS)本地服务 `server.ts`(628 行,带 Node polyfill 双模运行)。后端是「迷你 Claude Code」:ToolEngine+13 工具。后端 ~3,600 行 TS。manifest 1.0.0。依赖 LittleWhiteBox 变量管理。

## 核心机制剖析

**1. Bun 后端 + 双模 polyfill**(`server.ts:1-65`):用 `globalThis.Bun` 垫片把 Bun.file/write/serve 映射 Node fs/http,同一份代码 Bun 或纯 Node 都跑。自动探测 ST 端口(读 config.yaml),自愈式拷贝 stscript-reference.md 喂 AI 学 STscript。

**2. Agent ToolEngine + 13 工具**(`engine/ToolEngine.ts`、`tools/`):
- 文件系统级:Bash/FileRead/Edit/Write/Grep/Glob。
- **代码块级(核心)**:ReadCodeBlock(按字段名如 first_mes 读出展开后明文带行号,而非 JSON 转义串)/EditCodeBlock/WriteCodeBlock/GrepCodeBlock/CheckCodeBlock。**AI 不直接编辑 JSON 转义串,而是 CodeBlock 工具层「解封装→明文带行号→改→重封装」,避免在转义地狱改坏代码**。
- 角色卡级:CreateCharacterTool(生成 V3 全屏 HTML 交互卡模板)/InjectTemplateTool。

**3. PNG 角色卡读写**(`pngHelper.ts`,279 行)— ★纯字节级,无第三方 png 库:自实现 CRC32 表(`:4`);`extractDataFromPng`(`:44`)遍历 chunk 从 tEXt/iTXt 找 `chara`(V2 base64)或 `ccv3`(V3);embedDataInPng(removeCharaChunks 剥旧→createTextChunk 重写带 CRC,插 IEND 前)。保存配合清 ST 缓存「保存即生效不用重启」。

**4. 双重备份 + ST 联动**:启动时 Git 冷备份角色库 + 聊天内瞬时快照;反代 ST 的 /api/slash 跑 STscript、/api/chat/completions 复用酒馆当前 LLM 连接。

## 借鉴清单

| # | 借鉴点 | 对应能力 | 状态 | 移植 | 优先级 |
|---|---|---|---|---|---|
| 1 | CodeBlock 工具层(解封装→明文带行号→编辑→重封装,让 AI 安全改嵌套代码) | 卡片/HUD 编辑 | ⚪以后可能用 | 仅思路 | P2 |
| 2 | **PNG 角色卡 tEXt/ccv3 chunk 纯字节读写**(CRC32 自实现) | 导入 ST 卡 | 🔵仍可借 | 仅思路(若要**导出/写回 PNG** 卡,Python struct+zlib.crc32 重写) | P2 |
| 3 | 反代 ST 的 LLM/slash 复用宿主连接 | 与宿主集成 | ⚪以后可能用 | 仅思路 | P3 |
| 4 | 启动 Git 冷备份 + 聊天内快照双备份 | 存档安全 | 🔵仍可借 | 仅思路(不变量自动版本化) | P3 |

## 不值得碰
整个 Bun/TS 后端 + 624KB HTML IDE(与零依赖 Python+原生 HTML 正交,强耦合浏览器/ST/PNG 卡工作流)、依赖 LittleWhiteBox、全屏 HTML 游戏卡模板。

## 存档备忘(以后可能用)
- **pngHelper.ts**:日后 shadow-verse 若要支持「导出为标准 ST PNG 角色卡」(让产出物回流酒馆生态),这是唯一现成纯算法实现,标记可移植(Python struct+zlib.crc32)。
