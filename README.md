# ShadowVerse · 暗宇宙引擎

ShadowVerse 是一个让角色、世界、关系和事件可以持续演化的叙事状态引擎。模型负责创作表达，
引擎负责保存可计算、可追溯、可跨会话延续的世界事实。

## 理念

- 世界状态与生成文本分离；
- 角色、关系和事件拥有稳定身份与时间线；
- 同一份数据可以服务写作、角色扮演、群聊和世界模拟；
- 宿主 Agent 可更换，世界数据不依赖单一模型或平台。

## 主要功能

- 世界、角色、关系、事件和章节管理；
- 多世界穿梭、时间线与状态演化；
- 陪伴/RP、群聊和创作工具；
- CLI 与 MCP 两种调用方式；
- 工具分层、诊断和端到端 smoke test；
- 可独立存放的 universe 数据目录。

## 本地使用

```bash
python -m sv.skill_api doctor
python -m sim.smoke
python -m sv.mcp_server
```

运行时 MCP、Skill 安装位置和实际数据目录统一由仓库外运维配置管理。

## 目录

- `sv/`：领域引擎与 MCP；
- `sim/`：模拟与 smoke test；
- `universe/`：默认世界数据；
- `deploy/skills/`：可分发的通用 Skill 内容，不保存实际宿主配置。
