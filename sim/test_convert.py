"""H1.2 测试 —— convert 一稿多吃(差异化):章→CYOA / beats→剧本 / 对话→小说,各验转换包结构。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_convert_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import convert  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

w = World.create("w", "无限塔", genre="无限流")
t = Thread.create(w, "line", "登塔记", genre="无限流")
t.add_chapter("苏栀踏上第一层,在岔路口停下:是破门,还是绕行?", "抉择")
t.add_beat("苏栀得到第一层钥匙", lens="narrate", where="ch:1")
e = LocalEntity.create(w, "su", "苏栀", role="main")

# 章 → CYOA
p = convert.chapter_to(w, t, 1, "cyoa")
ok(p["from"] == "novel" and p["to"] == "cyoa", "章→CYOA:源/目标标记")
ok("岔路口" in p["material"], "材料 = 该章正文")
ok(bool(p.get("guide")) and isinstance(p.get("target"), dict), "带转换指引 + 目标模式包")

# beats → 剧本
pb = convert.beats_to(w, t, "screenplay")
ok(pb["from"] == "beats" and pb["to"] == "screenplay", "beats→剧本:源/目标标记")
ok("第一层钥匙" in pb["material"], "材料 = 事件 beats")

# 对话 → 小说(空历史也给合法包,不崩)
pc = convert.chat_to(w, e, "novel")
ok(pc["from"] == "chat" and pc["to"] == "novel" and "material" in pc, "对话→小说:结构合法(空历史不崩)")

# CYOA 产物 → 选项解析(给 branch 建分支)
ch = convert.cyoa_choices("1. 破门而入\n2. 绕行侧道\n3. 原地等待")
ok(len(ch) == 3 and ch[0]["label"] == "破门而入", "cyoa_choices 抽编号选项")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
