"""魂(Soul)—— 跨世界、跨透镜的不变量核心。opt-in:角色被「提取」(ascend)或被「创造为魂」才升华。

只存不变量(指针,不是快照):
  universe/souls/<soul_id>/
    soul.md        刚性身份/声音指纹/底线(跨世界一致的"我永远是谁")
    anchors.md     核心事实(= anchors,唯一真相,硬上限约 7;每行一条)
    identity.jsonl 身份级深记忆(所有化身、所有透镜共享,走 memory.retrieve_soul 的 union)
    meta.json      {name, origin{world,entity}, incarnations:[world/entity...], created}

魂**不**存 state.json、不存 episodic 经历——那些在各世界的化身(LocalEntity)里(此刻不同、本地经历不同)。
dormant:没有魂时引擎与今天字节等价;LocalEntity 仅当 card.soul_id 指向一个存在的魂时才走魂指针。
"""
from __future__ import annotations

from . import clock, memory, util
from .config import SOULS_DIR, load_json, save_json


class Soul:
    def __init__(self, sid: str):
        self.id = sid
        self.dir = SOULS_DIR / sid

    def exists(self) -> bool:
        return (self.dir / "meta.json").exists()

    def meta(self) -> dict:
        return load_json(self.dir / "meta.json", {}) or {}

    def anchors(self) -> list[str]:
        """核心事实(唯一真相):每行一条,去 bullet,硬上限 7。所有化身/透镜共读这一份。"""
        out = []
        for line in util.read_md(self.dir / "anchors.md").splitlines():
            s = line.strip()
            if s and not s.startswith("#") and not s.startswith("<!--"):
                out.append(s.lstrip("-* ").strip())
        return [x for x in out if x][:7]

    def incarnations(self) -> list[str]:
        return self.meta().get("incarnations", [])

    # ---- 身份级深记忆(跨化身共享)----
    def remember_identity(self, text: str, *, where: str = "", trace: str = "", tags=None) -> dict:
        return memory.append_identity(self.dir, text, where=where, trace=trace, tags=tags)

    def retrieve_for(self, inc_dir, query: str, k: int | None = None):
        """某化身视角的检索:它的本地经历 ∪ 本魂的身份记忆。"""
        return memory.retrieve_soul(inc_dir, self.dir, query, k) if k else memory.retrieve_soul(inc_dir, self.dir, query)

    @classmethod
    def load(cls, sid: str) -> "Soul":
        s = cls(sid)
        if not s.exists():
            raise FileNotFoundError(f"魂不存在:{sid}")
        return s

    @classmethod
    def create(cls, sid: str, name: str, *, anchors: list[str] | None = None,
               soul_md: str = "", origin: dict | None = None) -> "Soul":
        if not util.is_id(sid):
            raise ValueError(f"魂 id 必须 kebab-case:{sid!r}")
        s = cls(sid)
        if s.exists():
            raise FileExistsError(f"魂已存在:{sid}")
        s.dir.mkdir(parents=True, exist_ok=True)
        save_json(s.dir / "meta.json", {
            "id": sid, "name": name, "origin": origin or {},
            "incarnations": [], "created": clock.now_iso(),
        })
        util.write_md(s.dir / "anchors.md", "\n".join(f"- {a}" for a in (anchors or [])))
        util.write_md(s.dir / "soul.md", soul_md or f"# {name} · 魂\n\n> 跨世界不变量:声音 / 底线 / 身份。\n")
        return s

    def add_incarnation(self, world_id: str, entity_id: str) -> None:
        m = self.meta()
        ref = f"{world_id}/{entity_id}"
        if ref not in m.get("incarnations", []):
            m.setdefault("incarnations", []).append(ref)
            save_json(self.dir / "meta.json", m)
