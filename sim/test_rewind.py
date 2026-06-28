"""回溯测试 —— 世界快照 + 拨回时钟(状态/世界线恢复 + 回溯前自动备份 + 回溯留痕)。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_rw_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import memory, rewind  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

w = World.create("tower", "无限之塔", genre="无限流")
e = LocalEntity.create(w, "chuyao", "楚瑶", role="main")
e.update_state({"mood": "平静", "location": "一层"})
t = Thread.create(w, "climb", "攀登")
t.add_beat("进入第一层", lens="play", where="play:1")

snap = rewind.snapshot(w, label="一层·平静")
ok(snap["id"] == "snap-001" and snap["beats"] == 1, "快照:记录 id + beat 计数")
ok(len(rewind.snapshots(w)) == 1, "snapshots 列出 1 个")

# 之后世界继续变(状态 + 世界线)
e.update_state({"mood": "惊惧", "location": "三层"})
t.add_beat("被规则反噬", lens="play", where="play:3")
ok(memory.read_state(e.dir)["mood"] == "惊惧" and len(t.beats()) == 2, "快照后世界继续变(mood/beats 变了)")

# 拨回时钟
r = rewind.rollback(w, "snap-001")
st = memory.read_state(e.dir)
ok(st["mood"] == "平静" and st["location"] == "一层", "回溯:实体状态恢复到快照那一刻")
ok(len(Thread(w, "climb").beats()) == 1, "回溯:世界线 beats 回到快照(多出的那条没了)")
ok(r["backup"] == "snap-002" and len(rewind.snapshots(w)) >= 2, "回溯前自动备份当前(可 redo)")
wl = Thread(w, "worldline")
ok(wl.exists() and wl.beats() and wl.beats()[-1]["lens"] == "cross" and "回溯" in wl.beats()[-1]["text"],
   "回溯本身留痕:世界线补一条 ⟲ 回溯 beat(因果不虚)")

# 边界:再 rollback 到自动备份 = redo 回到回溯前
r2 = rewind.rollback(w, "snap-002")
ok(memory.read_state(e.dir)["mood"] == "惊惧", "可 redo:回溯到自动备份 = 拨回到回溯前的惊惧态")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
