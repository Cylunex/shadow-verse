"""创作组件库 —— 把硬编码的写作工艺 / 题材配方外化成可编辑数据(全局复用)。

铁律(字节等价):**缺文件时 load_group 原样回退到内置种子(_SEED_*)**,行为与今天逐字节一致;
灌种(seed_all)只在"想编辑组件"时发生。组件分 4 类 kind,决定 entry schema + 重建方式:
  menu    dict{key:desc}        entry {key, desc}
  list    list[str]              entry {id, text}
  note    单条 str               entry {text}(单条)
  record  dict{key:{字段...}}    entry {key, ...字段}
每条 entry 带 order(排序) / enabled(停用不删) / builtin(种子来=true)。
group 是闭集:由各引擎模块的 _GROUP_DEFS 注册;管理台只增删"一条 entry",不增"一个 group"。
"""
from __future__ import annotations

from .config import COMPONENTS_DIR, load_json, save_json

KINDS = ("menu", "list", "note", "record")
_META = ("key", "id", "order", "enabled", "builtin")


# ---- 组件族注册表(闭集):懒取自各引擎模块的 _GROUP_DEFS,避免循环导入 ----
def _registry() -> dict:
    """{(family, group): (kind, title, seed)} —— 全部已登记组件组。"""
    from . import craft, recipes
    reg = {}
    for family, mod in (("craft", craft), ("recipes", recipes)):
        for group, kind, title, seed in mod._GROUP_DEFS:
            reg[(family, group)] = (kind, title, seed)
    return reg


def _path(family: str, group: str):
    return COMPONENTS_DIR / family / f"{group}.json"


# ---- 重建:存储 entries → 原生形态(仅 seeded 时走;unseeded 直接回种子)----
def _entries_to_value(kind: str, entries: list):
    rows = [e for e in sorted(entries, key=lambda e: e.get("order", 0)) if e.get("enabled", True)]
    if kind == "menu":
        return {e["key"]: e.get("desc", "") for e in rows}
    if kind == "list":
        return [e.get("text", "") for e in rows]
    if kind == "note":
        return rows[0].get("text", "") if rows else ""
    if kind == "record":
        return {e["key"]: {k: v for k, v in e.items() if k not in _META} for e in rows}
    raise ValueError(f"未知组件 kind:{kind}")


def _value_to_entries(kind: str, value) -> list:
    if kind == "menu":
        return [{"key": k, "desc": v, "order": i, "enabled": True, "builtin": True}
                for i, (k, v) in enumerate(value.items())]
    if kind == "list":
        return [{"id": str(i), "text": t, "order": i, "enabled": True, "builtin": True}
                for i, t in enumerate(value)]
    if kind == "note":
        return [{"text": value, "order": 0, "enabled": True, "builtin": True}]
    if kind == "record":
        return [{"key": k, "order": i, "enabled": True, "builtin": True, **rec}
                for i, (k, rec) in enumerate(value.items())]
    raise ValueError(f"未知组件 kind:{kind}")


# ---- 核心:读一组(缺文件 = 原样回退种子 = 字节等价)----
def load_group(family: str, group: str, kind: str, seed):
    data = load_json(_path(family, group), None)
    if not isinstance(data, dict) or "entries" not in data:
        return seed
    return _entries_to_value(kind, data["entries"])


def _doc(family: str, group: str, kind: str, title: str, seed) -> dict:
    """已落盘则返回存储 doc,否则用种子现造一份(供管理台浏览 / CRUD 落地的起点)。"""
    data = load_json(_path(family, group), None)
    if isinstance(data, dict) and "entries" in data:
        return data
    return {"family": family, "group": group, "kind": kind, "title": title,
            "entries": _value_to_entries(kind, seed)}


def _lookup(family: str, group: str):
    reg = _registry()
    if (family, group) not in reg:
        raise ValueError(f"未登记的组件组:{family}/{group}")
    return reg[(family, group)]   # (kind, title, seed)


# ---- 管理台 / CRUD ----
def list_groups() -> list[dict]:
    out = []
    for (family, group), (kind, title, seed) in sorted(_registry().items()):
        data = load_json(_path(family, group), None)
        seeded = isinstance(data, dict) and "entries" in data
        count = len(data["entries"]) if seeded else len(_value_to_entries(kind, seed))
        out.append({"family": family, "group": group, "kind": kind, "title": title,
                    "count": count, "seeded": seeded})
    return out


def get_group(family: str, group: str) -> dict:
    kind, title, seed = _lookup(family, group)
    return _doc(family, group, kind, title, seed)


def upsert(family: str, group: str, entry: dict) -> dict:
    kind, title, seed = _lookup(family, group)
    doc = _doc(family, group, kind, title, seed)
    entries = doc["entries"]
    if kind == "note":
        text = entry.get("text", "")
        if entries:
            entries[0]["text"] = text; entries[0]["builtin"] = False
        else:
            entries.append({"text": text, "order": 0, "enabled": True, "builtin": False})
    else:
        idf = "key" if kind in ("menu", "record") else "id"
        key = entry.get(idf) or entry.get("key") or entry.get("id")
        if not key:
            raise ValueError(f"entry 缺标识字段 {idf}")
        hit = next((e for e in entries if e.get(idf) == key), None)
        if hit is not None:
            hit.update(entry); hit[idf] = key; hit["builtin"] = False
        else:
            order = max((e.get("order", 0) for e in entries), default=-1) + 1
            entries.append({**entry, idf: key, "order": entry.get("order", order),
                            "enabled": entry.get("enabled", True), "builtin": False})
    save_json(_path(family, group), doc)
    return doc


def delete(family: str, group: str, key_or_id: str) -> dict:
    kind, title, seed = _lookup(family, group)
    doc = _doc(family, group, kind, title, seed)
    before = len(doc["entries"])
    doc["entries"] = [e for e in doc["entries"]
                      if e.get("key") != key_or_id and e.get("id") != key_or_id]
    save_json(_path(family, group), doc)
    return {"removed": before - len(doc["entries"]), "family": family, "group": group}


def seed_all() -> dict:
    """幂等:把内置种子写成 group 文件(同 group 已存在则跳过)。缺省不灌种=字节等价。"""
    reg = _registry()
    added = 0
    for (family, group), (kind, title, seed) in reg.items():
        p = _path(family, group)
        if p.exists():
            continue
        save_json(p, {"family": family, "group": group, "kind": kind, "title": title,
                      "entries": _value_to_entries(kind, seed)})
        added += 1
    return {"added": added, "total": len(reg)}
