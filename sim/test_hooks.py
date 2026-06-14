"""结构化钩子台账测试 —— 状态机、过期未回收审计、写作包注入、审校揪漏。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_hook_")
os.environ["SV_PROVIDER"] = "stub"

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import lenses  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

w = World.create("w", "W", genre="悬疑")
t = Thread.create(w, "t", "线", genre="悬疑")

# α 悬念 + 加钩子
t.set_alpha("背后捅刀的是谁")
ok(t.hooks_data()["alpha"] == "背后捅刀的是谁", "α 悬念落盘")
h1 = t.add_hook("内鬼线索", type="event", level="主", payoff_target=3)
h2 = t.add_hook("塔的真相", type="concept", level="α")
ok(h1["id"] == "hook-0001" and h1["status"] == "待回收", "加钩子带 id + 初始待回收")
ok(len(t.open_hooks()) == 2, "两条都是开放钩子")

# 状态机
t.update_hook(h1["id"], status="进行中")
ok(t.hooks_data()["hooks"][0]["status"] == "进行中", "状态机:推进到进行中")
ok(len(t.open_hooks()) == 2, "进行中仍算开放")

# 非法状态/层级/类型拒绝
for bad in (lambda: t.update_hook(h1["id"], status="瞎填"),
            lambda: t.add_hook("x", level="超"),
            lambda: t.add_hook("x", type="不存在")):
    try:
        bad(); ok(False, "非法值应拒绝")
    except ValueError:
        ok(True, "非法值被拒绝")

# 过期未回收审计:h1 计划 ch3 回收,推进到 ch5 仍开放 → overdue
lenses.narrate_commit(w, t, {"chapter_text": "x" * 60, "title": "1"})
for _ in range(4):
    lenses.narrate_commit(w, t, {"chapter_text": "x" * 60})
ok(t.last_chapter_no() == 5, "写到第5章")
od = t.overdue_hooks()
ok(any(h["id"] == h1["id"] for h in od), "h1(计划ch3)过期未回收被揪出")
ok(not any(h["id"] == h2["id"] for h in od), "h2(无回收章)不算过期")

# 审校自动揪漏(确定性,verdict=revise)
rv = lenses.narrate_review(w, t, "随便一段正文。")
ok(any(f["dim"] == "钩子" for f in rv["findings"]), "审校把过期钩子列为 findings")
ok(rv["verdict"] == "revise", "有过期钩子 → verdict=revise")

# 回收后不再过期
t.update_hook(h1["id"], status="已回收")
ok(not t.overdue_hooks(), "回收后过期清零")
ok(len(t.open_hooks()) == 1, "回收后开放钩子减一")

# 写作包注入 α + 开放钩子
pkt = lenses.narrate_prep(w, t)
ok(pkt["alpha"] == "背后捅刀的是谁" and any(h["id"] == h2["id"] for h in pkt["open_hooks"]), "写作包带 α + 开放钩子")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
