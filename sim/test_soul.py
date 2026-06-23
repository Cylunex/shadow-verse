"""魂薄核心测试 —— opt-in 升华:无 soul_id 时与今天字节等价;有魂时锚点走唯一真相、身份记忆跨化身共享。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_soul_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import memory  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.soul import Soul  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# ---------- 1) dormant:无 soul_id,行为同今天 ----------
w1 = World.create("tower", "无限之塔", genre="无限流")
e = LocalEntity.create(w1, "chuyao", "楚瑶", role="main",
                       body="# 楚瑶\n## 核心事实\n- 外冷内热\n- 不抛下队友\n")
ok(e.anchors() == ["外冷内热", "不抛下队友"], "无魂:锚点从 profile.md 核心事实读(同今天)")
e.sediment("第一次进副本", level="持久", where="ch:1")
e.sediment("看穿规则缝隙", level="身份", where="ch:2")
ok(len(memory.all_experiences(e.dir)) == 2, "无魂:身份级也落在化身本地(souls/ 不介入)")
ok(e._soul() is None, "无 soul_id → _soul() 为 None")
# soul_id 指向不存在的魂 → 仍回退本地(back-compat 安全)
e.set_card_field("soul_id", "ghost")
ok(e._soul() is None and e.anchors() == ["外冷内热", "不抛下队友"], "soul_id 指向不存在的魂:安全回退到本地")

# ---------- 2) 升华:建魂 + 绑 soul_id ----------
soul = Soul.create("chuyao", "楚瑶", anchors=["外冷内热", "不抛下队友", "对玩家逐渐心动"],
                   origin={"world": "tower", "entity": "chuyao"})
e.set_card_field("soul_id", "chuyao")
ok(e._soul() is not None, "绑定存在的魂 → _soul() 命中")
ok(e.anchors() == ["外冷内热", "不抛下队友", "对玩家逐渐心动"], "有魂:锚点走魂的唯一真相(anchors.md),不再读 profile")

# 身份级沉淀 → 进魂的 identity.jsonl(不进化身本地);持久仍进本地
before_local = len(memory.all_experiences(e.dir))
e.sediment("认定:绝不在副本里抛下他", level="身份", where="ch:5")
e.sediment("学会了急救", level="持久", where="ch:5")
ok(len(memory.all_experiences(e.dir)) == before_local + 1, "有魂:持久仍落本地化身")
from sv.memory import _identity_path  # noqa: E402
from sv.config import read_jsonl  # noqa: E402
ok(len(read_jsonl(_identity_path(soul.dir))) == 1, "有魂:身份级写进魂的 identity.jsonl(跨化身共享层)")

# retrieve union:化身能检索到魂的身份记忆
hits = " ".join(x["text"] for x in e.retrieve("抛下"))
ok("绝不在副本里抛下他" in hits, "有魂:retrieve 并入魂身份记忆(union)")

# ---------- 3) 一魂两化身:身份共享,episodic 隔离 ----------
w2 = World.create("hospital", "死亡医院", genre="恐怖")
inc2 = LocalEntity.create(w2, "chuyao", "楚瑶", role="main", body="# 楚瑶\n## 核心事实\n- 临时档案\n")
inc2.set_card_field("soul_id", "chuyao")
soul.add_incarnation("hospital", "chuyao")
ok(inc2.anchors() == e.anchors(), "另一世界的化身:锚点与本体一致(同一个魂)")
h2 = " ".join(x["text"] for x in inc2.retrieve("抛下"))
ok("绝不在副本里抛下他" in h2, "另一化身也检索得到魂的身份记忆(身份跨世界共享)")
# episodic 隔离:本体的"学会了急救"(本地持久)不出现在另一化身
ok("学会了急救" not in h2, "episodic 隔离:化身本地经历不串味到另一世界")
inc2.sediment("在医院走廊崩过一次", level="持久", where="ch:1")
h1 = " ".join(x["text"] for x in e.retrieve("走廊"))
ok("在医院走廊崩过一次" not in h1, "反向隔离:另一化身的本地经历也不串回本体")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
