"""群聊 —— 多角色同场轮流发言(玩透镜的多角色版,单机网页用)。

借鉴 SillyTavern group-chats.js 的发言人选择(自然顺序:@提名→talkativeness 掷骰→禁连说→话痨池兜底)。
每个角色独立人设/记忆,共享同一群级 vars + 世界书 + 对话流。一份 group.json + chat.jsonl(char 行带 speaker)。
随机数仅用于发言人选择(`SV_SIM_NOW` 不固定它;测试可注入 rng)。
"""
from __future__ import annotations

import random

from . import chat, clock, jsonloose, llm, memory, util, varstate, worldbook
from .config import GROUPS_DIR, append_jsonl, load_json, read_jsonl, save_json
from .entity import LocalEntity
from .world import World

HISTORY_WINDOW = 16
TALKATIVENESS_DEFAULT = 0.5


class Group:
    def __init__(self, gid: str):
        self.gid = gid
        self.dir = GROUPS_DIR / gid

    @property
    def meta_path(self):
        return self.dir / "group.json"

    @property
    def chat_path(self):
        return self.dir / "chat.jsonl"

    def exists(self) -> bool:
        return self.meta_path.exists()

    def meta(self) -> dict:
        return load_json(self.meta_path, {}) or {}

    def save_meta(self, m: dict) -> None:
        save_json(self.meta_path, m)

    @classmethod
    def create(cls, gid: str, name: str, world_id: str, members: list[str], *,
               strategy: str = "natural", talkativeness: dict | None = None,
               allow_self: bool = False, greetings: list | None = None) -> "Group":
        if not util.is_id(gid):
            raise ValueError(f"群 id 须 kebab-case:{gid!r}")
        g = cls(gid)
        if g.exists():
            raise FileExistsError(f"群已存在:{gid}")
        g.save_meta({"id": gid, "name": name, "world": world_id, "members": list(members),
                     "strategy": strategy, "talkativeness": talkativeness or {},
                     "allow_self": allow_self, "greetings": greetings or [],
                     "created": clock.now_iso()})
        return g

    @classmethod
    def load(cls, gid: str) -> "Group":
        g = cls(gid)
        if not g.exists():
            raise FileNotFoundError(f"群不存在:{gid}")
        return g

    @classmethod
    def list_all(cls) -> list[str]:
        return sorted(p.parent.name for p in GROUPS_DIR.glob("*/group.json")) if GROUPS_DIR.exists() else []

    def world(self) -> World:
        return World.load(self.meta()["world"])

    def member_entities(self) -> list[LocalEntity]:
        w = self.world()
        out = []
        for eid in self.meta().get("members", []):
            e = LocalEntity(w, eid)
            if e.exists():
                out.append(e)
        return out

    def history(self, n: int | None = None) -> list[dict]:
        h = read_jsonl(self.chat_path)
        return h if n is None else h[-n:]

    def clear(self) -> None:
        if self.chat_path.exists():
            self.chat_path.unlink()


# ---------- 发言人选择(自然顺序;纯算法,翻自 group-chats.js:1422)----------
def activate_natural_order(members: list[dict], user_input: str, last_speaker: str | None,
                           allow_self: bool = False, rng: random.Random | None = None) -> list[str]:
    """返回本回合发言成员 id(有序去重)。members:[{id,name,talkativeness}]。"""
    rng = rng or random
    banned = None if allow_self else last_speaker
    activated: list[str] = []

    # ① @提名:用户文本点到谁,谁先说(中文名子串包含;排除 banned)
    text = user_input or ""
    for m in members:
        if m["name"] == banned:
            continue
        if m["name"] and m["name"] in text:
            activated.append(m["id"])

    # ② talkativeness 掷骰(打乱后逐个 roll)
    chatty = []
    for m in rng.sample(members, len(members)):
        if m["name"] == banned:
            continue
        t = m.get("talkativeness", TALKATIVENESS_DEFAULT)
        if t >= rng.random():
            activated.append(m["id"])
        if t > 0:
            chatty.append(m["id"])

    # ③ 兜底:没人激活就从话痨池随机抓一个
    pool = chatty or [m["id"] for m in members]
    tries = 0
    while not activated and pool and tries < len(pool):
        activated.append(rng.choice(pool))
        tries += 1

    seen: set[str] = set()
    return [x for x in activated if not (x in seen or seen.add(x))]


# ---------- 意图路由 + 结构化消息头(借 MimirLink standard-event/current-message-focus)----------
_QUESTION = ("?", "？", "吗", "呢", "怎么", "为什么", "为何", "什么", "如何", "是不是", "对不对")


def analyze_focus(message: str, members: list[dict], last_speaker: str | None) -> dict:
    """把一条玩家消息压成「意图 + 回复目标 + 策略提示」,让单 LLM 在多人场里有谱地应对。

    纯启发式零依赖(无 LLM)。intent∈call_out/question/low_info/chat;mentioned=被点名的成员名。
    """
    text = (message or "").strip()
    mentioned = [m["name"] for m in members if m["name"] and m["name"] in text]
    if mentioned:
        intent = "call_out"
    elif any(q in text for q in _QUESTION):
        intent = "question"
    elif len(text) <= 4:
        intent = "low_info"
    else:
        intent = "chat"
    hints = {
        "call_out": "被点名者优先正面回应,其他人可搭话但别抢。",
        "question": "正面回答,信息要落地,别用反问把问题甩回去。",
        "low_info": "玩家话少:用动作/环境推进,别复读关键词、别强行追问。",
        "chat": "群聊保持 1-3 句短回合,留话头给别人,别独占镜头。",
    }
    return {"intent": intent, "mentioned": mentioned, "strategy": hints[intent],
            "last_speaker": last_speaker}


def message_header(speaker: str, *, to: str = "", intent: str = "") -> str:
    """结构化消息头:一行文本携带说话人/对象/意图元数据(让线性历史里可分辨谁对谁说)。"""
    parts = [f"说话人:{speaker}"]
    if to:
        parts.append(f"对:{to}")
    if intent:
        parts.append(f"意图:{intent}")
    return "［" + "｜".join(parts) + "］"


# ---------- 提示词(每个角色独立 system,看得到群里其他人)----------
def _member_system(world: World, e: LocalEntity, others: list[str], pl: dict, varbag: dict,
                   focus: dict | None = None) -> str:
    name = e.card().get("name", e.id)
    parts = [
        f"你只扮演「{name}」这一个角色,第一人称,保持人设与说话风格。",
        f"人物档案:\n{util.read_md(e.dir / 'profile.md')[:2000]}",
    ]
    if e.anchors():
        parts.append("绝不违背的底线:" + "；".join(e.anchors()))
    parts.append(f"世界背景:{world.meta().get('name', '')}({world.meta().get('genre', '')})。")
    cast = "、".join(others)
    who = f"和你们对话的是「{pl['name']}」" + (f"——{pl['persona']}" if pl.get("persona") else "")
    parts.append(
        f"【群聊铁律】这是多人同场。在场还有:{cast}。{who}。\n"
        f"① 只写{name}的话与动作;② 绝不替{pl['name']}、也绝不替在场其他角色({cast})说话或描述其想法;"
        f"③ 说完就停,把话头留给别人;④ 不跳出角色、不复述设定、不加旁白。")
    if focus:
        tip = f"【本轮焦点】玩家意图:{focus['intent']}"
        if focus.get("mentioned"):
            tip += f";点名了:{'、'.join(focus['mentioned'])}"
        tip += f"。策略:{focus['strategy']}"
        parts.append(tip)
    if varbag:
        parts.append(f"当前群内变量:{varbag}。若本轮该变,在正文最后另起一行写 `{chat.VAR_SEP}` 再写一行 JSON(只写要变的);没变就别写。")
    return "\n\n".join(parts)


def _group_transcript(hist: list[dict], pl: dict, members_name: dict, speaker: str) -> str:
    lines = []
    for t in hist:
        if t["role"] == "user":
            lines.append(f"{pl['name']}:{t['text']}")
        else:
            lines.append(f"{t.get('speaker', '?')}:{t['text']}")
    convo = "\n".join(lines)
    return (convo + "\n" if convo else "") + f"（轮到 {speaker} 发言）\n{speaker}:"


def _gen_member(group: Group, world: World, e: LocalEntity, others: list[str], pl: dict,
                focus: dict | None = None) -> tuple[str, dict]:
    varbag = varstate.load(group)["data"]
    sys = _member_system(world, e, others, pl, varbag, focus)
    hist = group.history(HISTORY_WINDOW)
    q = hist[-1]["text"] if hist else ""
    mem = memory.retrieve(e.dir, q)
    if mem:
        sys += "\n\n该想起的事:" + " / ".join(m["text"] for m in mem)
    wb = worldbook.scan(world, q + "\n" + " ".join(t["text"] for t in hist[-4:]), budget_chars=1000)
    if wb["injection"]:
        sys += "\n\n相关世界设定:\n" + wb["injection"]
    name = e.card().get("name", e.id)
    raw = llm.generate(sys, _group_transcript(hist, pl, {}, name)).strip()
    prose, _, tail = raw.partition(chat.VAR_SEP)
    updates = jsonloose.loads(tail, {}) if tail.strip() else {}
    return prose.strip(), updates


def turn(group: Group, message: str) -> dict:
    """群聊一回合:选发言人 → 逐个生成并落盘(后说的看得到先说的)。"""
    if not llm.available():
        return {"available": False, "reply": "（未配 LLM,去 ⚙ 设置 配 provider+key）"}
    world = group.world()
    pl = chat.player()
    ents = group.member_entities()
    if not ents:
        return {"available": True, "note": "群里没有有效成员"}
    talk = group.meta().get("talkativeness", {})
    members = [{"id": e.id, "name": e.card().get("name", e.id),
                "talkativeness": talk.get(e.id, e.card().get("talkativeness", TALKATIVENESS_DEFAULT))}
               for e in ents]
    name_by_id = {m["id"]: m["name"] for m in members}
    hist = group.history()
    last_speaker = next((h.get("speaker") for h in reversed(hist) if h["role"] == "char"), None)
    focus = analyze_focus(message, members, last_speaker)   # 意图路由(指导发言人+策略)
    speakers = activate_natural_order(members, message, last_speaker, group.meta().get("allow_self", False))

    append_jsonl(group.chat_path, {"role": "user", "text": message, "ts": clock.now_iso()})
    ent_by_id = {e.id: e for e in ents}
    out = []
    notes = []
    for sid in speakers:
        e = ent_by_id[sid]
        others = [name_by_id[m["id"]] for m in members if m["id"] != sid]
        reply, updates = _gen_member(group, world, e, others, pl, focus)
        append_jsonl(group.chat_path, {"role": "char", "speaker": name_by_id[sid], "entity": sid,
                                       "text": reply, "ts": clock.now_iso()})
        if updates:   # 结算到群级 vars
            st = varstate.load(group)
            notes += varstate.apply_updates(st["data"], updates, st["rules"])
            varstate.save(group, st)
        out.append({"speaker": name_by_id[sid], "entity": sid, "reply": reply})
    return {"available": True, "speakers": [o["speaker"] for o in out], "replies": out,
            "focus": focus, "vars": varstate.load(group)["data"], "var_notes": notes}


def greet(group: Group) -> list[dict]:
    """群组开场:每个有 greeting 的成员各发一条(随机选 alternate)。"""
    out = []
    for e in group.member_entities():
        g = (e.card().get("greeting") or "").strip()
        if g:
            out.append({"speaker": e.card().get("name", e.id), "entity": e.id, "reply": g})
    return out
