# ShadowVerse · 暗宇宙引擎

> **暗宇宙 · 无限世界 · AIGC** —— 一个生成并连接无数世界的多元宇宙引擎。
> 从元件与一句话造出自洽世界(无限世界);万物 AIGC 产出、可重生;角色在世界间穿梭、世界彼此相连(暗宇宙);同一个世界能用多种方式体验——**读它、玩它、看它自己跑、把它画出来**。

真实软件项目(零依赖 Python 3.10+),不是 skill 集。设计见 **[ARCHITECTURE.md](ARCHITECTURE.md)**。

## 不是"写小说工具"

小说和 RP 只是引擎的**两个体验透镜**。核心是五层:

```
L4 枢纽    跨世界实体穿梭 + 世界互联 = 暗宇宙
L3 透镜    读(narrate)· 玩(play)· 模拟自演化(默认关)· 可视化多模态(可插拔)
L2 基质    世界 / 实体 / 叙事线(持久 + 谱系 + 跨透镜事件日志)
L1 锻造    AIGC 生成世界/实体/线(取料 → 宿主模型生成 → 落盘+谱系)
L0 元件    创世素材(元素周期表式可复用元件;内置 ~40 个亲手提炼的起始元件,`codex-seed` 一键填充)
```

**分工(Model A)**:引擎管确定性状态;生成与写作的智力由**宿主 Agent 的模型**(OpenClaw/Hermes/Claude)提供。引擎不内置模型、不限尺度。

## 快速开始

```bash
PYTHONUTF8=1 python -m sv.skill_api doctor      # 自检
PYTHONUTF8=1 python -m sim.run_tests            # 全套测试(memory/forge/lenses/nexus/smoke,5 套)

# 看得见也能用:播一个 demo 多元宇宙 → 启动网页控制台
PYTHONUTF8=1 python -m sim.seed                 # 造2世界/3角色/2章正文/跨世界穿梭
PYTHONUTF8=1 python -m sv.webapp                # → http://127.0.0.1:8787  (建/写/玩/连接都能在页面做)

# AIGC 造世界:取料 → (宿主据包生成 world.md) → 落盘
python -m sv.skill_api world-prep "一座无限攀登的规则之塔" --tags 规则
echo '{"id":"infinite-tower","name":"无限之塔","genre":"无限流","body":"# 无限之塔\n..."}' | python -m sv.skill_api world-commit

# 造角色 / 线,读一章,玩一场
python -m sv.skill_api entity-prep infinite-tower "外冷内热的守护者"
python -m sv.skill_api narrate-prep infinite-tower first-climb --intent "破解第一条矛盾规则"

# 暗宇宙:角色跨世界穿梭
python -m sv.skill_api ascend infinite-tower ye-wudao          # 升格为跨世界实体
python -m sv.skill_api link infinite-tower linjiang "塔之裂隙"  # 世界互联
python -m sv.skill_api summon ye-wudao linjiang --entry 换皮进   # 在另一个世界开化身
python -m sv.skill_api nexus                                    # 多元宇宙鸟瞰
```

## CLI 命令(`python -m sv.skill_api <cmd>`)

| 组 | 命令 |
|----|------|
| L0 元件 | `codex-add` / `codex-seed`(填充 ~40 抽象起始元件) / `codex-list` / `codex-pick` |
| L1 锻造(AIGC) | `world-prep`→`world-commit` · `entity-prep`→`entity-commit` · `thread-prep`→`thread-commit` · `recipes`(题材配方) · `gen-world`/`gen-entity`/`gen-thread`/`gen-chapter`(配 SV_PROVIDER 一键生成) |
| 手建 | `new-world` / `new-entity` / `new-thread` |
| L3 透镜 | `narrate-prep`→`narrate-commit`(读) · `play-prep`→`play-commit`(玩) · `simulate-*`(模拟,默认关) · `render-*`(多模态,可插拔) |
| narrate 产线 | `narrate-run`(写→审→改→落一键) · `review-prep`/`narrate-review`(审校) · `reflect-prep`/`narrate-reflect`(反思) |
| 钩子台账 | `hook-alpha`(设α悬念) · `hook-add` · `hook-set`(状态机) · `hooks`(查;审校自动揪过期未回收的伏笔) |
| L4 枢纽 | `ascend`(升格) · `summon`(召唤化身) · `link`(世界互联) · `nexus`(鸟瞰) |
| 管理/导出 | `export-thread`(全书导出) · `delete-world`/`delete-thread`/`delete-entity`/`delete-codex` · `unlink` |
| 工具 | `check` / `status` / `show` / `doctor` |

MCP(零依赖 stdio):`python -m sv.mcp_server`(22 个 typed 工具,语义同 CLI)。

## 目录

```
sv/         引擎(codex·forge·world·entity·thread·nexus·lenses·memory·
            provenance·recipes·checks·craft·skill_api·mcp_server·config·clock·util)
sv/webapp.py + web/index.html   网页视图层(零依赖 stdlib server,只读仪表盘)
universe/   数据真相(codex/ + worlds/<w>/{entities,threads}/ + nexus/)
sim/        run_tests(总跑) · test_memory/forge/lenses/nexus · smoke · seed(demo 播种)
ARCHITECTURE.md · sv.conf · deploy/
```

## 两种用法

- **独立运行**:`python -m sv.webapp` 起网页控制台,在 **⚙ 设置** 页填自己的 LLM(OpenAI/兼容端/Anthropic/Ollama)与渲染 key——保存即时生效、无需重启,密钥只存本机 `sv.local.conf`(gitignore,不入库)。一切自包含。
- **嵌入 Agent**:作为 OpenClaw/Hermes 的 MCP skill,**不用配 LLM**——生成/写作走宿主 Agent 的模型(Model A)。见 `deploy/`。

## 网页控制台

`python -m sv.webapp` → http://127.0.0.1:8787 起一个零依赖网页控制台(读写同一批 `universe/` 文件,直接调引擎;深色"暗宇宙"主题;只绑 `127.0.0.1`):

**看**:多元宇宙地图(世界节点+连接边)、世界设定、章节阅读器、角色经历时间线、**跨世界实体的各世界化身对照**(灵魂一致/记忆独立)、元件库。

**用**(直接在页面操作):
- 新建世界 / 实体 / 叙事线 / 元件,编辑世界设定 —— 每个建表都带 **🔮 AI生成**(配了 `SV_PROVIDER` 就真生成,没配=stub 占位)
- **✍ 写一章**:**🔮 AI写本章**(一键写正文+结构化沉淀)或「取写作包」喂你自己的 LLM → 审改 → 勾每个角色这章沉淀(客串自动忽略)→ 落章,回执显示字数/自动质检/门控
- **✨ AI 产线写章**:一键跑 写手→审校→修订→落章,弹窗显示全过程(草稿字数 / 审校 findings / 修订轮数 / 落章回执)
- **🧠 反思**:横向校验最近数章全局自洽 + 提示漏掉的成长(建议,不自动落)
- **🎭 玩一场**:场景+过程+按角色勾「触发成长」条件写回
- **💬 对话**:在角色页点「对话」,用你在设置里配的 LLM 跟角色逐句聊(以第一人称扮演,带记忆与人设);对话存角色 `chat.jsonl`。需先在 ⚙ 设置 配 LLM
- **📥 导入 ST 角色卡**:吃 SillyTavern 角色卡 V1/V2/V3(JSON 或 PNG 内嵌)+ 世界书 → 直接变 entity + 世界设定,导入后即可点「对话」聊起来
- **📜 故事时间线**:把一个世界跨所有叙事线的 beats + 角色★成长时刻合到一条时间轴,跨世界实体标出
- **⚙ 设置**:在页面里配 LLM provider/key/model、渲染 key,即时生效;状态面板显示当前 LLM/渲染是否启用
- **⬆ 升格**角色为跨世界实体、**✦ 召唤**进别的世界、**⇄ 连接**世界
- **🖼 多模态**:角色「生成立绘」(用固定 appearance 锁脸保持像同一人)、叙事线「生成场景图」,出图存进图库展示 —— 配 `SV_RENDER=gitee + GITEE_API_KEY` 才出图(Gitee z-image,~18s),没配则休眠
- **📖 导出全书**(把一条线的全部章节下载成单个 markdown)、**🗑 删除**世界/线/实体/元件(带确认,删世界自动清枢纽里它的连接与化身)

> 生成智力来自宿主模型(Model A)或你在 `sv.conf` 配的可插拔 LLM(`SV_PROVIDER`,默认 stub 关)。AI 生成**返回正文供你审改后再落盘**(人在环)。只绑 `127.0.0.1`(单机本地工具)。

## 状态

**Phase 0 五层地基已贯通**(测试 5 套全绿 + demo 种子 + 交互式网页控制台):元件取料 · AIGC 锻造世界/实体/线(带谱系+题材配方) · 读/玩透镜(核心循环铁律+沉淀门控+落章自动质检) · 跨世界实体穿梭 + 世界互联 · 页面里直接建/写/玩/连接。
模拟(自演化)与多模态渲染**接口已建、默认关/休眠**。后续慢慢填充:批量造世界、子代理产线(写→审→反思)、开自演化、向量记忆、线分支——见 ARCHITECTURE「演进阶梯」。
