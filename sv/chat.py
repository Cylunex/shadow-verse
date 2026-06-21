"""实时对话 / 扮演 —— 和一个实体逐句玩(玩透镜的单角色版,单机网页用)。

人设(profile+anchors)+ 此刻 state + 记忆检索 + 对话史 + **用户身份(你扮演谁)** + **变量** → LLM 第一人称扮演。
关键:给"你"(玩家)一个稳定身份并下硬规则,治"对话里我的身份老变/被写成别的角色"。
需配 SV_PROVIDER(stub 时给引导)。作为宿主 skill 时不用这个(宿主用 play_prep)。
"""
from __future__ import annotations

import json

from . import clock, expressions, jsonloose, llm, macros, memory, util, varstate, worldbook
from .config import UNIVERSE, append_jsonl, load_json, read_jsonl, save_json
from .entity import LocalEntity
from .world import World

HISTORY_WINDOW = 12
VAR_SEP = "===变量==="


def _path(e: LocalEntity):
    return e.dir / "chat.jsonl"


def history(e: LocalEntity, n: int | None = None) -> list[dict]:
    h = read_jsonl(_path(e))
    for t in h:   # 旧格式 char 行 lazy 升级为 swipe 形态(读时补,落盘时才持久)
        if t.get("role") == "char" and "swipes" not in t:
            t["swipes"] = [t.get("text", "")]
            t["swipe_id"] = 0
            t["swipe_meta"] = [{"updates": {}}]
    return h if n is None else h[-n:]


def _new_char_row(reply: str, updates: dict, baseline: dict) -> dict:
    """一条 char 楼(swipe 形态)。text=当前候选;vars_before=楼前基线(变量可回滚的根)。"""
    ts = clock.now_iso()
    return {"role": "char", "text": reply, "ts": ts,
            "swipes": [reply], "swipe_id": 0,
            "swipe_meta": [{"updates": updates or {}, "ts": ts}],
            "vars_before": baseline}


def _last_char_ctx(h: list[dict]):
    """末楼是 char 时返回 (char_idx, user_idx|None, user_text);否则 None。"""
    if not h or h[-1].get("role") != "char":
        return None
    ci = len(h) - 1
    ui = next((j for j in range(ci - 1, -1, -1) if h[j].get("role") == "user"), None)
    return ci, ui, (h[ui].get("text", "") if ui is not None else "")


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


# ---------- 变量系统(三段式 data/rules/meta,走 varstate;每个对话一份 vars.json)----------
def vars(e: LocalEntity) -> dict:
    """返回 data 视图(backward 兼容:旧代码/前端把它当扁平表读)。"""
    return varstate.load(e)["data"]


def var_state(e: LocalEntity) -> dict:
    """完整三段式(给 HUD/AI 建卡)。"""
    return varstate.load(e)


def set_var(e: LocalEntity, name: str, value) -> dict:
    st = varstate.load(e)
    varstate.apply_op(st["data"], name, value, st["rules"])
    varstate.save(e, st)
    return st["data"]


def del_var(e: LocalEntity, name: str) -> dict:
    st = varstate.load(e)
    varstate.apply_op(st["data"], name, None, st["rules"])
    varstate.save(e, st)
    return st["data"]


_INITVARS_SYS = "你在为角色初始化一张「状态卡」,只输出一个 JSON,不要任何解释。"


def init_vars(world: World, e: LocalEntity) -> dict:
    """AI 建变量卡:从人设+世界类型识别该追踪哪些状态变量并初始化(data+rules+meta)。需 LLM。"""
    if not llm.available():
        return {"available": False, "note": "AI 建卡需配 SV_PROVIDER"}
    prof = util.read_md(e.dir / "profile.md")[:1500]
    user = (
        "基于人设与世界类型,判断这段扮演该追踪哪些状态(HP/金币/背包/关系/进度/好感…),不超过 8 个。\n"
        '只输出 JSON:{"data":{变量名:初值},'
        '"rules":{变量名:{"min":0,"max":100,"step":20,"ro":false,"enum":[]}},'
        '"meta":{变量名:{"label":"中文名","vis":"bar|num|list|text|hidden","icon":""}}}。\n'
        "规则:① 只建真会变的状态;② 数值类给 min/max;③ 角色内心真实想法标 vis:hidden;"
        '④ 关系用嵌套 {"关系":{"NPC名":{"好感":0,"态度":"中立"}}}。\n'
        f"人设:\n{prof}\n世界类型:{world.meta().get('genre', '')}\n开场:{(e.card().get('greeting') or '')[:300]}")
    j = jsonloose.loads(llm.generate(_INITVARS_SYS, user, max_tokens=700, temperature=0.3), {})
    data = j.get("data") if isinstance(j.get("data"), dict) else {}
    rules = j.get("rules") if isinstance(j.get("rules"), dict) else {}
    meta = j.get("meta") if isinstance(j.get("meta"), dict) else {}
    st = set_rules_meta(e, rules=rules, meta=meta, data=data)
    return {"available": True, "data": st["data"], "rules": st["rules"], "meta": st["meta"]}


def set_rules_meta(e: LocalEntity, rules: dict | None = None, meta: dict | None = None,
                   data: dict | None = None) -> dict:
    """整体设/并入 rules+meta(+可选初始 data)——AI 建变量卡落库用。"""
    st = varstate.load(e)
    if data is not None:
        st["data"] = data
    if rules is not None:
        st["rules"].update(rules)
    if meta is not None:
        st["meta"].update(meta)
    varstate.save(e, st)
    return st


def _apply_baseline(e: LocalEntity, baseline: dict, updates: dict) -> tuple[dict, list]:
    """从「楼前基线」重放增量(不在当前 vars 累加)——切 swipe 不越加。返回 (data, notes)。"""
    st = varstate.load(e)
    data, notes = varstate.replay(baseline, updates, st["rules"])
    st["data"] = data
    varstate.save(e, st)
    return data, notes


def _settle(e: LocalEntity, char: dict) -> dict:
    """按 char 楼当前 swipe_id,从 vars_before 重算变量(切候选/重 roll 都走它)。"""
    baseline = char.get("vars_before")
    if baseline is None:   # 旧行无基线:不回滚,保持现状
        return vars(e)
    meta = char.get("swipe_meta") or [{}]
    sid = char.get("swipe_id", 0)
    updates = (meta[sid] if 0 <= sid < len(meta) else {}).get("updates", {})
    data, _ = _apply_baseline(e, baseline, updates)
    return data


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
    dp = e.card().get("depth_prompt")   # 角色卡私货(depth_prompt),贯穿全程注入
    if isinstance(dp, dict) and (dp.get("prompt") or "").strip():
        parts.append("【角色须始终遵守】" + dp["prompt"].strip())
    if varbag:
        parts.append(
            f"当前变量:{json.dumps(varbag, ensure_ascii=False)}。若本轮该变,在正文最后另起一行写 `{VAR_SEP}`,"
            f"其下写一行 JSON(只写要变的;数值用 +N/-N 增减或写新值);没变就别写、也别提变量。")
    # 内联宏展开({{getvar}}/{{roll}}/{{random}}/{{if}})——档案/设定里可写宏,注入模型前求值
    return macros.expand("\n\n".join(parts), varbag)


def _transcript(world: World, e: LocalEntity, message: str, hist: list[dict], pl: dict) -> str:
    cname = e.card().get("name", e.id)
    label = {"user": pl["name"], "char": cname}
    convo = "\n".join(f"{label[t['role']]}:{t['text']}" for t in hist)
    return (convo + "\n" if convo else "") + f"{pl['name']}:{message}\n{cname}:"


def _split_vars(reply: str):
    prose, _, tail = reply.partition(VAR_SEP)
    updates = jsonloose.loads(tail, {}) if tail.strip() else {}
    return prose.strip(), updates


def _generate(world: World, e: LocalEntity, message: str, hist: list[dict], pl: dict) -> tuple[str, dict]:
    varbag = vars(e)
    sys = _system(world, e, pl, varbag)
    mem = memory.retrieve(e.dir, message)
    if mem:
        sys += "\n\n该想起的事:" + " / ".join(m["text"] for m in mem)
    wb = worldbook.scan(world, message + "\n" + " ".join(h["text"] for h in hist[-4:]),
                        floor=len(hist), state_key=e.id, budget_chars=1000)   # 启用时效(sticky/cooldown/delay)
    if wb["injection"]:
        sys += "\n\n相关世界设定(触发):\n" + wb["injection"]
    raw = llm.generate(sys, _transcript(world, e, message, hist, pl)).strip()
    prose, updates = _split_vars(raw)
    return prose, updates


def _rewrite(e: LocalEntity, turns: list[dict]) -> None:
    if _path(e).exists():
        _path(e).unlink()
    for t in turns:
        append_jsonl(_path(e), t)


def _emotion(world: World, e: LocalEntity, text: str) -> dict | None:
    """该实体若已生成表情立绘,对回复分类情绪 → {emotion, sprite, zh}(给前端换立绘);否则 None。"""
    pdir = e.dir / "portraits"
    sprites = {}
    if pdir.exists():
        for p in sorted(pdir.glob("*.png")):
            if p.stem in expressions.EMOTION_PROMPT:
                sprites[p.stem] = f"worlds/{world.id}/entities/{e.id}/portraits/{p.stem}.png"
    if not sprites:
        return None
    emo = expressions.classify_emotion(text, list(sprites))
    return {"emotion": emo, "sprite": sprites.get(emo), "zh": expressions.EMOTION_ZH.get(emo, emo)}


def turn(world: World, e: LocalEntity, message: str) -> dict:
    if not llm.available():
        return {"available": False,
                "reply": "（还没配 LLM,没法真正对话。去左边 ⚙ 设置 填一个 provider + key,回来就能聊了。）"}
    pl = player()
    baseline = vars(e)   # 楼前基线(本楼变量回滚的根)
    reply, updates = _generate(world, e, message, history(e, HISTORY_WINDOW), pl)
    append_jsonl(_path(e), {"role": "user", "text": message, "ts": clock.now_iso()})
    append_jsonl(_path(e), _new_char_row(reply, updates, baseline))
    newvars, notes = _apply_baseline(e, baseline, updates)
    return {"available": True, "reply": reply, "vars": newvars, "var_changed": list(updates or {}),
            "var_notes": notes, "swipe_id": 0, "swipe_n": 1, "emotion": _emotion(world, e, reply)}


# ---------- swipe(一楼多候选;只作用于末楼)----------
def swipe_add(world: World, e: LocalEntity) -> dict:
    """重生成一个新候选,追加到末楼 swipes 并切过去(右滑生成,不覆盖旧候选)。"""
    if not llm.available():
        return {"available": False, "reply": "（未配 LLM）"}
    h = history(e)
    ctx = _last_char_ctx(h)
    if ctx is None:
        return {"available": True, "reply": "", "note": "没有可生成候选的对话"}
    ci, ui, user_text = ctx
    char = h[ci]
    prior = (h[:ui] if ui is not None else h[:ci])[-HISTORY_WINDOW:]
    reply, updates = _generate(world, e, user_text, prior, player())
    char["swipes"].append(reply)
    char["swipe_meta"].append({"updates": updates or {}, "ts": clock.now_iso()})
    char["swipe_id"] = len(char["swipes"]) - 1
    char["text"] = reply
    _rewrite(e, h)
    newvars = _settle(e, char)
    return {"available": True, "reply": reply, "swipe_id": char["swipe_id"],
            "swipe_n": len(char["swipes"]), "vars": newvars, "var_changed": list(updates or {}),
            "emotion": _emotion(world, e, reply)}


def swipe_select(e: LocalEntity, index: int) -> dict:
    """切到末楼已存在的候选(不调 LLM),并回滚变量到该候选。"""
    h = history(e)
    if not h or h[-1].get("role") != "char":
        return {"available": True, "note": "无可切换的回复"}
    char = h[-1]
    n = len(char.get("swipes", []))
    if n == 0:
        return {"available": True, "note": "无候选"}
    char["swipe_id"] = max(0, min(int(index), n - 1))
    char["text"] = char["swipes"][char["swipe_id"]]
    _rewrite(e, h)
    newvars = _settle(e, char)
    return {"available": True, "reply": char["text"], "swipe_id": char["swipe_id"],
            "swipe_n": n, "vars": newvars}


def swipe_next(world: World, e: LocalEntity, delta: int = 1) -> dict:
    """左右切候选;右滑到末尾时自动生成新候选(=swipe_add)。"""
    h = history(e)
    if not h or h[-1].get("role") != "char":
        return {"available": True, "note": "无可切换的回复"}
    char = h[-1]
    n = len(char.get("swipes", []))
    nxt = char.get("swipe_id", 0) + int(delta)
    if nxt >= n and delta > 0:
        return swipe_add(world, e)
    return swipe_select(e, max(0, nxt))


def regenerate(world: World, e: LocalEntity) -> dict:
    """重 roll —— 升级为 swipe_add(追加候选而非覆盖,旧回复可切回)。"""
    return swipe_add(world, e)


def floor_regenerate(world: World, e: LocalEntity, idx: int) -> dict:
    """从第 idx 楼重生成:截断其后所有楼,对该楼对应的 user 输入重新生成一条回复。

    变量回滚到被截断段之前(用首个被弃 char 楼的 vars_before),再重放新回复的增量。
    """
    if not llm.available():
        return {"available": False, "reply": "（未配 LLM）"}
    h = history(e)
    if idx < 0 or idx >= len(h):
        return {"available": True, "note": "楼层越界"}
    row = h[idx]
    if row.get("role") == "char":
        ui = next((j for j in range(idx - 1, -1, -1) if h[j].get("role") == "user"), None)
        if ui is None:
            return {"available": True, "note": "该楼无对应用户输入"}
        keep, prior, user_text = h[:idx], h[:ui], h[ui].get("text", "")
        baseline = row.get("vars_before", vars(e))
    else:   # user 楼:重生成它的回复
        nxt = h[idx + 1] if idx + 1 < len(h) and h[idx + 1].get("role") == "char" else None
        keep, prior, user_text = h[:idx + 1], h[:idx], row.get("text", "")
        baseline = (nxt or {}).get("vars_before", vars(e))
    reply, updates = _generate(world, e, user_text, prior[-HISTORY_WINDOW:], player())
    char = _new_char_row(reply, updates, baseline)
    _rewrite(e, keep + [char])
    newvars, notes = _apply_baseline(e, baseline, updates)
    return {"available": True, "reply": reply, "floor": len(keep), "swipe_id": 0, "swipe_n": 1,
            "vars": newvars, "var_changed": list(updates or {}), "var_notes": notes,
            "emotion": _emotion(world, e, reply)}


def undo_last(e: LocalEntity) -> dict:
    h = history(e)
    if h and h[-1]["role"] == "char":
        h = h[:-1]
    if h and h[-1]["role"] == "user":
        h = h[:-1]
    _rewrite(e, h)
    return {"ok": True, "remaining": len(h)}
