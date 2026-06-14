"""L4 · 枢纽(Nexus)—— 让"一堆世界"成为"暗宇宙"的连接层。

三件事:
1. 跨世界实体:把某世界的本地实体「升格」进枢纽,从此可在多个世界拥有「化身(incarnation)」,
   灵魂/anchors 跨世界一致,各世界化身有独立记忆线——这是角色跨世界穿梭的核心。
2. 世界互联:在世界之间连边(裂隙/同源/传承…),多元宇宙因此有拓扑而非一堆孤岛。
3. 多元宇宙索引:nexus.md 鸟瞰所有世界、连接、跨世界实体。

升格(ascend)= 旧"私藏 keep"的泛化;召唤(summon)= 实体进入另一个世界开化身(强连接)。
"""
from __future__ import annotations

from pathlib import Path

from . import clock, memory, provenance, util
from .config import NEXUS_DIR, load_json, save_json
from .entity import LocalEntity
from .world import World

SOUL_TEMPLATE = """# {name} · 灵魂(跨世界实体)

> 枢纽 id:`{id}` ｜ 起源:{origin}

## 身份 + Identity Core(刚性,跨世界不变)
<!-- 见下方来源 profile 摘录,可由 Agent 精炼 -->

## 声音指纹 / 核心欲望与底线
<!-- -->
"""


class NexusEntity:
    def __init__(self, eid: str):
        self.id = eid
        self.dir = NEXUS_DIR / "entities" / eid

    @property
    def meta_path(self) -> Path:
        return self.dir / "meta.json"

    def exists(self) -> bool:
        return self.meta_path.exists()

    def meta(self) -> dict:
        return load_json(self.meta_path, {}) or {}

    def save_meta(self, m: dict) -> None:
        save_json(self.meta_path, m)

    def anchors(self) -> list[str]:
        return self.meta().get("anchors", [])

    def incarnation_dir(self, world_id: str) -> Path:
        return self.dir / "incarnations" / world_id

    def incarnations(self) -> list[str]:
        d = self.dir / "incarnations"
        return sorted(p.name for p in d.iterdir() if p.is_dir()) if d.exists() else []

    # 跨世界化身上的核心循环
    def rebuild(self, world_id: str) -> dict:
        return memory.rebuild(self.incarnation_dir(world_id), self.anchors())

    def sediment(self, world_id: str, text: str, **kw) -> dict:
        return memory.append_experience(self.incarnation_dir(world_id), text, **kw)

    @classmethod
    def load(cls, eid: str) -> "NexusEntity":
        e = cls(eid)
        if not e.exists():
            raise FileNotFoundError(f"枢纽无此实体:{eid}")
        return e

    @classmethod
    def list_all(cls) -> list[str]:
        d = NEXUS_DIR / "entities"
        return sorted(p.name for p in d.iterdir() if (p / "meta.json").exists()) if d.exists() else []


# ---------- 升格:本地实体 → 跨世界枢纽实体 ----------
def ascend(world: World, local_id: str, *, as_id: str | None = None) -> dict:
    src = LocalEntity.load(world, local_id)
    nid = as_id or local_id
    ne = NexusEntity(nid)
    if ne.exists():
        raise FileExistsError(f"枢纽已有此实体:{nid}")
    name = src.card().get("name", nid)
    origin = f"{world.id}/{local_id}"

    soul = SOUL_TEMPLATE.format(id=nid, name=name, origin=origin)
    soul += "\n\n---\n\n## 来源 profile(升格时烘焙,可精炼)\n\n" + util.read_md(src.dir / "profile.md")
    util.write_md(ne.dir / "soul.md", soul)
    ne.save_meta({
        "id": nid, "name": name, "anchors": src.anchors(),
        "origin": {"world": world.id, "entity": local_id},
        "incarnations": [], "provenance": provenance.stamp("ascend", parent=origin),
        "created": clock.now_iso(),
    })

    # 起源世界化身:带上本地状态 + 经历
    inc = ne.incarnation_dir(world.id)
    memory.write_state(inc, memory.read_state(src.dir))
    for e in memory.all_experiences(src.dir):
        memory.append_experience(inc, e["text"], level=e.get("level", "持久"),
                                 where=e.get("where", origin), trace=e.get("trace", ""), tags=e.get("tags", []))
    util.write_md(inc / "growth.md", f"# {name} @ {world.id} · 成长(本化身有界)\n")
    util.write_md(inc / "summary.md", f"# {name} @ {world.id} · 摘要\n\n> 起源化身\n")
    m = ne.meta(); m["incarnations"] = [world.id]; ne.save_meta(m)

    _register(nid, name, origin)
    render_map()
    return {"nexus_id": nid, "name": name, "origin": origin, "anchors": src.anchors(), "incarnation": world.id}


# ---------- 召唤:枢纽实体进入另一个世界,开新化身(跨世界穿梭) ----------
def summon(nexus_id: str, target: World, *, entry: str = "本体进") -> dict:
    ne = NexusEntity.load(nexus_id)
    wid = target.id
    inc = ne.incarnation_dir(wid)
    if not (inc / "state.json").exists():
        # entry 模式决定带不带记忆;Phase 0:本体进=带,换皮进=清空起新身份(投影 Phase2 精化)
        memory.write_state(inc, {"location": "", "mood": "", "body": "", "goal": ""})
        util.write_md(inc / "growth.md", f"# {nexus_id} @ {wid} · 成长\n")
        util.write_md(inc / "summary.md", f"# {nexus_id} @ {wid} · 摘要\n\n> 召唤方式:{entry}\n")
    m = ne.meta()
    if wid not in m.get("incarnations", []):
        m.setdefault("incarnations", []).append(wid)
        ne.save_meta(m)
    render_map()
    return {"nexus_id": nexus_id, "world": wid, "entry": entry,
            "incarnations": ne.incarnations(), "note": "跨世界化身已开(换皮投影=Phase2 精化)"}


# ---------- 世界互联 ----------
def _links_path() -> Path:
    return NEXUS_DIR / "links.json"


def link_worlds(a: str, b: str, relation: str, *, note: str = "") -> dict:
    World.load(a); World.load(b)   # 校验存在
    data = load_json(_links_path(), {"links": []}) or {"links": []}
    edge = {"a": a, "b": b, "relation": relation, "note": note, "at": clock.now_iso()}
    data["links"].append(edge)
    save_json(_links_path(), data)
    for wid, other in ((a, b), (b, a)):
        w = World.load(wid); wm = w.meta()
        wm.setdefault("links", []).append({"to": other, "relation": relation})
        w.save_meta(wm)
    render_map()
    return edge


def links() -> list[dict]:
    return (load_json(_links_path(), {"links": []}) or {"links": []}).get("links", [])


def unlink(a: str, b: str) -> dict:
    """删掉 a 与 b 之间的所有连接(双向)。"""
    data = load_json(_links_path(), {"links": []}) or {"links": []}
    kept = [e for e in data["links"] if {e["a"], e["b"]} != {a, b}]
    removed = len(data["links"]) - len(kept)
    data["links"] = kept
    save_json(_links_path(), data)
    for wid, other in ((a, b), (b, a)):
        w = World(wid)
        if w.exists():
            m = w.meta()
            m["links"] = [l for l in m.get("links", []) if l.get("to") != other]
            w.save_meta(m)
    render_map()
    return {"removed": removed, "a": a, "b": b}


def purge_world(wid: str) -> None:
    """世界被删时清理枢纽残留:删touching它的连接 + 各跨世界实体在它里的化身。"""
    import shutil
    data = load_json(_links_path(), {"links": []}) or {"links": []}
    data["links"] = [e for e in data["links"] if wid not in (e["a"], e["b"])]
    save_json(_links_path(), data)
    for other in World.list_all():
        if other == wid:
            continue
        w = World.load(other); m = w.meta()
        if any(l.get("to") == wid for l in m.get("links", [])):
            m["links"] = [l for l in m["links"] if l.get("to") != wid]
            w.save_meta(m)
    for nid in NexusEntity.list_all():
        ne = NexusEntity(nid); m = ne.meta()
        if wid in m.get("incarnations", []):
            m["incarnations"] = [x for x in m["incarnations"] if x != wid]
            ne.save_meta(m)
            inc = ne.incarnation_dir(wid)
            if inc.exists():
                shutil.rmtree(inc)
    render_map()


# ---------- 索引 ----------
def _idx_path() -> Path:
    return NEXUS_DIR / "nexus.json"


def _register(nid: str, name: str, origin: str) -> None:
    idx = load_json(_idx_path(), {"entities": []}) or {"entities": []}
    idx["entities"] = [e for e in idx["entities"] if e.get("id") != nid]
    idx["entities"].append({"id": nid, "name": name, "origin": origin, "at": clock.now_iso()})
    save_json(_idx_path(), idx)


def kept_entities() -> list[dict]:
    return (load_json(_idx_path(), {"entities": []}) or {"entities": []}).get("entities", [])


def render_map() -> None:
    lines = ["# 暗宇宙 · 枢纽鸟瞰", "", "## 世界"]
    for wid in World.list_all():
        w = World.load(wid); m = w.meta()
        lines.append(f"- **{m.get('name', wid)}** (`{wid}`) — {m.get('genre','')} ｜ {len(w.list_threads())} 线")
    lines += ["", "## 世界互联(暗宇宙拓扑)"]
    ls = links()
    lines += [f"- {e['a']} ⇄ {e['b']} :{e['relation']}" for e in ls] or ["_(还没有连接)_"]
    lines += ["", "## 跨世界实体"]
    for k in kept_entities():
        ne = NexusEntity(k["id"])
        incs = "、".join(ne.incarnations()) if ne.exists() else ""
        lines.append(f"- **{k['name']}** (`{k['id']}`) — 起源 {k['origin']} ｜ 化身于:{incs or '—'}")
    if not kept_entities():
        lines.append("_(还没有跨世界实体)_")
    util.write_md(NEXUS_DIR / "nexus.md", "\n".join(lines))
