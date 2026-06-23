"""Lens 协议 + 统一写入口 commit_core —— 每扇「门」(读/玩/陪伴/模拟/可视化/跨界)都走同一条提交路径。

「一魂 · 多门 · 一条时间线」的物理咽喉:commit_core 是落盘的**唯一写入口**——
任何门发生的事都落在同一条 beats.jsonl 时间线上,角色记忆按 role 门控统一沉淀,
没有孤岛事件能藏身。新门 = 实现 prep + commit,即免费获得时间线 + 门控记忆 + 三条前门。

Model A:引擎只负责组装上下文与确定性落盘;生成智力来自宿主 Agent 的模型,引擎不内置。
"""
from __future__ import annotations

from typing import Protocol

from .entity import LocalEntity
from .thread import Thread
from .world import World

# 闭合的透镜标签集:beats.lens 只能取自这里,保证统一时间线可按门过滤(不退化成自由文本)。
LENS_TAGS = {"narrate", "play", "companion", "simulate", "render", "cross"}


class Lens(Protocol):
    """一扇门的契约:prep 只读组包,commit 唯一写盘——读写都落到同一基质。

    现有 narrate/play/simulate/render 已事实上符合;RP/陪伴等新门照此实现即可。
    """
    name: str          # beats.jsonl 的 lens 标签(取自 LENS_TAGS)
    where_prefix: str  # beat.where 命名空间,如 'ch:' / 'play:' / 'comp:' / 'rift:'

    def prep(self, world: World, thread: Thread, **kw) -> dict: ...
    def commit(self, world: World, thread: Thread, payload: dict) -> dict: ...


def commit_core(world: World, thread: Thread, *, lens: str, where: str = "",
                beat: str | None = None, sediments=(), state_updates=None, mark: bool = False) -> dict:
    """所有透镜的统一写盘核心。顺序:① 角色门控沉淀记忆 → ② 写回状态 → ③ 落 beat → ④(可选)标记透镜。

    - sediments: [{entity, text, level?, trace?, tags?}],cameo/npc 经 entity.sediment 门控自动丢弃。
    - state_updates: {entity_id: {...}},调用方自带的字段(如章号)原样写入。
    - 返回 {beat, sedimented:[{entity,id,level}], skipped:[{entity,why}]}。
    """
    if lens not in LENS_TAGS:
        raise ValueError(f"未知透镜标签:{lens}(应取自 {sorted(LENS_TAGS)})")
    sedimented, skipped = [], []
    for s in sediments or ():
        e = LocalEntity(world, s.get("entity"))
        if not e.exists():
            skipped.append({"entity": s.get("entity"), "why": "实体不存在"}); continue
        ent = e.sediment(s.get("text", ""), level=s.get("level", "持久"),
                         where=where, trace=s.get("trace", ""), tags=s.get("tags", []))
        if ent is None:
            skipped.append({"entity": e.id, "why": f"role={e.role} 不写回"})
        else:
            sedimented.append({"entity": e.id, "id": ent["id"], "level": ent["level"]})
    for eid, upd in (state_updates or {}).items():
        e = LocalEntity(world, eid)
        if e.exists():
            e.update_state(dict(upd))
    beat_obj = thread.add_beat(beat, lens=lens, where=where) if beat is not None else None
    if mark:
        thread.mark_lens(lens)
    return {"beat": beat_obj, "sedimented": sedimented, "skipped": skipped}
