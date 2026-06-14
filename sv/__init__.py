"""ShadowVerse · 暗宇宙引擎 —— AIGC 多元宇宙(海量世界生成 · 多种体验 · 强连接)。

分工(Model A):引擎管确定性状态(数据契约/核心循环/取料/落盘/连接),
生成与写作的智力由宿主 Agent 的模型负责。详见 ARCHITECTURE.md。

五层:
- L0 元件库   codex            创世素材(可复用抽象元件 + AI摘要 + 标签)
- L1 锻造器   forge            AIGC 生成世界/实体/线(prep 取料 → 宿主生成 → commit 落盘+谱系)
- L2 基质     world/entity/thread  持久暗宇宙(稳定 id + 谱系 + 跨透镜事件日志)
- L3 透镜     lenses           读(narrate)/玩(play)/模拟(simulate,默认关)/可视化(render,可插拔)
- L4 枢纽     nexus            跨世界实体(升格+召唤化身) + 世界互联 = 暗宇宙

工程内核:
- memory        核心循环铁律:rebuild(状态重建) ≠ retrieve(记忆检索) + 经历沉淀
- provenance    AIGC 谱系(可重生/可分支/可追溯)
- checks/craft  确定性质检 + 工艺食材
- skill_api     CLI 入口 ｜ mcp_server  零依赖 stdio MCP
"""

__version__ = "0.2.0"
