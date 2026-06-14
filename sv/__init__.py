"""ShadowVerse · 暗宇宙引擎 —— AIGC 多元宇宙(海量世界生成 · 多种体验 · 强连接)。

分工(Model A):引擎管确定性状态(数据契约/核心循环/取料/落盘/连接),
生成与写作的智力由宿主 Agent 的模型负责。详见 ARCHITECTURE.md。

五层:
- L0 元件库   codex/codex_starter   创世素材(可复用抽象元件 + AI摘要 + 标签;内置起始库)
- L1 锻造器   forge/recipes         AIGC 生成世界/实体/线(取料+题材配方 → 生成 → 落盘+谱系)
- L2 基质     world/entity/thread   持久暗宇宙(稳定 id + 谱系 + 跨透镜事件日志 + 钩子台账)
- L3 透镜     lenses/chat           读(narrate产线)/玩(play+chat扮演页)/模拟(默认关)/可视化(render)
- L4 枢纽     nexus/merge           跨世界实体(升格+召唤化身) + 世界互联 + 世界融合 = 暗宇宙

工程内核:
- memory        核心循环铁律:rebuild(状态重建) ≠ retrieve(记忆检索) + 经历沉淀
- provenance    AIGC 谱系(可重生/可分支/可追溯)
- checks/craft  确定性质检 + 工艺食材
- importer      导入 SillyTavern 角色卡(V1/V2/V3,JSON/PNG)+ 世界书
- config        sv.conf + sv.local.conf 热加载 ｜ llm  可插拔 provider
- skill_api     CLI ｜ mcp_server  零依赖 MCP(40 工具) ｜ webapp+web  网页控制台
"""

__version__ = "0.3.0"
