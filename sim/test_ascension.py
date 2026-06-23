"""P3 测试 —— 升华(提取/创造)+ 跨世界召唤建在魂模型上:多元宇宙变真 + 世界有后果 + 升华落数值卡。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_asc_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import ascension, memory, nexus, varstate  # noqa: E402
from sv.config import read_jsonl  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.memory import _identity_path  # noqa: E402
from sv.soul import Soul  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# ---------- 提取(就地抽魂)----------
w1 = World.create("tower", "无限之塔", genre="无限流")
e = LocalEntity.create(w1, "chuyao", "楚瑶", role="main",
                       body="# 楚瑶\n## 核心事实\n- 外冷内热\n- 不抛下队友\n")
e.sediment("看穿第一层规则", level="持久", where="ch:1")
e.sediment("认定:绝不在副本抛下同伴", level="身份", where="ch:3")

r = ascension.extract(w1, "chuyao")
ok(e.card().get("soul_id") == "chuyao", "提取:原角色 card 设 soul_id(就地成为化身)")
ok(Soul.load("chuyao").anchors() == ["外冷内热", "不抛下队友"], "提取:魂 anchors 来自角色核心事实(唯一真相)")
ok(r["moved_identity"] == 1, "提取:身份级经历搬进魂")
ok(len(read_jsonl(_identity_path(Soul("chuyao").dir))) == 1, "魂 identity.jsonl 收到身份记忆")
locals_left = [x["level"] for x in memory.all_experiences(e.dir)]
ok("身份" not in locals_left and "持久" in locals_left, "身份级已从化身移除(免 union 重复),持久留本地")
panel = varstate.load(e)["data"]
ok("体魄" in panel and "关系" in panel and len(varstate.load(e)["meta"]) >= 20, "升华落多维数值攻略卡(attrs)")
ok(e.anchors() == ["外冷内热", "不抛下队友"], "化身锚点现走魂(retrieve/anchors 指针)")

# ---------- 召唤(跨世界穿越 + 世界有后果)----------
w2 = World.create("hospital", "死亡医院", genre="恐怖")
nexus.link_worlds("tower", "hospital", "副本裂隙")
s = ascension.summon("chuyao", w2, entry="本体进")
ok(s["incarnation"] == "chuyao" and s["entry"] == "本体进" and s["via"] == "副本裂隙", "召唤:经链接进入(本体进)")
inc2 = LocalEntity.load(w2, "chuyao")
ok(inc2.card().get("soul_id") == "chuyao", "目标世界化身出生即绑魂")
ok(inc2.anchors() == e.anchors(), "另一世界化身锚点与本体一致(同一个魂)")
hits = " ".join(x["text"] for x in inc2.retrieve("抛下"))
ok("绝不在副本抛下同伴" in hits, "化身检索到魂的身份记忆(身份跨世界共享)")
wl = Thread(w2, "worldline")
ok(wl.exists() and wl.beats() and wl.beats()[-1]["lens"] == "cross", "魂降临落 cross beat 到【目标世界线】(世界有后果)")
incs = Soul("chuyao").incarnations()
ok("tower/chuyao" in incs and "hospital/chuyao" in incs, "魂记录起源 + 新化身两具")

# 无链接 → 无门强召(约束教学,不静默失败)
w3 = World.create("oasis", "绿洲", genre="游戏")
s3 = ascension.summon("chuyao", w3)
ok(s3["entry"] == "无门强召", "无链接的世界:记为『无门强召』而非静默成功")

# ---------- 创造一个一出生就是魂的角色 ----------
r2 = ascension.create_soul(w1, "linshen", "林深", anchors=["沉默寡言", "守约"])
le = LocalEntity.load(w1, "linshen")
ok(le.card().get("soul_id") == "linshen" and le.anchors() == ["沉默寡言", "守约"], "创造即魂:绑定 + 锚点走魂")
ok("体魄" in varstate.load(le)["data"], "创造的魂也落数值攻略卡")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
