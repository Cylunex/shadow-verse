"""群聊测试 —— 发言人选择算法(@提名/talkativeness/禁连说/兜底)+ 多角色轮流落盘 + 群级变量。"""
from __future__ import annotations

import os
import random
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_grp_")
os.environ["SV_LOCAL_CONF"] = tempfile.mktemp(suffix=".conf")
os.environ.pop("SV_PROVIDER", None)

from sv import clock  # noqa: E402

clock.use_virtual()

import sv.group as G  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.group import Group  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

MEMBERS = [{"id": "lin", "name": "凛", "talkativeness": 0.5},
           {"id": "ye", "name": "夜", "talkativeness": 0.5},
           {"id": "lu", "name": "璐", "talkativeness": 0.5}]
rng = random.Random(42)

# @提名优先
sp = G.activate_natural_order(MEMBERS, "凛你怎么看", None, rng=rng)
ok(sp[0] == "lin", "@提名:点到「凛」凛先说")

# 禁止连续发言(上一个发言者是凛 → 本轮 banned)
sp2 = G.activate_natural_order(MEMBERS, "凛再说一句", "凛", rng=rng)
ok("lin" not in sp2, "禁连说:上轮发言者本轮不发言")

# allow_self 放开连说
sp3 = G.activate_natural_order(MEMBERS, "凛再说一句", "凛", allow_self=True, rng=rng)
ok("lin" in sp3, "allow_self:放开连续发言")

# talkativeness=0 的人不主动开口(除非兜底/被点名)
silent = [{"id": "a", "name": "甲", "talkativeness": 0.0}, {"id": "b", "name": "乙", "talkativeness": 0.0}]
got = G.activate_natural_order(silent, "你们好", None, rng=random.Random(1))
ok(len(got) == 1, "全沉默时兜底也只挑一个发言(不冷场)")

# 去重保序
dup = G.activate_natural_order([{"id": "x", "name": "甲乙", "talkativeness": 1.0}], "甲乙甲乙", None, rng=rng)
ok(dup == ["x"], "@提名+掷骰命中同一人也只发一次")

# 意图路由
f1 = G.analyze_focus("凛你怎么看", MEMBERS, None)
ok(f1["intent"] == "call_out" and "凛" in f1["mentioned"], "意图:点名→call_out")
f2 = G.analyze_focus("这是为什么呢", MEMBERS, None)
ok(f2["intent"] == "question" and "甩回去" in f2["strategy"], "意图:疑问→question+策略")
f3 = G.analyze_focus("嗯", MEMBERS, None)
ok(f3["intent"] == "low_info" and "别复读" in f3["strategy"], "意图:话少→low_info")
ok("说话人:凛" in G.message_header("凛", to="夜", intent="call_out"), "结构化消息头")

# ---- 建群 + 假 LLM 轮流落盘 ----
w = World.create("w", "W", genre="都市")
for eid, nm in [("lin", "凛"), ("ye", "夜"), ("lu", "璐")]:
    LocalEntity.create(w, eid, nm, role="main", body=f"# {nm}\n## 核心事实\n- 普通人")
grp = Group.create("crew", "三人组", "w", ["lin", "ye", "lu"], talkativeness={"lin": 1.0, "ye": 1.0, "lu": 0.0})
ok(Group.load("crew").meta()["members"] == ["lin", "ye", "lu"], "建群落盘")

_av, _gen = G.llm.available, G.llm.generate
G.llm.available = lambda: True
def _fake(system, user, **kw):
    # 谁的回合从 user 末尾「轮到 X 发言」拿;附带给群变量 +1
    who = user.strip().splitlines()[-1].split(":")[0]
    return f"{who}说了句话\n===变量===\n{{\"气氛\":\"+1\"}}"
G.llm.generate = _fake
try:
    r = G.turn(grp, "凛,出什么事了")   # @点名凛 + 高 talkativeness
    ok("凛" in r["speakers"], "群聊回合:被点名的凛发言了")
    h = grp.history()
    ok(h[0]["role"] == "user" and any(x["role"] == "char" and x.get("speaker") for x in h), "落盘 user + 带 speaker 的 char 行")
    ok(r["vars"].get("气氛") == len([x for x in h if x["role"] == "char"]), "群级变量按发言人次数累加")
    # 第二回合:上一个发言者本轮被禁连说
    last_sp = [x["speaker"] for x in h if x["role"] == "char"][-1]
    r2 = G.turn(grp, "继续说")
    ok(last_sp not in r2["speakers"] or len(grp.meta()["members"]) == 1, "第二回合禁连说生效")
finally:
    G.llm.available, G.llm.generate = _av, _gen

if os.path.exists(os.environ["SV_LOCAL_CONF"]):
    os.remove(os.environ["SV_LOCAL_CONF"])

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
