"""世界书运行时触发引擎 —— 按上下文激活相关设定条目,注入生成/对话包。

旧路:导入的世界书只平铺进 world.md(写手得读全本)。现在结构化存 `worlds/<w>/worldbook.json`,
按"此刻在写/在聊的上下文"**触发相关条目**注入(蓝灯常驻 + 关键词命中 + selective 次键 + 递归 lore + 预算)。

借鉴 SillyTavern(Luker world-info.js 的 matchKeys/selectiveLogic/递归扫描 + Narratium world-book.ts 精简版),
只读其算法,零依赖 Python 重写。引擎确定性那一半(触发/排序/预算),内容仍是宿主模型消费。
"""
from __future__ import annotations

import random
import re

from .config import load_json, save_json

# ST selectiveLogic 码 → 内部语义
_LOGIC = {0: "and_any", 1: "not_all", 2: "not_any", 3: "and_all"}
_REGEX_KEY = re.compile(r"^/(.+)/([a-z]*)$")
_WORD_KEY = re.compile(r"[A-Za-z0-9_ ]+")
_SPLIT = re.compile(r"[,，、]")


def _path(world):
    return world.dir / "worldbook.json"


def load(world) -> dict:
    return load_json(_path(world), {"entries": []}) or {"entries": []}


def save(world, data: dict) -> None:
    save_json(_path(world), data)


# ---------- 条目规范化(吃 ST 世界书 entry 的各种字段拼写)----------
def _as_list(v) -> list[str]:
    if not v:
        return []
    if isinstance(v, str):
        return [k.strip() for k in _SPLIT.split(v) if k.strip()]
    return [str(k).strip() for k in v if str(k).strip()]


def _int(v, default):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def normalize_entry(raw: dict, source: str = "") -> dict:
    keys = _as_list(raw.get("keys") or raw.get("key"))
    sec = _as_list(raw.get("secondary_keys") or raw.get("keysecondary"))
    ext = raw.get("extensions") or {}

    def g(*names, default=None):   # 从 raw 或 extensions 任一拼写取值
        for n in names:
            if raw.get(n) not in (None, ""):
                return raw.get(n)
            if ext.get(n) not in (None, ""):
                return ext.get(n)
        return default

    logic_raw = raw.get("selectiveLogic", ext.get("selectiveLogic"))
    order = g("insertion_order", "order", default=100)
    enabled = raw.get("enabled", not raw.get("disable", False))
    name = (raw.get("comment") or raw.get("name") or (keys[0] if keys else "条目")).strip()
    return {
        "name": name, "keys": keys, "secondary_keys": sec,
        "content": (raw.get("content") or "").strip(),
        "constant": bool(raw.get("constant", False)),
        "selective": bool(raw.get("selective", bool(sec))),
        "logic": _LOGIC.get(logic_raw, "and_any"),
        "case_sensitive": bool(raw.get("case_sensitive", raw.get("caseSensitive", False))),
        "whole_word": bool(raw.get("match_whole_words", raw.get("matchWholeWords", False)) or False),
        "order": _int(order, 100),
        # 位置注入(0 before_char/1 after_char/2 an_top/3 an_bottom/4 at_depth)+ @D depth + role
        "position": _int(g("position", default=0), 0),
        "depth": _int(g("depth", default=4), 4),
        "role": _int(g("role", default=0), 0),
        "scan_depth": _int(g("scan_depth"), None) if g("scan_depth") is not None else None,
        # 概率触发
        "probability": _int(g("probability", default=100), 100),
        "use_probability": bool(g("useProbability", "use_probability", default=False)),
        # 时效(基于楼号)
        "sticky": _int(g("sticky", default=0), 0),
        "cooldown": _int(g("cooldown", default=0), 0),
        "delay": _int(g("delay", default=0), 0),
        # 互斥组
        "group": str(g("group", default="") or "").strip(),
        "group_weight": _int(g("group_weight", default=100), 100),
        "group_override": bool(g("group_override", "groupOverride", default=False)),
        "use_group_scoring": bool(g("use_group_scoring", "useGroupScoring", default=False)),
        "ignore_budget": bool(g("ignore_budget", default=False)),
        "enabled": bool(enabled),
        "source": source,
    }


def add_entries(world, raw_entries, source: str = "") -> int:
    """把(ST 或内部)条目规范化后并入世界书,返回并入数。"""
    if isinstance(raw_entries, dict):
        raw_entries = list(raw_entries.values())
    data = load(world)
    next_uid = max((e.get("uid", 0) for e in data["entries"]), default=0) + 1
    added = 0
    for raw in raw_entries or []:
        e = normalize_entry(raw, source=source)
        if e["keys"] or e["constant"]:   # 没键又非常驻的条目永不触发,丢弃
            e["uid"] = next_uid; next_uid += 1
            data["entries"].append(e)
            added += 1
    if added:
        save(world, data)
    return added


def remove_source(world, source: str) -> int:
    """撤销某来源(如导入的角色卡 eid)并入的条目。返回删除数。"""
    if not source:
        return 0
    data = load(world)
    before = len(data["entries"])
    data["entries"] = [e for e in data["entries"] if e.get("source") != source]
    removed = before - len(data["entries"])
    if removed:
        save(world, data)
    return removed


# ---------- 触发原语(matchKeys / selective 逻辑)----------
def match_key(text: str, key: str, *, case_sensitive: bool = False, whole_word: bool = False) -> bool:
    """单键命中:/regex/ 走正则;ASCII 全词走边界;其余(含中文)走子串。"""
    if not key:
        return False
    m = _REGEX_KEY.match(key)
    if m:
        try:
            return re.search(m.group(1), text, re.I if "i" in m.group(2) else 0) is not None
        except re.error:
            return False
    hay = text if case_sensitive else text.lower()
    needle = key if case_sensitive else key.lower()
    if whole_word and _WORD_KEY.fullmatch(needle.strip()):
        return re.search(r"(?:^|\W)" + re.escape(needle) + r"(?:$|\W)", hay) is not None
    return needle in hay


def entry_matches(entry: dict, buffer: str) -> bool:
    """主键命中 + (selective 时)次键按逻辑(and_any/and_all/not_any/not_all)。"""
    keys = entry.get("keys") or []
    if not keys:
        return False
    cs, ww = entry.get("case_sensitive", False), entry.get("whole_word", False)
    if not any(match_key(buffer, k, case_sensitive=cs, whole_word=ww) for k in keys):
        return False
    sec = entry.get("secondary_keys") or []
    if not entry.get("selective") or not sec:
        return True
    hits = [match_key(buffer, k, case_sensitive=cs, whole_word=ww) for k in sec]
    logic = entry.get("logic", "and_any")
    if logic == "and_all":
        return all(hits)
    if logic == "not_any":
        return not any(hits)
    if logic == "not_all":
        return not all(hits)
    return any(hits)   # and_any


# ---------- 时效状态(sticky/cooldown,按楼号锚定;持久到 worlds/<w>/wi_state/<key>.json)----------
_POS_NAME = {0: "before_char", 1: "after_char", 2: "an_top", 3: "an_bottom", 4: "at_depth"}


def _wi_state_path(world, key):
    return world.dir / "wi_state" / f"{key}.json"


def _load_state(world, key):
    return load_json(_wi_state_path(world, key), {"sticky": {}, "cooldown": {}}) or {"sticky": {}, "cooldown": {}}


def _score(entry, buffer):
    cs, ww = entry.get("case_sensitive", False), entry.get("whole_word", False)
    return sum(1 for k in (entry.get("keys") or []) if match_key(buffer, k, case_sensitive=cs, whole_word=ww))


def _filter_groups(cands, buffer, rng):
    """互斥组:同 group 只留一条(use_group_scoring→命中键最高;否则 order/weight 最高;平票取首)。"""
    by_group: dict[str, list] = {}
    out = []
    for e in cands:
        g = e.get("group", "")
        if not g:
            out.append(e)
        else:
            by_group.setdefault(g, []).append(e)
    for g, members in by_group.items():
        if any(m.get("group_override") for m in members):
            members = [m for m in members if m.get("group_override")]
        if any(m.get("use_group_scoring") for m in members):
            best = max(members, key=lambda m: (_score(m, buffer), m.get("group_weight", 100), m.get("order", 100)))
        else:
            best = max(members, key=lambda m: (m.get("group_weight", 100), m.get("order", 100)))
        out.append(best)
    return out


# ---------- 扫描(常驻 + 关键词 + selective + 递归 lore + 时效 + 概率 + 互斥组 + 位置分桶 + 预算)----------
def scan(world, context_text: str, *, floor: int | None = None, state_key: str | None = None,
         budget_chars: int = 1800, max_recursion: int = 3, flatten: bool = True,
         rng=None, dry_run: bool = False) -> dict:
    """据上下文激活世界书条目。

    floor+state_key 给定时启用时效(sticky 粘附/cooldown 冷却/delay 延迟);否则无状态(backward 兼容)。
    flatten=True 返回单 `injection` 串(旧契约);flatten=False 额外给 `buckets`(按 position/@D 分桶)。
    """
    rng = rng or random
    data = load(world)
    entries = [e for e in data.get("entries", []) if e.get("enabled", True)]
    timed_on = floor is not None and state_key is not None
    st = _load_state(world, state_key) if timed_on else {"sticky": {}, "cooldown": {}}
    by_uid = {str(e.get("uid")): e for e in entries}

    # 时效预处理:过期清理 + sticky→cooldown 交接
    if timed_on:
        for uid, end in list(st["sticky"].items()):
            if floor >= end:
                st["sticky"].pop(uid)
                e = by_uid.get(uid)
                if e and e.get("cooldown", 0) > 0:
                    st["cooldown"][uid] = floor + e["cooldown"]   # 粘完即冷却
        for uid, end in list(st["cooldown"].items()):
            if floor >= end:
                st["cooldown"].pop(uid)

    def _sticky(e):
        return timed_on and str(e.get("uid")) in st["sticky"]

    def _cooldown(e):
        return timed_on and str(e.get("uid")) in st["cooldown"]

    def _delayed(e):
        return timed_on and e.get("delay", 0) > 0 and floor < e["delay"]

    activated: list[dict] = []
    used: set = set()

    def _activate(e):
        used.add(e.get("uid", id(e)))
        activated.append(e)

    def _gated(e):
        if _delayed(e) and not _sticky(e):
            return False
        if _cooldown(e) and not _sticky(e):
            return False
        return True

    for e in entries:
        if (e.get("constant") and not _delayed(e)) or _sticky(e):   # 蓝灯常驻 + 粘附中的恒入
            _activate(e)
    buffer = (context_text or "") + "\n" + "\n".join(e.get("content", "") for e in activated)
    for _ in range(max_recursion):
        added = False
        for e in entries:
            if e.get("uid", id(e)) in used or not e.get("keys") or not _gated(e):
                continue
            if entry_matches(e, buffer):
                _activate(e)
                buffer += "\n" + e.get("content", "")
                added = True
        if not added:
            break

    # 概率筛选(sticky 免 roll)
    kept = []
    for e in activated:
        if e.get("use_probability") and e.get("probability", 100) < 100 and not _sticky(e):
            if rng.random() * 100 > e["probability"]:
                continue
        kept.append(e)
    # 互斥组
    kept = _filter_groups(kept, buffer, rng)

    # 落时效状态(新激活的设 sticky / cooldown)
    if timed_on and not dry_run:
        for e in kept:
            uid = str(e.get("uid"))
            if e.get("sticky", 0) > 0 and uid not in st["sticky"]:
                st["sticky"][uid] = floor + e["sticky"]
            elif e.get("cooldown", 0) > 0 and uid not in st["cooldown"] and not _sticky(e):
                st["cooldown"][uid] = floor + e["cooldown"]
        save_json(_wi_state_path(world, state_key), st)

    # 排序 + 预算
    kept.sort(key=lambda e: e.get("order", 100))
    out, total = [], 0
    for e in kept:
        c = (e.get("content") or "").strip()
        if not c:
            continue
        if out and not e.get("ignore_budget") and total + len(c) > budget_chars:
            continue
        out.append(e)
        total += len(c)

    injection = "\n\n".join(f"〔{e.get('name') or '设定'}〕{(e.get('content') or '').strip()}" for e in out)
    result = {
        "injection": injection, "count": len(out), "chars": total,
        "activated": [{"name": e.get("name"), "keys": e.get("keys"), "position": e.get("position", 0),
                       "constant": e.get("constant", False), "sticky": _sticky(e),
                       "source": e.get("source", "")} for e in out],
    }
    if not flatten:
        buckets = {v: [] for v in _POS_NAME.values()}
        depth_msgs = {}
        for e in out:
            txt = f"〔{e.get('name') or '设定'}〕{(e.get('content') or '').strip()}"
            if e.get("position", 0) == 4:   # @D 深度注入
                depth_msgs.setdefault((e.get("depth", 4), e.get("role", 0)), []).append(txt)
            else:
                buckets[_POS_NAME.get(e.get("position", 0), "before_char")].append(txt)
        result["buckets"] = buckets
        result["depth_msgs"] = [{"depth": d, "role": r, "content": "\n\n".join(v)}
                                for (d, r), v in sorted(depth_msgs.items())]
    return result


def summary(world) -> dict:
    data = load(world)
    es = data.get("entries", [])
    return {"total": len(es), "constant": sum(1 for e in es if e.get("constant")),
            "keyword": sum(1 for e in es if e.get("keys") and not e.get("constant"))}
