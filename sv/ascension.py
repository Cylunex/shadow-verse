"""升华 / 跨世界穿越(建在魂模型 [[soul]] 上的多元宇宙真实层)。

两条升华路径(opt-in,由用户触发,普通角色不升华):
- extract(world, entity):**提取**一个已有角色 → 就地抽魂(不复制平行树):
    建 Soul(profile/anchors 烘焙)→ 把身份级经历搬进魂 identity.jsonl(从化身移除免 union 重复)
    → 原角色 card 设 soul_id(它就地成为魂的第一具化身)→ 落多维数值「攻略卡」(attrs)。
- create_soul(world, eid, name):**创造**一个一出生就是魂的角色。

summon(soul_id, target_world):召唤魂进入另一个世界开真实化身——受世界链接约束,
  且**在目标世界线落一条 cross beat**:魂的到来是那个【世界】的事件(世界与魂同等,世界有后果)。

魂与世界同等:魂带着身份/锚点穿行;每个世界有自己的「世界线」(worldline thread)记宏观大事。
这是新的规范路径;旧 nexus.py(NexusEntity 平行树)暂留作 legacy,迁移后退役。
"""
from __future__ import annotations

from . import attrs, memory, nexus, util
from .entity import LocalEntity
from .lens import commit_core
from .soul import Soul
from .thread import Thread
from .world import World


def _worldline(world: World) -> Thread:
    """世界自己的宏观线(worldline thread):记跨副本的大事(魂降临、世界剧变…)。世界=一等核心。"""
    tid = "worldline"
    if not Thread(world, tid).exists():
        Thread.create(world, tid, f"{world.meta().get('name', world.id)} · 世界线",
                      genre=world.meta().get("genre", ""))
    return Thread(world, tid)


def extract(world: World, entity_id: str, *, player_name: str = "你", soul_id: str | None = None) -> dict:
    """提取一个角色 → 升华为跨世界的魂(就地抽魂)。"""
    e = LocalEntity.load(world, entity_id)
    if e.card().get("soul_id"):
        raise ValueError(f"{entity_id} 已是魂的化身(soul_id={e.card()['soul_id']})")
    sid = soul_id or entity_id
    name = e.card().get("name", entity_id)
    soul = Soul.create(sid, name, anchors=e.anchors(),
                       soul_md=f"# {name} · 魂\n\n> 跨世界不变量(从 {world.id}/{entity_id} 抽取)\n\n"
                               + util.read_md(e.dir / "profile.md"),
                       origin={"world": world.id, "entity": entity_id})
    # 身份级经历搬进魂(从化身本地移除,避免 retrieve_soul union 重复计)
    moved, kept = [], []
    for x in memory.all_experiences(e.dir):
        (moved if x.get("level") == "身份" else kept).append(x)
    for x in moved:
        memory.append_identity(soul.dir, x.get("text", ""), where=x.get("where", ""),
                               trace=x.get("trace", ""), tags=x.get("tags", []))
    if moved:
        memory.set_experiences(e.dir, kept)
    e.set_card_field("soul_id", sid)
    soul.add_incarnation(world.id, entity_id)
    attrs.apply_panel(e, player_name)   # 升华即落多维数值攻略卡(初期数值化,直观)
    return {"soul": sid, "name": name, "incarnation": f"{world.id}/{entity_id}",
            "moved_identity": len(moved), "anchors": soul.anchors()}


def create_soul(world: World, eid: str, name: str, *, role: str = "main",
                anchors: list[str] | None = None, appearance: str = "", player_name: str = "你") -> dict:
    """创造一个一出生就是魂的角色(第二条升华路径):本地化身 + 魂 + 绑定 + 数值卡。"""
    e = LocalEntity.create(world, eid, name, role=role, appearance=appearance)
    soul = Soul.create(eid, name, anchors=anchors or [], origin={"world": world.id, "entity": eid})
    e.set_card_field("soul_id", eid)
    soul.add_incarnation(world.id, eid)
    attrs.apply_panel(e, player_name)
    return {"soul": eid, "name": name, "incarnation": f"{world.id}/{eid}", "anchors": soul.anchors()}


def summon(soul_id: str, target_world: World, *, entry: str = "本体进",
           as_id: str | None = None, player_name: str = "你") -> dict:
    """召唤魂进入另一个世界,开真实化身。受链接约束;在目标世界线落 cross beat(世界有后果)。"""
    soul = Soul.load(soul_id)
    eid = as_id or soul_id
    if LocalEntity(target_world, eid).exists():
        raise FileExistsError(f"{target_world.id} 已有实体:{eid}")
    name = soul.meta().get("name", eid)
    inc_worlds = [r.split("/")[0] for r in soul.incarnations()]
    # 链接约束:目标世界须与魂的某个化身世界相连;无门则记「无门强召」(约束教学,不静默失败)
    via = None
    for ln in nexus.links():
        if ({ln["a"], ln["b"]} & set(inc_worlds)) and target_world.id in (ln["a"], ln["b"]):
            via = ln
            break
    if via is None:
        entry = "无门强召"
    e = LocalEntity.create(target_world, eid, name, role="main")
    e.set_card_field("soul_id", soul_id)           # 出生即绑魂:锚点+身份记忆即刻共享(非快照)
    soul.add_incarnation(target_world.id, eid)
    attrs.apply_panel(e, player_name)
    src = inc_worlds[0] if inc_worlds else "?"
    rel = via["relation"] if via else "无门"
    t = _worldline(target_world)
    commit_core(target_world, t, lens="cross", where=f"rift:{src}->{target_world.id}",
                beat=f"{name} 自 {src} 经「{rel}」降临 {target_world.id}", mark=True)
    return {"soul": soul_id, "world": target_world.id, "incarnation": eid,
            "entry": entry, "via": (via or {}).get("relation"), "worldline_beat": True}
