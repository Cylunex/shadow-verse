# 暗宇宙愿景 ↔ shadow-verse 现状对照

> 对照 `F:/Project/ShadowVerse/参考功能.txt`(三版架构草稿,收敛为「统一底层 + 多模式并行」)。
> 状态:✅已实现 · 🟡框架已搭(待充实) · 🔵未做(规模/需求驱动) · ⬜不做(已判过)。
> 更新 2026-06-18 · 规模(引擎模块 / MCP 工具 / 测试套数)以 `sv doctor`、`python -m sim.run_tests` 实际输出为准,文档不写死。

---

## 核心思想对照

愿景的灵魂:**「所有模式共享同一套底层;新增模式只需添加提示模板 + 前端视图,无需改动核心引擎」+「数据互通(模式间一键转换)」。**

shadow-verse 的五层(codex→forge→substrate→透镜→nexus)+ 透镜(lens)架构**正是这个思想的实现**。本轮把它**形式化**:
- 🟡 `sv/modes.py` —— 模式注册表(11 模式作纯数据,每个 = 透镜 + 模板 guide + 输出格式 + 视图)。加模式 = 加一条 MODES 数据,不改核心。
- 🟡 `sv/convert.py` —— 数据互通(以 thread.beats 跨透镜事件日志为枢纽,chat↔小说↔CYOA↔剧本↔跑团一键转换)。

---

## A. 核心层(Core Layer)对照

| 愿景 | 状态 | shadow-verse |
|---|---|---|
| 用户 Persona | ✅ | `player.json`(name+persona,治身份漂移) |
| 角色卡(信息/性格/关系/记忆锚点)+ ST 导入导出 | ✅ | entity(card.json+profile.md+anchors)、importer 导入 ST V1/V2/V3(导出 PNG 待做) |
| 世界卡/Lorebook(地点/势力/规则/历史/事件) | ✅ | world.md 12模块 + worldbook 触发引擎(关键词/selective/递归/时效/position@D) |
| 无限世界(持久演化/时间线/动态事件/腐化追踪) | 🟡 | world+thread+beats 持久;演化=simulate 透牜(默认关);腐化/时间线追踪待充实 |
| 向量记忆(长期/情感/sanity/关系) | 🟡 | memory.py(确定性 rebuild + 加权 retrieve,bigram 占位);向量全量版=规模驱动(蓝图见 competitor-archives/LittleWhiteBox) |
| 跨模式记忆共享(RP事件自动进小说/跑团) | ✅ | thread.beats 跨透镜事件日志(所有透镜发生的事落同一线)+ convert 转换 |
| AIGC 文本 | ✅ | llm(可插拔 openai/anthropic/ollama) |
| AIGC 图像(立绘/场景/分镜) | ✅ | render(Gitee 出图,appearance 锁脸 + 立绘表情切换);分镜=comic 模式 |
| AIGC 音乐/音效 | 🔵 | music 模式有模板,无音频后端(可插拔接口可留) |
| 提示模板引擎(按模式切风格) | ✅ | modes.mode_pack + promptkit + skills + recipes |
| 数据互通与一键导出(TXT/PDF/EPUB/图集) | 🟡 | convert(模式转换)+ export(全书 md);PDF/EPUB 待做 |

## B. 模式层(Mode Layer)对照 —— 13 模式

| # | 模式 | 状态 | 落地 |
|---|---|---|---|
| 核心1 | 酒馆角色扮演 | ✅ | play 透镜 + chat 扮演页(swipe/变量/HUD/立绘/世界书) |
| 核心2 | 小说创作 | ✅ | narrate 产线(写→审→改→落+钩子+stylestat+诊断+skill库+journal) |
| 核心3 | 虚拟陪伴/生活模拟 | 🟡 | chat + 变量(关系数值);专属产品是独立的 Doll;模式入口已注册 |
| 支柱4 | 互动小说/CYOA | 🟡 | branch.py(分叉+蝴蝶效应+Scene/Beat 图)+ convert(小说→CYOA);选项驱动 UI 待做 |
| 支柱5 | 剧本/影视脚本 | 🟡 | modes 模板 + convert(小说/beats→剧本);格式渲染待做 |
| 支柱6 | 漫画/图形小说 | 🟡 | render(出图)+ modes 分镜模板 + convert(小说→分镜);气泡/排版待做 |
| 支柱7 | 音乐/歌词 | 🔵 | modes 模板(歌曲结构);无音频生成后端 |
| 支柱8 | 桌游/跑团 | 🟡 | play + macros(`{{roll::NdM}}` 骰子)+ modes 模板 + convert(beats→战役日志);属性/战斗系统待做 |
| 支柱9 | 教育/知识探索 | 🟡 | modes 模板(导师+问答);纯模板,可用 |
| 支柱10 | 梦境/超现实 | 🟡 | modes 模板(象征叙事+sanity 变量);可用 |
| 世界 | 世界探索 | 🟡 | simulate 透镜(默认关)+ 多元宇宙地图;地图导航 UI 待做 |

> **关键:11 个模式都已在注册表里、有提示模板、复用现成透镜。** 大多是 🟡「框架已搭、模板可用、专属前端视图待充实」——这正是愿景说的「加模式只加模板+视图」。

## C. 数据互通对照

| 愿景数据流 | 状态 | convert 支持 |
|---|---|---|
| RP聊天 → 小说章节 | ✅ | `convert.chat_to(world, entity, "novel")` |
| 聊天/小说 → CYOA分支 | ✅ | `chat_to(...,"cyoa")` / `chapter_to(...,"cyoa")` + branch.py 落分支 |
| 小说 → 剧本场景 | ✅ | `chapter_to(...,"screenplay")` |
| 小说 → 漫画分镜 | ✅ | `chapter_to(...,"comic")`(+render 出图) |
| beats → 跑团战役日志 | ✅ | `beats_to(...,"tabletop")` |
| 无限世界事件 → 同步所有模式 | ✅ | thread.beats 即跨透镜共享枢纽 |
| AIGC图像通用(立绘/分镜/插图) | ✅ | render 产物存 universe,各模式可引 |

---

## 整体判断

- **核心层 ≈ 已就位**:愿景核心层的角色/世界/Persona/记忆/AIGC/提示引擎/数据互通,shadow-verse 都有对应(✅或🟡)。
- **模式层 = 框架已搭**:本轮 modes.py 把「模式」做成可插拔数据(11 模式),convert.py 打通数据互通——愿景最独特的「统一底层+多模式+一键转换」骨架立起来了。
- **剩下的主要是「每个模式的专属前端视图」和少量后端**(音频/PDF/地图导航/CYOA 选项 UI/向量记忆全量),都是 🟡/🔵,可按需逐个充实,不动核心。

**一句话:愿景的「引擎与骨架」已基本到位;接下来是给各模式补「视图与皮肤」。** 这与愿景「新增模式只需模板+视图」完全吻合——shadow-verse 已经走在这条路上。
