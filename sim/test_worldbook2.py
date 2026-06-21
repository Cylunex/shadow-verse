"""世界书高级特性 —— timed effects(sticky/cooldown/delay)/ 概率 / 互斥组 / 位置分桶。"""
from __future__ import annotations

import os
import random
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_wb2_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import worldbook as WB  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

def names(r): return [a["name"] for a in r["activated"]]

# ---- sticky:命中后粘附 N 楼,即使后续不再命中 ----
w = World.create("w", "W", genre="都市")
WB.add_entries(w, [{"keys": ["门"], "content": "那扇门吱呀作响", "comment": "门", "sticky": 3}], source="s")
r0 = WB.scan(w, "他推开门", floor=0, state_key="chat")
ok("门" in names(r0), "sticky 条目首次命中激活")
r1 = WB.scan(w, "天气不错", floor=1, state_key="chat")
ok("门" in names(r1) and r1["activated"][0]["sticky"], "sticky:不命中也粘附(楼1)")
r3 = WB.scan(w, "天气不错", floor=3, state_key="chat")
ok("门" not in names(r3), "sticky:到期(楼3=start0+3)失效")

# ---- cooldown:命中后冷却 N 楼不再触发 ----
w2 = World.create("w2", "W2", genre="都市")
WB.add_entries(w2, [{"keys": ["彩蛋"], "content": "隐藏彩蛋", "comment": "彩蛋", "cooldown": 2}], source="s")
c0 = WB.scan(w2, "彩蛋", floor=0, state_key="chat")
ok("彩蛋" in names(c0), "cooldown 条目首次命中")
c1 = WB.scan(w2, "彩蛋", floor=1, state_key="chat")
ok("彩蛋" not in names(c1), "cooldown:冷却期内不再触发(楼1)")
c2 = WB.scan(w2, "彩蛋", floor=2, state_key="chat")
ok("彩蛋" in names(c2), "cooldown:楼2 冷却结束可再触发")

# ---- delay:前 N 楼内不可激活 ----
w3 = World.create("w3", "W3", genre="都市")
WB.add_entries(w3, [{"keys": ["秘密"], "content": "后期才解锁的秘密", "comment": "秘密", "delay": 3}], source="s")
d1 = WB.scan(w3, "秘密", floor=1, state_key="chat")
ok("秘密" not in names(d1), "delay:楼1<3 不激活")
d3 = WB.scan(w3, "秘密", floor=3, state_key="chat")
ok("秘密" in names(d3), "delay:楼3 解锁")

# 无 floor/state_key → 时效全关(backward 兼容)
ns = WB.scan(w3, "秘密")
ok("秘密" in names(ns), "无 floor:时效关闭,delay 不生效(无状态兼容)")

# ---- 概率触发 ----
w4 = World.create("w4", "W4", genre="都市")
WB.add_entries(w4, [{"keys": ["运气"], "content": "罕见事件", "comment": "罕见", "probability": 0, "useProbability": True},
                    {"keys": ["运气"], "content": "必现", "comment": "必现", "probability": 100, "useProbability": True}], source="s")
pr = WB.scan(w4, "运气", rng=random.Random(1))
ok("必现" in names(pr) and "罕见" not in names(pr), "概率:p=0 不触发,p=100 必触发")

# ---- 互斥组:同组只激活一条(order 高者)----
w5 = World.create("w5", "W5", genre="都市")
WB.add_entries(w5, [{"keys": ["天气"], "content": "晴", "comment": "晴", "group": "weather", "order": 1},
                    {"keys": ["天气"], "content": "雨", "comment": "雨", "group": "weather", "order": 5}], source="s")
gr = WB.scan(w5, "今天天气", rng=random.Random(1))
ok(len([n for n in names(gr) if n in ("晴", "雨")]) == 1, "互斥组:同组只激活一条")

# ---- 位置分桶(flatten=False)----
w6 = World.create("w6", "W6", genre="都市")
WB.add_entries(w6, [{"keys": [], "constant": True, "content": "总则", "comment": "总则", "position": 0},
                    {"keys": ["近况"], "content": "贴着对话的设定", "comment": "近况", "position": 4, "depth": 2, "role": 0}], source="s")
bk = WB.scan(w6, "聊聊近况", flatten=False)
ok("buckets" in bk and any("总则" in x for x in bk["buckets"]["before_char"]), "position 0 → before_char 桶")
ok(bk["depth_msgs"] and bk["depth_msgs"][0]["depth"] == 2, "position 4 → @D depth_msgs(深度2)")
ok(bk["injection"], "flatten=False 仍给 injection(兼容)")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
