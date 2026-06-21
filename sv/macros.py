"""精简内联宏 —— 只读取值/骰子/随机/条件,不写变量(写操作走 ===变量=== 结算块,过 guard 校验)。

借鉴 STScript 但**不上完整 CST 解析器**(那是上千行的脚本语言),只做 ~一组正则替换:
  {{getvar::路径}}  取变量(支持 `关系.张三.好感` 深路径) · {{roll::3d6}} / {{roll::20}}  骰子
  {{random::a,b,c}}  随机选一 · {{if::路径>10::真::假}}  简单条件(操作数可为变量路径或字面量)
用在角色档案/世界设定注入模型前 + HUD 渲染前。随机仅来自这里(可注入 rng,可复现)。
"""
from __future__ import annotations

import random
import re

from . import varstate

_GET = re.compile(r"\{\{getvar::([^}]+)\}\}", re.I)
_ROLL = re.compile(r"\{\{roll::([^}]+)\}\}", re.I)
_RAND = re.compile(r"\{\{random::([^}]+)\}\}", re.I)
_IF = re.compile(r"\{\{if::\s*([^:}]+?)\s*(>=|<=|==|!=|>|<)\s*([^:}]+?)\s*::([^:}]*)::([^}]*)\}\}", re.I)


def _val_str(v):
    if v is None:
        return ""
    if isinstance(v, list):
        return "、".join(str(x) for x in v)
    return str(v)


def _resolve(token: str, data: dict):
    """操作数:先当变量深路径取,取不到再当字面量。"""
    v = varstate.deep_get(data, token.strip())
    return v if v is not None else token.strip()


def expand(text: str, data: dict | None = None, rng=None) -> str:
    if not text or "{{" not in text:
        return text or ""
    rng = rng or random
    data = data or {}

    text = _GET.sub(lambda m: _val_str(varstate.deep_get(data, m.group(1).strip())), text)

    def _roll(m):
        spec = m.group(1).strip().lower()
        dm = re.fullmatch(r"(\d+)d(\d+)", spec)
        if dm:
            n, faces = int(dm.group(1)), int(dm.group(2))
            return str(sum(rng.randint(1, max(1, faces)) for _ in range(min(n, 100))))
        return str(rng.randint(1, int(spec))) if spec.isdigit() else m.group(0)
    text = _ROLL.sub(_roll, text)

    text = _RAND.sub(lambda m: rng.choice([x.strip() for x in m.group(1).split(",") if x.strip()] or [""]), text)

    def _cond(m):
        a, op, b, t, f = m.groups()
        av, bv = _resolve(a, data), _resolve(b, data)
        try:
            av, bv = float(av), float(bv)
        except (TypeError, ValueError):
            av, bv = str(av), str(bv)
        res = {">": av > bv, "<": av < bv, ">=": av >= bv, "<=": av <= bv,
               "==": av == bv, "!=": av != bv}.get(op, False)
        return t if res else f
    return _IF.sub(_cond, text)
