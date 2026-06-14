"""实时对话 —— 直接和一个实体逐句聊(玩透镜的轻量单角色版,单机网页用)。

用实体的灵魂(profile+anchors)+ 此刻 state + 记忆检索 + 近期对话史,组装人设,
交可插拔 LLM 以第一人称扮演。对话存实体 chat.jsonl。需配 SV_PROVIDER(stub 时给引导)。
作为宿主 skill 时不用这个——宿主 Agent 用 play_prep 自己扮演。
"""
from __future__ import annotations

from . import clock, llm, memory, util
from .config import append_jsonl, read_jsonl
from .entity import LocalEntity
from .world import World

HISTORY_WINDOW = 12   # 喂给模型的近期对话轮数


def _path(e: LocalEntity):
    return e.dir / "chat.jsonl"


def history(e: LocalEntity, n: int | None = None) -> list[dict]:
    h = read_jsonl(_path(e))
    return h if n is None else h[-n:]


def greeting(e: LocalEntity) -> str:
    return (e.card().get("greeting") or "").strip() or f"（{e.card().get('name', e.id)} 抬眼看了你一下。）"


def clear(e: LocalEntity) -> None:
    p = _path(e)
    if p.exists():
        p.unlink()


def _persona(world: World, e: LocalEntity) -> str:
    name = e.card().get("name", e.id)
    prof = util.read_md(e.dir / "profile.md")
    anchors = e.anchors()
    st = memory.read_state(e.dir)
    parts = [
        f"你就是「{name}」。以第一人称严格扮演,保持人设与说话风格,绝不跳出角色、绝不自报是 AI 或系统、绝不复述设定。",
        f"人物档案:\n{prof[:2500]}",
    ]
    if anchors:
        parts.append("绝不违背的底线:" + "；".join(anchors))
    now = " ".join(x for x in (st.get("location", ""), st.get("mood", "")) if x)
    if now:
        parts.append(f"此刻:{now}")
    parts.append(f"世界背景:{world.meta().get('name', '')}({world.meta().get('genre', '')})。")
    parts.append("只说角色的话与必要动作,简洁有画面,不加旁白解释。")
    return "\n\n".join(parts)


def turn(world: World, e: LocalEntity, message: str) -> dict:
    """聊一轮:组装人设+记忆+对话史 → LLM 出角色回复,落 chat.jsonl。"""
    if not llm.available():
        return {"available": False,
                "reply": "（还没配 LLM,没法真正对话。去左边 ⚙ 设置 填一个 provider + key,回来就能聊了。）"}
    sys = _persona(world, e)
    mem = memory.retrieve(e.dir, message)
    if mem:
        sys += "\n\n该想起的事:" + " / ".join(m["text"] for m in mem)
    h = history(e, HISTORY_WINDOW)
    convo = "\n".join((("你" if t["role"] == "char" else "对方") + ":" + t["text"]) for t in h)
    user = (convo + "\n" if convo else "") + "对方:" + message + "\n你:"
    reply = llm.generate(sys, user).strip()
    append_jsonl(_path(e), {"role": "user", "text": message, "ts": clock.now_iso()})
    append_jsonl(_path(e), {"role": "char", "text": reply, "ts": clock.now_iso()})
    return {"available": True, "reply": reply}
