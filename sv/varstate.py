"""变量状态引擎 —— 三段式 {data, rules, meta} + 深路径 + 五 op + validate 护栏。

借鉴 LittleWhiteBox State 2.0(parser/guard/variable-path),但**不引入 YAML**(守零依赖):
- data:嵌套对象/数组/标量(`关系.张三.好感` 深路径,`背包[0]` 下标)。
- rules:`{min,max,step,ro,enum}`,落库前 clamp/限幅/拒写——**模型乱写也写不坏**。
- meta:`{label,vis,color,icon,persist}`——vis∈bar/num/list/text/hidden 决定 HUD 怎么渲染;hidden 参与结算不进面板。

op 沿用现有 JSON 增量格式(交给 jsonloose 容错):`+N/-N`(数值增减或数组 push/pop)、裸值(set)、null(del)。
"""
from __future__ import annotations

import copy
import re

from .config import load_json, save_json

_SEG_IDX = re.compile(r"\[(\d+)\]")
_INC = re.compile(r"^([+-])(\d+(?:\.\d+)?)$")


# ---------- 存储(三段式,backward 兼容旧扁平 vars.json)----------
def _path(e):
    return e.dir / "vars.json"


def load(e) -> dict:
    raw = load_json(_path(e), {}) or {}
    if "data" in raw and isinstance(raw.get("data"), dict):
        raw.setdefault("rules", {})
        raw.setdefault("meta", {})
        return raw
    # 旧扁平 {key:val} → 迁移成三段式(整包当 data)
    return {"data": raw if isinstance(raw, dict) else {}, "rules": {}, "meta": {}}


def save(e, state: dict) -> None:
    save_json(_path(e), {"data": state.get("data", {}), "rules": state.get("rules", {}),
                         "meta": state.get("meta", {})})


# ---------- 深路径 ----------
def parse_path(path) -> list:
    out: list = []
    for seg in str(path).split("."):
        idxs = _SEG_IDX.findall(seg)
        name = _SEG_IDX.sub("", seg)
        if name:
            out.append(name)
        out.extend(int(i) for i in idxs)
    return out


def deep_get(data, path, default=None):
    cur = data
    for k in parse_path(path):
        if isinstance(k, int):
            if isinstance(cur, list) and 0 <= k < len(cur):
                cur = cur[k]
            else:
                return default
        elif isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur


def deep_set(data, path, value) -> None:
    keys = parse_path(path)
    cur = data
    for i, k in enumerate(keys[:-1]):
        nxt = keys[i + 1]
        if isinstance(k, int):
            while len(cur) <= k:
                cur.append({})
            if not isinstance(cur[k], (dict, list)):
                cur[k] = [] if isinstance(nxt, int) else {}
            cur = cur[k]
        else:
            if not isinstance(cur.get(k), (dict, list)):
                cur[k] = [] if isinstance(nxt, int) else {}
            cur = cur[k]
    last = keys[-1]
    if isinstance(last, int):
        while len(cur) <= last:
            cur.append(None)
        cur[last] = value
    else:
        cur[last] = value


def deep_del(data, path) -> None:
    keys = parse_path(path)
    cur = data
    for k in keys[:-1]:
        if isinstance(k, int) and isinstance(cur, list) and k < len(cur):
            cur = cur[k]
        elif isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return
    last = keys[-1]
    if isinstance(cur, dict):
        cur.pop(last, None)
    elif isinstance(cur, list) and isinstance(last, int) and last < len(cur):
        cur.pop(last)


# ---------- 规则匹配(支持通配 `关系.*.好感`)----------
def match_rule(path, rules: dict) -> dict:
    if path in rules:
        return rules[path]
    pk = parse_path(path)
    for rpath, rule in rules.items():
        rk = parse_path(rpath)
        if len(rk) != len(pk):
            continue
        if all(a == "*" or str(a) == str(b) for a, b in zip(rk, pk)):
            return rule
    return {}


def _coerce(s: str):
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        return s


def _norm(x):
    return int(x) if float(x) == int(float(x)) else round(float(x), 4)


def _clamp(v, rule):
    note = None
    if rule.get("min") is not None and v < rule["min"]:
        v, note = rule["min"], f"已托底到 {rule['min']}"
    if rule.get("max") is not None and v > rule["max"]:
        v, note = rule["max"], f"已封顶到 {rule['max']}"
    return v, note


# ---------- 单 op 结算(带护栏)----------
def apply_op(data: dict, path: str, spec, rules: dict) -> str | None:
    """对 data 路径施一个 op,返回 note(被改/被拒时)或 None。data 原地改。"""
    rule = match_rule(path, rules)
    if rule.get("ro"):
        return f"「{path}」只读,拒写"
    old = deep_get(data, path)

    if spec is None or spec == "$del":
        deep_del(data, path)
        return None
    s = str(spec).strip()

    # 数组 push/pop(+x / -x,当目标是 list)
    if isinstance(old, list):
        if s.startswith("+"):
            old.append(_coerce(s[1:]))
            return None
        if s.startswith("-"):
            val = _coerce(s[1:])
            if val in old:
                old.remove(val)
            return None

    # 数值增减
    m = _INC.match(s)
    if m and (isinstance(old, (int, float)) or old is None):
        delta = float(s)
        note = None
        step = rule.get("step")
        if step is not None and abs(delta) > step:
            delta = step if delta > 0 else -step
            note = f"「{path}」增量超步长,限到 {delta:+g}"
        v, n2 = _clamp(float(old or 0) + delta, rule)
        deep_set(data, path, _norm(v))
        return note or n2

    # enum 校验(set 路径)
    val = _coerce(s)
    if rule.get("enum") and val not in rule["enum"]:
        return f"「{path}」={s} 不在允许值,拒写"
    note = None
    if isinstance(val, (int, float)):
        val, note = _clamp(val, rule)
    deep_set(data, path, _norm(val) if isinstance(val, (int, float)) else val)
    return note


def apply_updates(data: dict, updates: dict, rules: dict) -> list[str]:
    """施一批 {路径:spec};返回所有护栏 notes。data 原地改。"""
    notes = []
    for path, spec in (updates or {}).items():
        if not path:
            continue
        n = apply_op(data, path, spec, rules)
        if n:
            notes.append(n)
    return notes


def replay(baseline: dict, updates: dict, rules: dict) -> tuple[dict, list[str]]:
    """从基线深拷贝重放增量(swipe 切候选/楼前回滚用)。返回 (新data, notes)。"""
    data = copy.deepcopy(baseline or {})
    notes = apply_updates(data, updates, rules)
    return data, notes


# ---------- 可见性(给 HUD)----------
def visible(state: dict) -> list[dict]:
    """返回非 hidden 的顶层变量 + 渲染提示(供前端 HUD)。"""
    data, meta = state.get("data", {}), state.get("meta", {})
    out = []
    for k, v in data.items():
        m = meta.get(k, {})
        if m.get("vis") == "hidden":
            continue
        out.append({"name": k, "value": v, "label": m.get("label", k),
                    "vis": m.get("vis", "list" if isinstance(v, list) else
                                  "num" if isinstance(v, (int, float)) else "text"),
                    "color": m.get("color"), "icon": m.get("icon"),
                    "min": match_rule(k, state.get("rules", {})).get("min"),
                    "max": match_rule(k, state.get("rules", {})).get("max")})
    return out
