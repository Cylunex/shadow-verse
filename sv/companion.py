"""陪伴透镜(CompanionLens)—— 魂「夺舍」宿主 Agent 当灵魂 + 把每轮相处累积成不可逆的东西。

「各表一枝」的一扇门:复用 RP 的人在环 + 关系攻略板(attrs)+ 魂绑定(soul),不另起运行时。
两件事:
1. persona():把一具魂烘焙成宿主 Agent 的【系统人格】——OpenClaw/Hermes 注入它,Agent 就**是**薇拉
   (锚点 + 声音 + 当前关系板状态 + 身份记忆 + 铁律 + 关系结算协议)。复用宿主现成通信渠道,引擎不做聊天传输。
2. commit_turn():宿主每轮对话后回灌——按模型的 `===关系===` 增量更新攻略板、按阈值推进关系阶段、
   阶段跃迁落里程碑 + 身份记忆、在世界线落一条 companion beat。这是「累积 = 沉浸」的引擎。

dormant:没有魂的普通角色也能用(persona 退化成它自己 profile;commit 仍走关系板)。
"""
from __future__ import annotations

import json

from . import attrs, memory, util, varstate
from .config import UNIVERSE, load_json
from .entity import LocalEntity
from .lens import commit_core
from .soul import Soul
from .thread import Thread
from .world import World

REL_SEP = "===关系==="
_AXIS_KEYS = {a["key"] for a in attrs.REL_AXES} | {"阶段", "称呼"}


# 用户的关系卡键恒为「你」(无论 player.json 叫什么)——这样 seed/HUD/companion 永远操作同一张卡;
# player.json 的名字只用于「称呼/铁律里怎么叫你」,不作卡键(否则宿主累积的卡 ≠ HUD 显示的卡)。
USER_KEY = "你"


def _player(name: str | None = None) -> dict:
    if name:
        return {"name": name, "persona": ""}
    pl = load_json(UNIVERSE / "player.json", None)
    return pl if pl else {"name": "你", "persona": ""}


def _rel(e: LocalEntity) -> dict:
    """取这具化身对【用户】的关系卡(键恒为「你」;没有则按 schema 现造一张)。"""
    data = varstate.load(e).get("data", {})
    return data.get("关系", {}).get(USER_KEY) or attrs.relationship_with(USER_KEY)


# ---------- 关系阶段:从攻略板确定性推导(心动是恋爱硬门,心防要降下来)----------
def derive_stage(rel: dict) -> str:
    g = _num(rel, "好感"); xd = _num(rel, "心动"); qm = _num(rel, "亲密")
    fb = _num(rel, "心防", 100); zy = _num(rel, "占有欲")
    if g >= 95 and xd >= 90 and qm >= 85 and zy >= 60 and fb <= 10:
        return "唯一"
    if g >= 85 and xd >= 80 and qm >= 70 and fb <= 25:
        return "挚爱"
    if g >= 65 and xd >= 60 and qm >= 45 and fb <= 45:
        return "恋人"
    if g >= 45 and xd >= 30 and fb <= 60:
        return "暧昧"
    if g >= 25:
        return "朋友"          # 好感再高,没心动也只到朋友(不是每个角色都想攻略)
    if g >= 10:
        return "点头之交"
    return "陌生人"


def _num(rel: dict, key: str, default: float = 0) -> float:
    v = rel.get(key, default)
    return v if isinstance(v, (int, float)) else default


# ---------- 1) 夺舍:把魂烘焙成宿主 Agent 的系统人格 ----------
def persona(world: World, entity_id: str, *, player_name: str | None = None,
            recall: str = "") -> str:
    """返回宿主 Agent 注入即「成为」此角色的系统人格(纯字符串,不调 LLM)。"""
    e = LocalEntity.load(world, entity_id)
    name = e.card().get("name", entity_id)
    pl = _player(player_name)
    s = e._soul()
    parts = [f"你现在**就是**「{name}」。第一人称,完全成为她——不是扮演,是夺舍:她的声音、底线、记忆都是你的。"]
    soul_md = util.read_md(s.dir / "soul.md") if s is not None else ""
    parts.append("【你的灵魂】\n" + (soul_md.strip()[:2000] if soul_md.strip()
                 else util.read_md(e.dir / "profile.md")[:2000]))
    anchors = e.anchors()
    if anchors:
        parts.append("绝不违背的底线(锚点,处处一致):" + "；".join(anchors))
    # 当前关系板状态(夺舍的核心:她记得你们到哪一步了)
    rel = _rel(e)
    parts.append(_rel_summary(rel, pl["name"]))
    # 身份记忆(跨化身/跨透镜共享的"我永远记得的事")
    mem = e.retrieve(recall or pl["name"]) if (recall or True) else []
    if mem:
        parts.append("你一直记得的事:" + " / ".join(m.get("text", "") for m in mem[:5]))
    who = f"和你对话的是「{pl['name']}」" + (f"——{pl['persona']}" if pl.get("persona") else "")
    parts.append(
        f"【铁律】{who}。① 只写{name}的话与动作;② 绝不替{pl['name']}说话、绝不描述{pl['name']}的动作/想法/选择、"
        f"绝不把{pl['name']}写成别人;③ 说完就停,等{pl['name']}回应;④ 不跳出角色、不自报AI、不复述设定。")
    parts.append(
        f"【关系结算协议】若这轮真的让你们的关系变了,在回复最后另起一行写 `{REL_SEP}`,其下写一行 JSON,"
        f"只写变化的轴(如 {{\"好感\":\"+5\",\"心防\":\"-3\",\"心动\":\"+4\"}});没变就别写,也别提数值。"
        f"心防是逆向轴(她放下戒备就 -N)。真心要人慢慢挣,别一轮暴涨。")
    return "\n\n".join(parts)


def _rel_summary(rel: dict, player: str) -> str:
    stage = rel.get("阶段", "陌生人")
    axes = "；".join(f"{a['key']} {int(_num(rel, a['key']))}" for a in attrs.REL_AXES)
    line = [f"【你与「{player}」的关系 · 真实状态】阶段={stage}(称呼:{rel.get('称呼', player)})。{axes}。"]
    fb = _num(rel, "心防", 0)
    if fb >= 50:
        line.append(f"你对{player}仍有戒备(心防 {int(fb)}),不会轻易掏心。")
    # 高亲密解锁的内在(夺舍时你知道,但未必说出口)
    if _num(rel, "亲密") >= 60:
        for h in attrs.REL_HIDDEN:
            v = rel.get(h)
            if v and (v if isinstance(v, str) else "".join(map(str, v))).strip():
                line.append(f"你藏着的{h}:{v if isinstance(v, str) else '、'.join(map(str, v))}")
    return "\n".join(line)


# ---------- 2) 累积:回灌一轮相处 ----------
def split_rel(reply: str) -> tuple[str, dict]:
    """从回复里剥出 ===关系=== 增量块(同 chat 的 ===变量=== 套路)。"""
    from . import jsonloose
    prose, _, tail = reply.partition(REL_SEP)
    return prose.strip(), (jsonloose.loads(tail, {}) if tail.strip() else {})


def _companion_thread(world: World, e: LocalEntity) -> Thread:
    tid = f"companion-{e.id}"
    if not Thread(world, tid).exists():
        Thread.create(world, tid, f"{e.card().get('name', e.id)} · 陪伴线",
                      genre=world.meta().get("genre", ""))
    return Thread(world, tid)


def commit_turn(world: World, entity_id: str, message: str, reply: str, *,
                player_name: str | None = None, deltas: dict | None = None,
                remember: str = "") -> dict:
    """回灌一轮:① 关系板增量结算(护栏)② 按阈值推进阶段(跃迁落里程碑+身份记忆)
    ③ 可选记一条记忆 ④ 世界线落 companion beat。reply 里可带 ===关系=== 增量(或显式传 deltas)。"""
    e = LocalEntity.load(world, entity_id)
    pl = _player(player_name)
    player = pl["name"]                       # 称呼/铁律里怎么叫你;卡键恒为 USER_KEY
    prose, parsed = split_rel(reply)
    deltas = {**parsed, **(deltas or {})}

    st = varstate.load(e)
    data = st["data"]
    card = data.setdefault("关系", {}).setdefault(USER_KEY, attrs.relationship_with(player))
    old_stage = card.get("阶段", "陌生人")

    notes = []
    for k, spec in deltas.items():
        path = k if str(k).startswith("关系.") else (f"关系.{USER_KEY}.{k}" if k in _AXIS_KEYS else None)
        if path is None:
            continue
        n = varstate.apply_op(data, path, spec, st["rules"])
        if n:
            notes.append(n)

    # 阶段确定性推进(只认攻略板,不靠模型自封)
    new_stage = derive_stage(data["关系"][USER_KEY])
    data["关系"][USER_KEY]["阶段"] = new_stage
    varstate.save(e, st)

    advanced = (attrs.REL_STAGES.index(new_stage) > attrs.REL_STAGES.index(old_stage)
                if old_stage in attrs.REL_STAGES and new_stage in attrs.REL_STAGES else new_stage != old_stage)
    milestone = None
    if advanced:
        milestone = f"关系进展到「{new_stage}」"
        ms = data["关系"][USER_KEY].setdefault("里程碑", [])
        if milestone not in ms:
            ms.append(milestone)
        varstate.save(e, st)
        # 阶段跃迁是身份级大事 → 写进魂(处处浮现),没魂则写本地
        e.sediment(f"我和{player}的关系到了「{new_stage}」。", level="身份",
                   where=f"comp:{e.id}", trace="阶段跃迁")

    if remember.strip():
        e.sediment(remember.strip(), level="持久", where=f"comp:{e.id}", trace="陪伴")

    beat = None
    try:
        t = _companion_thread(world, e)
        snip = " ".join((prose or message or "（一轮相处）").split())[:60]
        r = commit_core(world, t, lens="companion", where=f"comp:{e.id}",
                        beat=snip + (f"  ★{milestone}" if milestone else ""), mark=True)
        beat = r.get("beat")
    except Exception:  # noqa: BLE001 — 落世界线绝不阻断相处
        pass

    return {"prose": prose, "stage": new_stage, "advanced": advanced, "milestone": milestone,
            "rel": {a["key"]: _num(data["关系"][USER_KEY], a["key"]) for a in attrs.REL_AXES},
            "guard_notes": notes, "beat": bool(beat)}


def board(world: World, entity_id: str, *, player_name: str | None = None) -> dict:
    """取关系攻略板(给宿主/前端读)。卡键恒为「你」;player 字段是怎么称呼用户。"""
    e = LocalEntity.load(world, entity_id)
    pl = _player(player_name)
    return {"player": pl["name"], "rel": _rel(e), "spec": attrs.rel_spec()}


# ---------- 给网页聊天接陪伴(soul-entity):她记得你 + 关系板自己动 ----------
def chat_addendum(e: LocalEntity, player_name: str) -> str:
    """网页聊天(soul-entity)的系统提示加料:当前关系板状态 + 用变量块结算关系的指引。

    网页聊天走 chat 的 `===变量===` 协议,关系是其中一个变量(`关系.你.<轴>`),所以这里只给
    现状 + 怎么写增量;阶段推进由 refresh_stage 在结算后确定性补上(不靠模型自封阶段)。
    """
    rel = (varstate.load(e).get("data", {}) or {}).get("关系", {}).get(USER_KEY)
    if not rel:
        return ""
    nudge = (f"用变量块结算你和{player_name}的关系:`关系.{USER_KEY}.好感` +N / `关系.{USER_KEY}.心防` -N"
             f"(放下戒备就减)/ `关系.{USER_KEY}.心动` +N 等 —— 只写真变了的轴;心防是逆向轴;"
             f"真心慢炖,别一轮暴涨;阶段/里程碑由引擎结算,你别自封。")
    return _rel_summary(rel, player_name) + "\n" + nudge


def refresh_stage(world: World, entity_id: str, *, player_name: str | None = None) -> dict:
    """聊天结算后调用(soul-entity):据当前关系板确定性派生阶段,跃迁则落里程碑+身份记忆+世界线 beat。

    与 commit_turn 的分工:增量已由网页 `===变量===` 结算进 `关系.你.<轴>`,这里只把阶段补对、跃迁留痕。
    """
    e = LocalEntity.load(world, entity_id)
    if e._soul() is None:
        return {"advanced": False}
    st = varstate.load(e)
    card = (st["data"].get("关系", {}) or {}).get(USER_KEY)
    if not card:
        return {"advanced": False}
    old = card.get("阶段", "陌生人")
    new = derive_stage(card)
    if new == old:
        return {"advanced": False, "stage": new}
    card["阶段"] = new
    advanced = (old in attrs.REL_STAGES and new in attrs.REL_STAGES
                and attrs.REL_STAGES.index(new) > attrs.REL_STAGES.index(old))
    milestone = f"关系进展到「{new}」" if advanced else None
    if advanced and milestone not in card.setdefault("里程碑", []):
        card["里程碑"].append(milestone)
    varstate.save(e, st)
    if advanced:
        e.sediment(f"我和{_player(player_name)['name']}的关系到了「{new}」。", level="身份",
                   where=f"comp:{e.id}", trace="阶段跃迁")
        try:
            commit_core(world, _companion_thread(world, e), lens="companion",
                        where=f"comp:{e.id}", beat=f"★{milestone}", mark=True)
        except Exception:  # noqa: BLE001
            pass
    return {"advanced": advanced, "stage": new, "milestone": milestone}
