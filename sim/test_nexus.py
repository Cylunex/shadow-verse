"""枢纽测试 —— 强连接多元宇宙:升格、世界互联、跨世界召唤化身(灵魂一致/记忆独立)。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_nexus_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import memory, nexus  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.nexus import NexusEntity  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

w1 = World.create("w1", "世界一", genre="无限流")
w2 = World.create("w2", "世界二", genre="都市")
e = LocalEntity.create(w1, "hero", "主角", role="main", body="# 主角\n\n## 核心事实\n- 绷紧护人\n- 不伤无辜\n")
e.update_state({"location": "塔", "mood": "戒备"})
e.sediment("在塔里看穿规则", level="持久", where="ch:1")

# 升格
asr = nexus.ascend(w1, "hero")
ne = NexusEntity.load("hero")
ok(ne.exists(), "升格:枢纽实体落盘")
ok("绷紧护人" in ne.anchors(), "升格:anchors 从核心事实烘焙")
ok(asr["incarnation"] == "w1" and "w1" in ne.incarnations(), "升格:起源世界化身已播")
ok(len(memory.all_experiences(ne.incarnation_dir("w1"))) == 1, "升格:起源化身带上经历")
ok((ne.dir / "soul.md").exists(), "升格:灵魂文件生成")

# 世界互联(双向)
nexus.link_worlds("w1", "w2", "裂隙相连")
ok(any(l["relation"] == "裂隙相连" for l in nexus.links()), "互联:links.json 记边")
ok(any(l["to"] == "w2" for l in World.load("w1").meta()["links"]), "互联:w1 meta 记 →w2")
ok(any(l["to"] == "w1" for l in World.load("w2").meta()["links"]), "互联:w2 meta 记 →w1(双向)")

# 跨世界召唤化身
nexus.summon("hero", w2, entry="换皮进")
ok("w2" in NexusEntity.load("hero").incarnations(), "召唤:w2 化身已开")
ne.sediment("w2", "在世界二以新身份醒来", level="身份", where="cross")
w1_exp = memory.all_experiences(ne.incarnation_dir("w1"))
w2_exp = memory.all_experiences(ne.incarnation_dir("w2"))
ok(len(w1_exp) == 1 and len(w2_exp) == 1, "化身记忆独立:各世界各记各的")
ok(w1_exp[0]["text"] != w2_exp[0]["text"], "化身记忆不串味")
ok(ne.anchors() == NexusEntity.load("hero").anchors(), "灵魂 anchors 跨世界一致")
ok(ne.rebuild("w2")["anchors"] == ne.anchors(), "rebuild 任一化身共享同一灵魂 anchors")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
