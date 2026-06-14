"""实时对话 / 扮演 —— 和一个实体逐句玩(玩透镜的单角色版,单机网页用)。

人设(profile+anchors)+ 此刻 state + 记忆检索 + 对话史 + **用户身份(你扮演谁)** + **变量** → LLM 第一人称扮演。
关键:给"你"(玩家)一个稳定身份并下硬规则,治"对话里我的身份老变/被写成别的角色"。
需配 SV_PROVIDER(stub 时给引导)。作为宿主 skill 时不用这个(宿主用 play_prep)。
"""
from __future__ import annotations

import json
import re

from . import clock, llm, memory, util
from .config import UNIVERSE, append_jsonl, load_json, read_jsonl, save_json
from .entity import LocalEntity
from .world import World

HISTORY_WINDOW = 12
VAR_SEP = "===变量==="


def _path(e: LocalEntity):
    return e.dir / "chat.jsonl"


def history(e: LocalEntity, n: int | None = None) -> list[dict]:
    h = read_jsonl(_path(e))
    return h if n is None else h[-n:]


def greeting(e: LocalEntity) -> str:
    return (e.card().get("greeting") or "").strip() or f"（{e.card().get('name', e.id)} 抬眼看了你一下。）"


def clear(e: LocalEntity) -> None:
    if _path(e).exists():
        _path(e).unlink()


# ---------- 玩家身份(你扮演谁)----------
def _player_path():
    return UNIVERSE / "player.json"


def player() -> dict:
    p = load_json(_player_path(), None)
    if not p:
        return {"name": "你", "persona": ""}
    return {"name": p.get("name") or "你", "persona": p.get("persona", "")}


def set_player(name: str, persona: str = "") -> dict:
    p = {"name": (name or "你").strip(), "persona": (persona or "").strip()}
    save_json(_player_path(), p)
    return p


# ---------- 变量系统(简化:每个对话一份 vars.json)----------
def _vars_path(e: LocalEntity):
    return e.dir / "vars.json"


def vars(e: LocalEntity) -> dict:
    return load_json(_vars_path(e), {}) or {}


def set_var(e: LocalEntity, name: str, value) -> dict:
    v = vars(e)
    v[name] = _apply_one(v.get(name), value)
    save_json(_vars_path(e), v)
    return v


def del_var(e: LocalEntity, name: str) -> dict:
    v = vars(e); v.pop(name, None); save_json(_vars_path(e), v); return v


def _apply_one(old, spec):
    """spec 为 '+5'/'-3' 时按数值增减(old 当数字),否则直接设为 spec。"""
    s = str(spec).strip()

    def _norm(x):   # 整数就显示整数,不留 .0
        return int(x) if float(x) == int(float(x)) else round(float(x), 4)

    if re.fullmatch(r"[+-]\d+(\.\d+)?", s):
        try:
            return _norm(float(old or 0) + float(s))
        except (TypeError, ValueError):
            return s
    if re.fullmatch(r"-?\d+(\.\d+)?", s):
        return _norm(s)
    return spec


def _apply_updates(e: LocalEntity, updates: dict) -> dict:
    v = vars(e)
    for k, spec in (updates or {}).items():
        if k:
            v[k] = _apply_one(v.get(k), spec)
    save_json(_vars_path(e), v)
    return v


# ---------- 提示词 ----------
def _system(world: World, e: LocalEntity, pl: dict, varbag: dict) -> str:
    name = e.card().get("name", e.id)
    parts = [
        f"你只扮演「{name}」这一个角色,第一人称,保持人设与说话风格。",
        f"人物档案:\n{util.read_md(e.dir / 'profile.md')[:2500]}",
    ]
    if e.anchors():
        parts.append("绝不违背的底线:" + "；".join(e.anchors()))
    st = memory.read_state(e.dir)
    now = " ".join(x for x in (st.get("location", ""), st.get("mood", "")) if x)
    if now:
        parts.append(f"此刻:{now}")
    parts.append(f"世界背景:{world.meta().get('name', '')}({world.meta().get('genre', '')})。")
    # 用户身份 + 铁律(治身份漂移)
    who = f"和你对话的是「{pl['name']}」" + (f"——{pl['persona']}" if pl.get("persona") else "")
    parts.append(
        f"【对话铁律】{who}。\n"
        f"① 只写{name}的话与动作;② 绝不替{pl['name']}说话、绝不描述{pl['name']}的动作/想法/选择、"
        f"绝不把{pl['name']}写成别的角色或NPC;③ 说完就停,等{pl['name']}回应;④ 不跳出角色、不自报AI、不复述设定、不加旁白。")
    if varbag:
        parts.append(
            f"当前变量:{json.dumps(varbag, ensure_ascii=False)}。若本轮该变,在正文最后另起一行写 `{VAR_SEP}`,"
            f"其下写一行 JSON(只写要变的;数值用 +N/-N 增减或写新值);没变就别写、也别提变量。")
    return "\n\n".join(parts)


def _transcript(world: World, e: LocalEntity, message: str, hist: list[dict], pl: dict) -> str:
    cname = e.card().get("name", e.id)
    label = {"user": pl["name"], "char": cname}
    convo = "\n".join(f"{label[t['role']]}:{t['text']}" for t in hist)
    return (convo + "\n" if convo else "") + f"{pl['name']}:{message}\n{cname}:"


def _split_vars(reply: str):
    prose, _, tail = reply.partition(VAR_SEP)
    updates = {}
    if tail.strip():
        try:
            m = re.search(r"\{.*\}", tail, re.S)
            updates = json.loads(m.group(0)) if m else {}
        except Exception:
            updates = {}
    return prose.strip(), updates


def _generate(world: World, e: LocalEntity, message: str, hist: list[dict], pl: dict) -> tuple[str, dict]:
    varbag = vars(e)
    sys = _system(world, e, pl, varbag)
    mem = memory.retrieve(e.dir, message)
    if mem:
        sys += "\n\n该想起的事:" + " / ".join(m["text"] for m in mem)
    raw = llm.generate(sys, _transcript(world, e, message, hist, pl)).strip()
    prose, updates = _split_vars(raw)
    return prose, updates


def _rewrite(e: LocalEntity, turns: list[dict]) -> None:
    if _path(e).exists():
        _path(e).unlink()
    for t in turns:
        append_jsonl(_path(e), t)


def turn(world: World, e: LocalEntity, message: str) -> dict:
    if not llm.available():
        return {"available": False,
                "reply": "（还没配 LLM,没法真正对话。去左边 ⚙ 设置 填一个 provider + key,回来就能聊了。）"}
    pl = player()
    reply, updates = _generate(world, e, message, history(e, HISTORY_WINDOW), pl)
    append_jsonl(_path(e), {"role": "user", "text": message, "ts": clock.now_iso()})
    append_jsonl(_path(e), {"role": "char", "text": reply, "ts": clock.now_iso()})
    newvars = _apply_updates(e, updates) if updates else vars(e)
    return {"available": True, "reply": reply, "vars": newvars, "var_changed": list(updates or {})}


def regenerate(world: World, e: LocalEntity) -> dict:
    if not llm.available():
        return {"available": False, "reply": "（未配 LLM）"}
    h = history(e)
    if h and h[-1]["role"] == "char":
        h = h[:-1]
    if not h or h[-1]["role"] != "user":
        return {"available": True, "reply": "", "note": "没有可重生成的对话"}
    last_user = h[-1]["text"]
    reply, _ = _generate(world, e, last_user, h[:-1], player())   # 重 roll 不改变量(避免重复结算)
    _rewrite(e, h + [{"role": "char", "text": reply, "ts": clock.now_iso()}])
    return {"available": True, "reply": reply, "vars": vars(e)}


def undo_last(e: LocalEntity) -> dict:
    h = history(e)
    if h and h[-1]["role"] == "char":
        h = h[:-1]
    if h and h[-1]["role"] == "user":
        h = h[:-1]
    _rewrite(e, h)
    return {"ok": True, "remaining": len(h)}
