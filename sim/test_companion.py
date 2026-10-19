"""陪伴透镜测试 —— 夺舍人格 + 关系累积(阶段确定性推进 + 跃迁里程碑 + 世界线 beat + 护栏)。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_comp_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import ascension, companion, varstate  # noqa: E402
from sv.config import read_jsonl  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.memory import _identity_path  # noqa: E402
from sv.soul import Soul  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

w = World.create("tavern", "混沌酒馆", genre="无限流")
ascension.create_soul(w, "mu", "穆", anchors=["守账本", "真心要人挣"])
e = LocalEntity.load(w, "mu")

# ---------- 夺舍人格 ----------
p = companion.persona(w, "mu")
ok("你现在**就是**「穆」" in p, "persona:第一人称夺舍开头")
ok("完全成为TA" in p and "TA的声音" in p, "persona:默认中性人称 TA(不硬编码她)")
ok("守账本" in p and "真心要人挣" in p, "persona:注入魂的锚点(底线)")
ok("【铁律】" in p and "绝不替你说话" in p.replace("「你」", "你"), "persona:带对话铁律(治身份漂移)")
ok(companion.REL_SEP in p and "心防是逆向轴" in p, "persona:带关系结算协议")
# 可配置人称
ok(companion.resolve_voice(raw="")["pronoun"] == "TA", "resolve_voice:空→TA")
ok(companion.resolve_voice(raw="女")["pronoun"] == "她", "resolve_voice:女→她")
ok(companion.resolve_voice(raw="he")["pronoun"] == "他", "resolve_voice:he→他")
companion.set_voice(e, "she")
p_she = companion.persona(w, "mu")
ok("完全成为她" in p_she and "她的声音" in p_she, "persona:card.voice=she → 她")
companion.set_voice(e, "he")
p_he = companion.persona(w, "mu")
ok("完全成为他" in p_he and "他放下戒备" in p_he, "persona:card.voice=he → 他")
companion.set_voice(e, "they")  # 还原中性,后续测试不受影响

# ---------- 阶段确定性推导(心动是恋爱硬门)----------
ok(companion.derive_stage({}) == "陌生人", "阶段:空板=陌生人")
ok(companion.derive_stage({"好感": 90, "心动": 0}) == "朋友", "阶段:高好感无心动只到朋友(不是每个角色都想攻略)")
ok(companion.derive_stage({"好感": 70, "心动": 65, "亲密": 50, "心防": 40}) == "恋人", "阶段:满足恋爱门=恋人")
ok(companion.derive_stage({"好感": 60, "心动": 40, "心防": 80}) == "朋友", "阶段:心防太高压制到朋友(要降戒备)")

# ---------- 累积一轮(reply 带 ===关系=== 增量)----------
reply = ("（穆没看你,指尖敲了敲账本。）……坐吧。\n"
         f"{companion.REL_SEP}\n" + '{"好感":"+30","心动":"+5","心防":"-4"}')
r = companion.commit_turn(w, "mu", "我又来了", reply)
ok(r["prose"].startswith("（穆没看你") and "===" not in r["prose"], "commit:剥出正文(变量块不外泄)")
ok(r["rel"]["好感"] == 30 and r["rel"]["心防"] == 66, "commit:关系板增量结算(含逆向轴 心防 -4)")
ok(r["stage"] == "朋友" and r["advanced"] and r["milestone"] == "关系进展到「朋友」", "commit:阶段确定性跃迁 + 落里程碑")
ms = varstate.load(e)["data"]["关系"]["你"]["里程碑"]
ok("关系进展到「朋友」" in ms, "commit:里程碑写进关系板")
ok(len(read_jsonl(_identity_path(Soul("mu").dir))) >= 1, "commit:阶段跃迁是身份级大事 → 写进魂 identity.jsonl")
wl = Thread(w, "companion-mu")
ok(wl.exists() and wl.beats() and wl.beats()[-1]["lens"] == "companion", "commit:相处落 companion beat 到世界线")

# ---------- 护栏:乱写也写不坏 ----------
r2 = companion.commit_turn(w, "mu", "x", '一句话\n' + companion.REL_SEP + '\n{"好感":"+999"}')
ok(r2["rel"]["好感"] == 100 and any("封顶" in n for n in r2["guard_notes"]), "护栏:超界增量被 clamp(好感封顶 100)")

# ---------- 关系板读取 ----------
b = companion.board(w, "mu")
ok(b["player"] == "你" and b["rel"]["阶段"] == "朋友" and len(b["spec"]["axes"]) == 9, "board:返回关系卡 + 渲染规格(9 轴)")
ok(b.get("voice", {}).get("key") == "they" and b["voice"]["pronoun"] == "TA", "board:带回 voice 规格(默认 they/TA)")
ok(any(a.get("reverse") for a in b["spec"]["axes"] if a["key"] == "心防"), "board.spec:心防轴 reverse=True")

# ---------- 用户卡键恒为「你」,player.json 名只作称呼(防 seed/HUD/companion 三方分裂)----------
from sv.config import UNIVERSE, save_json  # noqa: E402
save_json(UNIVERSE / "player.json", {"name": "影", "persona": "夜行的过客"})
p2 = companion.persona(w, "mu")
ok("「影」" in p2, "persona:用 player.json 名「影」称呼用户")
companion.commit_turn(w, "mu", "hi", "好。\n" + companion.REL_SEP + '\n{"好感":"+5"}')
rels2 = varstate.load(e)["data"]["关系"]
ok("你" in rels2 and "影" not in rels2, "累积仍写进恒定的「你」卡,不因 player.json 名另起一张(治 seed/HUD/companion 分裂)")
ok(companion.board(w, "mu")["player"] == "影", "board.player 报告称呼名(影),卡键仍是「你」")

# ---------- 网页聊天接陪伴:chat_addendum(系统提示加料)+ refresh_stage(结算后确定性推进阶段)----------
add = companion.chat_addendum(e, "影")
ok("阶段=" in add and "关系.你.好感" in add, "chat_addendum:注入关系现状 + 用变量块结算关系的指引")
card = varstate.load(e)["data"]["关系"]["你"]                      # 模拟网页 ===变量=== 把关系推过恋爱门
card.update({"好感": 80, "心动": 65, "亲密": 50, "心防": 40})
st_e = varstate.load(e); st_e["data"]["关系"]["你"] = card; varstate.save(e, st_e)
rs = companion.refresh_stage(w, "mu")
ok(rs["advanced"] and rs["stage"] == "恋人", "refresh_stage:据攻略板确定性推进(好感80+心动65+亲密50+心防40→恋人)")
ok("恋人" in str(varstate.load(e)["data"]["关系"]["你"]["里程碑"]), "refresh_stage:跃迁落里程碑")
plain = LocalEntity.create(w, "luren", "路人", role="secondary")   # 非 soul 角色
ok(companion.refresh_stage(w, "luren") == {"advanced": False}, "非 soul 角色:refresh_stage 零行为(字节等价)")
ok(companion.chat_addendum(plain, "影") == "", "非 soul 且无关系卡:chat_addendum 返回空")

# ---------- 显著关系波动自动温层记忆(无显式 remember、无阶段跃迁)----------
# 此刻已是恋人(好感80/心动65/亲密50/心防40);再推心动+亲密,不进挚爱(需亲密70+心防25)
exp_path = e.dir / "experiences.jsonl"
exps_before = len(read_jsonl(exp_path)) if exp_path.exists() else 0
r3 = companion.commit_turn(w, "mu", "今天聊了很久",
    '（穆合上账本。）……下次别这么晚。\n' + companion.REL_SEP + '\n{"心动":"+20","亲密":"+15"}')
ok(not r3["advanced"] and r3["stage"] == "恋人", "显著波动:未跨阶段(仍恋人)")
ok(r3.get("swing", 0) >= 12, "显著波动:真实落库 swing≥12")
exps_after = len(read_jsonl(exp_path)) if exp_path.exists() else 0
ok(exps_after == exps_before + 1, "显著波动:自动落温层相处印象(+1 experiences)")
last = read_jsonl(exp_path)[-1]
ok(last.get("text", "").startswith("相处印象:") and "下次别这么晚" in last["text"],
   "显著波动:印象文本取自本轮正文")


# ---------- 温层印象注入 + 网页 after_chat_settle ----------
wl = companion.warm_lines(e, limit=3)
ok(any("相处印象:" in x or x.startswith("★") for x in wl), "warm_lines:含相处印象或里程碑")
add_w = companion.chat_addendum(e, "影")
ok("你们最近相处留下的印象:" in add_w, "chat_addendum:注入温层印象")

# 模拟网页聊天:先记下 before_rel,改轴,再 after_chat_settle
before = dict(varstate.load(e)["data"]["关系"]["你"])
st = varstate.load(e)
st["data"]["关系"]["你"]["心动"] = before.get("心动", 0) + 15
st["data"]["关系"]["你"]["亲密"] = before.get("亲密", 0) + 10
varstate.save(e, st)   # 模拟 ===变量=== 已结算
acs = companion.after_chat_settle(w, "mu", before_rel=before,
                                  prose="（穆把茶推过来。）喝吧。", message="谢谢")
ok(acs.get("swing", 0) >= 12 and acs.get("warmed"), "after_chat_settle:显著波动 → warmed")
ok(any("喝茶" in x or "茶" in x or "喝吧" in x for x in companion.warm_lines(e)),
   "after_chat_settle:温层印象取自本轮正文")


print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
