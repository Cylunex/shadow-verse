# 部署 ShadowVerse 引擎(平台中立)

引擎零依赖(纯标准库 Python 3.10+)。宿主 Agent(OpenClaw / Hermes / Claude Code)通过
**MCP**(推荐)或 **CLI** 调用引擎,自己的模型负责写正文(Model A)。

## 三步

1. **放项目**:把本仓库放到运行时工作区(如 `<workspace>/projects/shadow-verse`)。记 `$SV_HOME` = 项目根绝对路径。
2. **装技能**:把 [`deploy/skills/shadowverse/SKILL.md`](skills/shadowverse/SKILL.md) 放进运行时技能目录(如 `<skills根>/<category>/shadowverse/SKILL.md`)。
3. **注册 MCP server**(推荐):
   ```json
   {
     "command": "python",
     "args": ["-m", "sv.mcp_server"],
     "cwd": "<$SV_HOME 的绝对路径>",
     "env": { "PYTHONUTF8": "1", "SV_MCP_TIER": "1" }
   }
   ```
   工具以 `mcp_shadowverse_*` 前缀出现。也可直接跑 CLI:`cd $SV_HOME && python -m sv.skill_api <cmd>`。
   - **工具分层(`SV_MCP_TIER`,看板娘强烈建议)**:全量 typed 工具 ~60 个,一股脑进 agent loop 会工具过载。设 `SV_MCP_TIER=1` 只暴露**主回路 Tier1**(陪伴/RP `play_*`、群聊 `group_*`、`status`/`nexus`/`summon`/`ascend`/`link`/`expr_classify`/`doctor`);`=2` 再含创作/质量工具;缺省或 `=3` 全暴露。分层只收敛 `tools/list` 的"广告面",任何工具仍可被 `tools/call` 直接调(工具语义不变)。

## 两个最常踩的坑

- **注册用 `cwd` 不是 `PYTHONPATH`**:`-m sv.mcp_server` 必须在项目根运行,引擎才能找到 `sv/` 包与 `sv.conf`。
- **数据与代码分离**:若不想创作数据混在代码仓里,在 `sv.conf` 设 `SV_UNIVERSE_DIR=<workspace 数据区>`,引擎读写那里。**部署更新代码时绝不覆盖 `universe/` 创作数据。**

## 自检

```bash
cd $SV_HOME && PYTHONUTF8=1 python -m sv.skill_api doctor
PYTHONUTF8=1 python -m sim.smoke      # 端到端 21 项(五层贯通)
```

具体注册命令以运行时为准(`hermes mcp --help` / OpenClaw 的 MCP 配置)。typed 工具数以 `python -m sv.mcp_server`(=`mcp_server.TOOLS` 长度)/ `sv doctor` 实际为准(现 ~60,分 Tier1/2/3),语义同 CLI。
