"""谱系(provenance)—— AIGC 一等公民:每个被生成的工件都记录"谁由什么生成"。

让万物可重生 / 可分支 / 可追溯。世界、实体、线的 meta.json 都带 provenance 字段。
"""
from __future__ import annotations

from . import clock


def stamp(source: str, *, prompt: str = "", from_codex: list[str] | None = None, parent: str = "") -> dict:
    """生成一条谱系记录。
    source: forge(AIGC生成) | manual(手建) | import(导入) | ascend(升格) | summon(召唤化身) | branch(分支)
    """
    return {
        "source": source,
        "prompt": prompt,
        "from_codex": from_codex or [],
        "parent": parent,
        "generated_at": clock.now_iso(),
    }
