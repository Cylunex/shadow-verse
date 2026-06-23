"""实时对话 / 扮演 —— 和一个实体逐句玩(玩透镜的单角色版,单机网页用)。

人设(profile+anchors)+ 此刻 state + 记忆检索 + 对话史 + **用户身份(你扮演谁)** + **变量** → LLM 第一人称扮演。
关键:给"你"(玩家)一个稳定身份并下硬规则,治"对话里我的身份老变/被写成别的角色"。
需配 SV_PROVIDER(stub 时给引导)。作为宿主 skill 时不用这个(宿主用 play_prep)。
"""
from __future__ import annotations

import json
import os
import tempfile
import threading

from . import clock, config, expressions, importer, jsonloose, llm, macros, memory, util, varstate, worldbook
from .config import UNIVERSE, append_jsonl, load_json, read_jsonl, save_json
from .entity import LocalEntity
from .lens import commit_core       # RP 落世界线走统一写入口
from .thread import Thread
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


def greetings(e: LocalEntity) -> list[str]:
    """该角色的全部开场白(主 + alternate);卡没给则空。"""
    c = e.card()
    gs = c.get("greetings")
    if isinstance(gs, list) and gs:
        return [g for g in gs if (g or "").strip()]
    g = (c.get("greeting") or "").strip()
    return [g] if g else []


def greeting_id(e: LocalEntity) -> int:
    gs = greetings(e)
    i = int((load_json(_meta_path(e), {}) or {}).get("greeting_id", 0))
    return i if 0 <= i < len(gs) else 0


def set_greeting(e: LocalEntity, idx: int) -> dict:
    """选用第 idx 个开场白(对话还没开始时可切;开场一旦落为首楼即固定)。"""
    meta = load_json(_meta_path(e), {}) or {}
    gs = greetings(e)
    meta["greeting_id"] = max(0, min(int(idx), max(0, len(gs) - 1)))
    save_json(_meta_path(e), meta)
    return {"ok": True, "greeting_id": meta["greeting_id"], "greeting": greeting(e)}


def greeting(e: LocalEntity) -> str:
    gs = greetings(e)
    if gs:
        return gs[greeting_id(e)]
    return f"（{e.card().get('name', e.id)} 抬眼看了你一下。）"


def _ensure_opening(e: LocalEntity, baseline: dict) -> None:
    """开聊前:若历史为空且卡确有开场白,把选中的开场白落为首楼(进上下文 + 永久可见/可编辑)。"""
    if history(e) or not greetings(e):
        return
    append_jsonl(_path(e), _new_char_row(greeting(e), {}, baseline))


def clear(e: LocalEntity) -> None:
    if _path(e).exists():
        _path(e).unlink()
    if _meta_path(e).exists():           # 重置自动总结进度,新对话从头算
        _meta_path(e).unlink()


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


# ---------- 作者笔记(Author's Note:导演旁注,按角色存,注入系统提示)----------
def author_note(e: LocalEntity) -> dict:
    j = load_json(e.dir / "authornote.json", None) or {}
    return {"text": j.get("text", "")}


def set_author_note(e: LocalEntity, text: str) -> dict:
    save_json(e.dir / "authornote.json", {"text": (text or "").strip()})
    return author_note(e)


# ---------- 快速回复(Quick Replies:全局自定义按钮,点一下发一句)----------
def _qr_path():
    return UNIVERSE / "quickreplies.json"


def quick_replies() -> list[dict]:
    j = load_json(_qr_path(), None) or []
    return [{"label": x.get("label", ""), "message": x.get("message", "")}
            for x in j if isinstance(x, dict) and x.get("message")]


def set_quick_replies(items: list[dict]) -> list[dict]:
    clean = [{"label": (x.get("label") or x.get("message", ""))[:24], "message": (x.get("message") or "").strip()}
             for x in (items or []) if isinstance(x, dict) and (x.get("message") or "").strip()]
    save_json(_qr_path(), clean)
    return clean


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
    an = (author_note(e).get("text") or "").strip()   # 作者笔记(导演旁注,贯穿注入)
    if an:
        parts.append("【作者笔记 · 创作方向,始终留意但不要复述】" + an)
    if varbag:
        parts.append(
            f"当前变量:{json.dumps(varbag, ensure_ascii=False)}。若本轮该变,在正文最后另起一行写 `{VAR_SEP}`,"
            f"其下写一行 JSON(只写要变的;数值用 +N/-N 增减或写新值);没变就别写、也别提变量。")
    core = macros.expand("\n\n".join(parts), varbag)
    # 预设(ST 采样集+提示词模块):作者写的系统/越狱/文风模块作为前置层叠加;
    # 引擎核心(人设/铁律/变量协议)始终保留在后、最终权威,预设无法覆盖正确性。
    pre = _active_preset()
    if pre:
        author = macros.expand(importer.assemble_preset(pre, slots={}), varbag).strip()
        if author:
            return author + "\n\n" + core
    # 内联宏展开({{getvar}}/{{roll}}/{{random}}/{{if}})——档案/设定里可写宏,注入模型前求值
    return core


def _active_preset():
    """当前生效的预设(config.PRESET 指定且存在)——没有则 None,走引擎原生系统提示。"""
    pid = getattr(config, "PRESET", "") or ""
    if not pid:
        return None
    try:
        return importer.load_preset(pid)
    except Exception:  # noqa: BLE001 — 预设被删/损坏时静默退回原生
        return None


def _transcript(world: World, e: LocalEntity, message: str, hist: list[dict], pl: dict) -> str:
    cname = e.card().get("name", e.id)
    label = {"user": pl["name"], "char": cname}
    convo = "\n".join(f"{label[t['role']]}:{t['text']}" for t in hist)
    return (convo + "\n" if convo else "") + f"{pl['name']}:{message}\n{cname}:"


def _split_vars(reply: str):
    prose, _, tail = reply.partition(VAR_SEP)
    updates = jsonloose.loads(tail, {}) if tail.strip() else {}
    return prose.strip(), updates


def _build_prompt(world: World, e: LocalEntity, message: str, hist: list[dict], pl: dict) -> tuple[str, str]:
    """组装 (system, transcript)。供阻塞生成与流式生成共用,保证两条路提示词一致。"""
    varbag = vars(e)
    sys = _system(world, e, pl, varbag)
    mem = memory.retrieve(e.dir, message)
    if mem:
        sys += "\n\n该想起的事:" + " / ".join(m["text"] for m in mem)
    wb = worldbook.scan(world, message + "\n" + " ".join(h["text"] for h in hist[-4:]),
                        floor=len(hist), state_key=e.id, budget_chars=1000)   # 启用时效(sticky/cooldown/delay)
    if wb["injection"]:
        sys += "\n\n相关世界设定(触发):\n" + wb["injection"]
    return sys, _transcript(world, e, message, hist, pl)


def _gen_params() -> dict | None:
    """当前生效预设的采样参数(temperature/top_p/penalties/seed/max_tokens…)→ 传给 LLM。无预设则 None。"""
    pre = _active_preset()
    return (pre.get("sampling") or None) if pre else None


def _generate(world: World, e: LocalEntity, message: str, hist: list[dict], pl: dict) -> tuple[str, dict]:
    sys, transcript = _build_prompt(world, e, message, hist, pl)
    raw = llm.generate(sys, transcript, params=_gen_params()).strip()
    prose, updates = _split_vars(raw)
    return prose, updates


class _StreamSplitter:
    """流式时只吐正文增量,把尾部变量块(VAR_SEP 起)挡在外面(用户看不到变量 JSON)。"""

    def __init__(self, sep: str):
        self.sep = sep
        self.buf = ""
        self.emitted = 0
        self.cut = False

    def feed(self, piece: str) -> str:
        self.buf += piece
        if self.cut:
            return ""                         # 已进入变量段,正文不再吐
        i = self.buf.find(self.sep)
        if i != -1:
            self.cut = True
            safe = self.buf[:i]
        else:                                 # 留出 sep-1 字符,防把半截分隔符当正文吐出去
            safe = self.buf[:max(self.emitted, len(self.buf) - len(self.sep) + 1)]
        out = safe[self.emitted:]
        self.emitted = len(safe)
        return out

    def flush(self) -> str:
        if self.cut:
            return ""
        out = self.buf[self.emitted:]
        self.emitted = len(self.buf)
        return out


def stream_turn(world: World, e: LocalEntity, message: str):
    """流式一轮:逐块 yield ("delta", 文本);收尾 yield ("done", 元信息)。落盘/变量/表情在 done 时结算。"""
    if not llm.available():
        yield ("done", {"available": False,
                         "reply": "（还没配 LLM,没法真正对话。去左边 ⚙ 设置 填一个 provider + key,回来就能聊了。）"})
        return
    pl = player()
    baseline = vars(e)
    _ensure_opening(e, baseline)   # 开场白落为首楼(进上下文)
    hist = history(e, HISTORY_WINDOW)
    sys, transcript = _build_prompt(world, e, message, hist, pl)
    # 用户消息先落盘:中途出错 / 用户中止都不会把玩家这句弄丢
    append_jsonl(_path(e), {"role": "user", "text": message, "ts": clock.now_iso()})
    splitter = _StreamSplitter(VAR_SEP)
    raw_parts: list[str] = []
    persisted = False
    try:
        for piece in llm.stream(sys, transcript, params=_gen_params()):
            raw_parts.append(piece)
            out = splitter.feed(piece)
            if out:
                yield ("delta", out)
        tail = splitter.flush()
        if tail:
            yield ("delta", tail)
        prose, updates = _split_vars("".join(raw_parts).strip())
        append_jsonl(_path(e), _new_char_row(prose, updates, baseline))
        persisted = True
        newvars, notes = _apply_baseline(e, baseline, updates)
        yield ("done", {"available": True, "reply": prose, "vars": newvars, "var_changed": list(updates or {}),
                        "var_notes": notes, "swipe_id": 0, "swipe_n": 1, "emotion": _emotion(world, e, prose)})
        _kick_summary(world, e)           # done 已发,这里只是快速 spawn 后台线程,不拖慢客户端
        _rp_commit(world, e, message, prose, updates)   # RP → 世界线
    finally:
        if not persisted:                 # 流中途异常 / 客户端中止(GeneratorExit):把已出的部分也落盘,刷新后不蒸发
            prose, updates = _split_vars("".join(raw_parts).strip())
            if prose:
                append_jsonl(_path(e), _new_char_row(prose, updates, baseline))


def _rewrite(e: LocalEntity, turns: list[dict]) -> None:
    """原子重写 chat.jsonl:同目录临时文件 + os.replace。读者要么看到旧全本要么新全本,
    不再有 unlink 之后、re-append 之前那个 [] / 截断态的窗口;崩溃也不会留下半截文件。"""
    p = _path(e)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=".chat.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for t in turns:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")
        os.replace(tmp, p)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


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


# ---------- RP 落世界线(不放弃世界线:每轮 RP 进入世界的时间轴 thread.beats,RP 不再是孤岛)----------
def _rp_thread(world: World, e: LocalEntity) -> Thread:
    """这场 RP 的世界线 thread:chat_meta.thread_id 指定则用(可绑某副本),否则自动建/取 rp-<eid>。
    它落在世界的 threads/ 下,所以 RP 事件自然进入【世界】的时间轴(世界与魂同等一等)。"""
    meta = load_json(_meta_path(e), {}) or {}
    tid = meta.get("thread_id")
    if tid and Thread(world, tid).exists():
        return Thread(world, tid)
    tid = f"rp-{e.id}"
    if not Thread(world, tid).exists():
        Thread.create(world, tid, f"{e.card().get('name', e.id)} · RP 线", genre=world.meta().get("genre", ""))
    meta["thread_id"] = tid
    save_json(_meta_path(e), meta)
    return Thread(world, tid)


def _rp_beat_text(message: str, prose: str) -> str:
    snip = lambda s: " ".join((s or "").split())[:60]   # noqa: E731
    return snip(prose) or snip(message) or "（一轮对话）"


def _rp_commit(world: World, e: LocalEntity, message: str, prose: str, updates: dict) -> None:
    """把这一轮 RP 落到世界线(thread.beats,走统一 commit_core)。门控 config.RP_COMMIT,关时零行为=旧逻辑。"""
    if not config.RP_COMMIT or not (prose or "").strip():
        return
    try:
        t = _rp_thread(world, e)
        commit_core(world, t, lens="play", where=f"play:{t.id}", beat=_rp_beat_text(message, prose), mark=True)
    except Exception:  # noqa: BLE001 — 落世界线绝不阻断对话
        pass


def turn(world: World, e: LocalEntity, message: str) -> dict:
    if not llm.available():
        return {"available": False,
                "reply": "（还没配 LLM,没法真正对话。去左边 ⚙ 设置 填一个 provider + key,回来就能聊了。）"}
    pl = player()
    baseline = vars(e)   # 楼前基线(本楼变量回滚的根)
    _ensure_opening(e, baseline)   # 开场白落为首楼(进上下文)
    reply, updates = _generate(world, e, message, history(e, HISTORY_WINDOW), pl)
    append_jsonl(_path(e), {"role": "user", "text": message, "ts": clock.now_iso()})
    append_jsonl(_path(e), _new_char_row(reply, updates, baseline))
    newvars, notes = _apply_baseline(e, baseline, updates)
    _kick_summary(world, e)
    _rp_commit(world, e, message, reply, updates)   # RP → 世界线
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
        # 基线=被丢弃段里「第一条 char 楼的 vars_before」(扫,不只看 idx+1),否则才回退当前 vars。
        # 治:先 delete_floor 删掉 idx+1 的 char 楼后,baseline 错用当前 vars(把已被丢弃的增量重叠加进新回复)。
        first_discarded_char = next(
            (r for r in h[idx + 1:] if r.get("role") == "char" and "vars_before" in r), None)
        keep, prior, user_text = h[:idx + 1], h[:idx], row.get("text", "")
        baseline = (first_discarded_char or {}).get("vars_before", vars(e))
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


# ---------- 楼层编辑 / 删除(任意楼,不只末楼)----------
def edit_floor(e: LocalEntity, idx: int, text: str) -> dict:
    """改任意一楼的文字。char 楼同步改当前候选,免切 swipe 时回退掉编辑。"""
    h = history(e)
    if idx < 0 or idx >= len(h):
        return {"ok": False, "note": "楼层越界"}
    row = h[idx]
    text = (text or "").strip()
    row["text"] = text
    if row.get("role") == "char":
        sw, sid = row.get("swipes"), row.get("swipe_id", 0)
        if isinstance(sw, list) and 0 <= sid < len(sw):
            sw[sid] = text
    _rewrite(e, h)
    return {"ok": True}


def delete_floor(e: LocalEntity, idx: int) -> dict:
    """删任意一楼。删后从「最新还活着的 char 楼」按其 vars_before+所选 swipe 增量重算变量,
    免得被删 char 楼的增量永久卡在 vars.json 里(链上没有任何操作会再去重算它)。
    若删的是 char 楼且之后没有其它 char 楼了,直接把变量回退到被删楼的 vars_before。"""
    h = history(e)
    if idx < 0 or idx >= len(h):
        return {"ok": False, "note": "楼层越界"}
    removed = h[idx]
    del h[idx]
    _rewrite(e, h)
    last_char = next((r for r in reversed(h) if r.get("role") == "char"), None)
    if last_char is not None:
        _settle(e, last_char)
    elif removed.get("role") == "char" and "vars_before" in removed:
        st = varstate.load(e); st["data"] = removed["vars_before"] or {}; varstate.save(e, st)
    return {"ok": True, "remaining": len(h)}


# ---------- 自动总结(滚出模型窗口的对话 → 压缩进长期记忆,供 retrieve 召回)----------
_SUMMARY_SYS = ("你在把一段角色扮演对话压缩成「记忆」。只输出 2-3 句中文要点"
                "(关键事件 / 关系或态度变化 / 承诺与约定 / 状态变更),不要解说、不要分点、不要复述原文。")


def _meta_path(e: LocalEntity):
    return e.dir / "chat_meta.json"


def _summary_upto(e: LocalEntity) -> int:
    return int((load_json(_meta_path(e), {}) or {}).get("summarized_upto", 0))


def _set_summary_upto(e: LocalEntity, n: int) -> None:
    """read-merge-write:不要把整张 chat_meta.json 覆成只剩 summarized_upto,会顺手把 greeting_id 抹掉。"""
    meta = load_json(_meta_path(e), {}) or {}
    meta["summarized_upto"] = int(n)
    save_json(_meta_path(e), meta)


_summary_inflight: set = set()                  # (entity_dir, cut) 已在跑,防同一段被两个 kick 重复总结
_summary_lock = threading.Lock()


def _summarize_chunk(world: World, e: LocalEntity, chunk: list[dict]) -> None:
    pl = player()
    label = {"user": pl["name"], "char": e.card().get("name", e.id)}
    convo = "\n".join(f"{label.get(t.get('role'), '?')}:{t.get('text', '')}" for t in chunk if t.get("text"))
    if not convo.strip():
        return
    note = llm.generate(_SUMMARY_SYS, convo, max_tokens=300, temperature=0.3).strip()
    if note:
        memory.append_experience(e.dir, note, level="持久", where="对话", trace="auto-summary")


def _summarize_safe(world: World, e: LocalEntity, chunk: list[dict], cut: int) -> None:
    key = (str(e.dir), cut)
    try:
        _summarize_chunk(world, e, chunk)
        _set_summary_upto(e, cut)               # 成功才推进标记;失败下轮再试,不会永久丢这段记忆
    except Exception:  # noqa: BLE001 — 后台总结绝不影响对话主流程
        pass
    finally:
        with _summary_lock:
            _summary_inflight.discard(key)


def _kick_summary(world: World, e: LocalEntity) -> None:
    """对话推进后:把滚出 HISTORY_WINDOW 又没总结过的整段,丢后台线程压缩进记忆(不阻塞回复)。
    用 in-flight 集合防同段重复总结;标记推进改到 worker 成功后,LLM 挂了不会把这段永久踢出记忆。"""
    if not llm.available():
        return
    h = history(e)
    cut = len(h) - HISTORY_WINDOW            # 已滚出模型上下文窗口的边界
    upto = _summary_upto(e)
    if cut - upto < max(2, config.SUMMARY_EVERY):
        return
    chunk = h[upto:cut]
    key = (str(e.dir), cut)
    with _summary_lock:
        if key in _summary_inflight:
            return
        _summary_inflight.add(key)
    threading.Thread(target=_summarize_safe, args=(world, e, chunk, cut), daemon=True).start()
