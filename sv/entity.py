"""L2 · 实体 —— 栖居世界的角色(也可扩展到势力/造物)。

两种存储:
- LocalEntity:某世界内的实体,`worlds/<w>/entities/<id>/`(card.json 记 role + profile + state/experiences)。
- 跨世界实体住在枢纽(nexus.py),通过 incarnations/<world>/ 在各世界有化身——这是强连接多元宇宙的核心。

role 门控成长写回:main/secondary 写回,cameo 不写回,npc 随戏份。
三层心智:灵魂(profile,刚性) ｜ 此刻(state) ｜ 记忆(experiences/summary)。记忆委托 memory.py(铁律)。
"""
from __future__ import annotations

from pathlib import Path

from . import clock, memory, provenance, util
from .config import load_json, save_json
from .world import World

ROLES = ("main", "secondary", "cameo", "npc")
GROWS = {"main", "secondary"}

PROFILE_TEMPLATE = """# {name}

> 实体 id:`{id}` ｜ 戏份:{role}

## 身份
<!-- 名 / 年龄 / 外貌 / 出身 -->

## Identity Core(3-5 条刚性:原则 / 创伤 / 底线)
<!-- 成长只提议有界增量,不自由改写这里 -->

## 声音指纹(含签名句型)
<!-- 标点 / 口头禅 / 句式 / 禁止套路 -->

## 核心欲望与底线
<!-- -->

## 核心事实(身份级常驻,免检索;= anchors,硬上限约 7)
<!-- 每行一条;升格进枢纽时提炼为 anchors -->
"""


class LocalEntity:
    def __init__(self, world: World, eid: str):
        self.world = world
        self.id = eid
        self.dir = world.entities_dir / eid

    @property
    def card_path(self) -> Path:
        return self.dir / "card.json"

    def exists(self) -> bool:
        return self.card_path.exists()

    def card(self) -> dict:
        return load_json(self.card_path, {}) or {}

    @property
    def role(self) -> str:
        return self.card().get("role", "secondary")

    def grows(self) -> bool:
        return self.role in GROWS

    @classmethod
    def create(
        cls, world: World, eid: str, name: str, *, role: str = "secondary",
        prov: dict | None = None, body: str | None = None,
    ) -> "LocalEntity":
        if not util.is_id(eid):
            raise ValueError(f"实体 id 必须 kebab-case:{eid!r}")
        if role not in ROLES:
            raise ValueError(f"role 必须 ∈ {ROLES}:{role!r}")
        e = cls(world, eid)
        if e.exists():
            raise FileExistsError(f"实体已存在:{eid}")
        save_json(e.card_path, {
            "id": eid, "name": name, "role": role,
            "provenance": prov or provenance.stamp("manual"), "created": clock.now_iso(),
        })
        util.write_md(e.dir / "profile.md", body or PROFILE_TEMPLATE.format(id=eid, name=name, role=role))
        memory.write_state(e.dir, {"location": "", "mood": "", "body": "", "goal": ""})
        return e

    @classmethod
    def load(cls, world: World, eid: str) -> "LocalEntity":
        e = cls(world, eid)
        if not e.exists():
            raise FileNotFoundError(f"实体不存在:{eid}")
        return e

    def delete(self) -> None:
        import shutil
        if self.dir.exists():
            shutil.rmtree(self.dir)

    def anchors(self) -> list[str]:
        return _extract_section_lines(self.dir / "profile.md", "核心事实")

    # 核心循环委托(铁律由 memory.py 保证)
    def rebuild(self) -> dict:
        return memory.rebuild(self.dir, self.anchors())

    def retrieve(self, query: str):
        return memory.retrieve(self.dir, query)

    def sediment(self, text: str, **kw) -> dict | None:
        """按 role 门控:cameo 不写回(返回 None)。"""
        return memory.append_experience(self.dir, text, **kw) if self.grows() else None

    def update_state(self, updates: dict) -> dict:
        return memory.write_state(self.dir, updates)


def _extract_section_lines(md_path: Path, header_kw: str) -> list[str]:
    text = util.read_md(md_path)
    out, grab = [], False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("## "):
            grab = header_kw in s
            continue
        if grab and s and not s.startswith("<!--") and not s.startswith("#"):
            out.append(s.lstrip("-* ").strip())
    return [x for x in out if x][:7]
