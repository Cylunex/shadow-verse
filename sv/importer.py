"""导入器 —— 吃 SillyTavern 角色卡(V1/V2/V3,JSON 或 PNG 内嵌)+ 世界书,落成 entity/世界设定。

借鉴酒馆生态的现成资产(只读其格式,不照搬其实现)。卡→entity profile;世界书→world.md 设定条目。
零依赖:PNG 内嵌卡用标准库解 tEXt chunk(角色卡放 'chara'[v2 base64]/'ccv3'[v3])。
"""
from __future__ import annotations

import base64
import json
import struct

from . import provenance, util
from .config import save_json
from .entity import LocalEntity
from .world import World


def _png_text_chunks(b: bytes) -> dict[str, str]:
    """从 PNG 取 tEXt chunks(keyword→text)。"""
    out: dict[str, str] = {}
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        return out
    i = 8
    while i + 8 <= len(b):
        (length,) = struct.unpack(">I", b[i : i + 4])
        ctype = b[i + 4 : i + 8]
        data = b[i + 8 : i + 8 + length]
        if ctype == b"tEXt" and b"\x00" in data:
            k, v = data.split(b"\x00", 1)
            out[k.decode("latin-1")] = v.decode("latin-1")
        i += 12 + length
        if ctype == b"IEND":
            break
    return out


def parse_card(data) -> dict:
    """把 JSON 字符串 / dict / PNG bytes 统一成规范卡字典。"""
    if isinstance(data, bytes) and data[:8] == b"\x89PNG\r\n\x1a\n":
        chunks = _png_text_chunks(data)
        raw = chunks.get("ccv3") or chunks.get("chara")
        if not raw:
            raise ValueError("PNG 里没有内嵌角色卡(chara/ccv3)")
        data = base64.b64decode(raw).decode("utf-8")
    if isinstance(data, (bytes, str)):
        data = json.loads(data)
    if not isinstance(data, dict):
        raise ValueError("无法识别的角色卡格式")
    d = data.get("data", data)   # V2/V3 包在 data 里;V1 是平铺
    return {
        "name": d.get("name", "").strip() or "未命名",
        "description": d.get("description", ""),
        "personality": d.get("personality", ""),
        "scenario": d.get("scenario", ""),
        "first_mes": d.get("first_mes", ""),
        "mes_example": d.get("mes_example", ""),
        "system_prompt": d.get("system_prompt", ""),
        "post_history_instructions": d.get("post_history_instructions", ""),
        "alternate_greetings": d.get("alternate_greetings", []) or [],
        "tags": d.get("tags", []) or [],
        "creator": d.get("creator", ""),
        "character_book": d.get("character_book") or d.get("world_scenario") or None,
        "spec": data.get("spec", "v1"),
    }


def _profile_md(card: dict, eid: str, role: str) -> str:
    def sec(title, body):
        return f"## {title}\n{body.strip()}\n\n" if body and body.strip() else ""
    greetings = "\n\n".join([card["first_mes"], *card["alternate_greetings"]]).strip()
    return (
        f"# {card['name']}\n\n> 实体 id:`{eid}` ｜ 戏份:{role} ｜ 导入自 SillyTavern 角色卡({card['spec']})\n\n"
        + sec("身份", card["description"])
        + sec("Identity Core", card["personality"])
        + sec("声音指纹(对话示例)", card["mes_example"])
        + sec("场景 / 背景", card["scenario"])
        + sec("开场白(参考)", greetings)
        + sec("系统提示(原卡)", card["system_prompt"])
        + "## 核心事实\n<!-- 可由 Agent 从上文精炼为 ≤7 条 anchors -->\n"
    )


def _unique_id(world: World, base: str) -> str:
    """给导入实体一个唯一 id。中文名 slug 退化成 'x',这类一律走 imported-NNN 防撞。"""
    if base and base != "x" and util.is_id(base) and not LocalEntity(world, base).exists():
        return base
    i = 1
    while LocalEntity(world, f"imported-{i:03d}").exists():
        i += 1
    return f"imported-{i:03d}"


def import_card(world: World, card: dict, *, role: str = "secondary", as_id: str | None = None) -> dict:
    """卡 → 世界内 entity。返回 {entity, name, lorebook_entries}。"""
    name = card["name"]
    eid = as_id if (as_id and util.is_id(as_id)) else _unique_id(world, util.slug(name))
    prov = provenance.stamp("import", prompt=f"ST card:{name}")
    e = LocalEntity.create(world, eid, name, role=role, prov=prov, body=_profile_md(card, eid, role))
    c = e.card()
    if card["tags"]:
        c["tags"] = card["tags"]
    if card.get("first_mes"):
        c["greeting"] = card["first_mes"].strip()   # 开场白,对话时用
    save_json(e.card_path, c)
    n = import_lorebook(world, card.get("character_book")) if card.get("character_book") else 0
    return {"entity": eid, "name": name, "lorebook_entries": n}


def import_lorebook(world: World, book) -> int:
    """世界书 entries → 追加到 world.md 的「导入世界书」段(关键词条目)。返回条目数。"""
    if not book or not isinstance(book, dict):
        return 0
    entries = book.get("entries") or []
    if isinstance(entries, dict):
        entries = list(entries.values())
    if not entries:
        return 0
    lines = ["", "## 导入世界书(SillyTavern lorebook)"]
    for en in entries:
        keys = en.get("keys") or en.get("key") or []
        kw = "、".join(keys) if isinstance(keys, list) else str(keys)
        const = "常驻" if en.get("constant") else "关键词触发"
        content = (en.get("content") or "").strip()
        comment = (en.get("comment") or "").strip()
        lines.append(f"\n### {comment or kw or '条目'}（{const}）\n触发词:{kw or '—'}\n\n{content}")
    wp = world.dir / "world.md"
    util.write_md(wp, util.read_md(wp).rstrip() + "\n" + "\n".join(lines) + "\n")
    return len(entries)
