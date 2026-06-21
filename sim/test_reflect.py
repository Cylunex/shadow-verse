"""reflect 规则化诊断 + 四维相关章节反查 测试。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_rfl_")

from sv import checks, clock  # noqa: E402

clock.use_virtual()

from sv import lenses  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

w = World.create("w", "W", genre="玄幻")
t = Thread.create(w, "line", "测试线", genre="玄幻")

# 造 15 章 + 钩子 + beats
for i in range(1, 16):
    t.add_chapter(f"第{i}章正文内容,主角又前进了一步。", f"第{i}回")
t.add_hook("神秘玉佩的来历", type="event", level="主", plant_chapter=2, payoff_target=5)  # 已过期(now=15)
t.add_hook("宗门大比", type="event", level="中", plant_chapter=3, payoff_target=20)
t.add_beat("主角得到玉佩", lens="narrate", where="ch:002")
t.add_beat("初遇对手", lens="narrate", where="ch:004")
t.add_beat("最近一战", lens="narrate", where="ch:014")   # 在 exclude_recent 内

# 四维相关章节反查
rel = t.related_chapters(exclude_recent=10)
chaps = [r["chapter"] for r in rel]
ok(2 in chaps, "反查含伏笔埋设章(ch2)")
ok(5 in chaps, "反查含计划回收章(ch5)")
ok(4 in chaps, "反查含事件章(ch4)")
ok(14 not in chaps, "排除最近 10 章(ch14 不入)")
ok(all("reasons" in r and r["reasons"] for r in rel), "每条带 reasons")

# 规则化诊断
diag = checks.reflect_diagnose(t)
rules = [f["rule"] for f in diag["findings"]]
ok("伏笔过期" in rules, "诊断:伏笔过期(玉佩 ch5 未回收)")
ok(any(f["target"] == "writer" for f in diag["findings"]), "Finding 带 target=writer")
ok("target_summary" in diag and diag["target_summary"].get("writer", 0) >= 1, "target 汇总")
ok(diag["profile"]["stall_max"] == 2, "诊断带题材 profile(玄幻 stall_max=2)")
fo = next(f for f in diag["findings"] if f["rule"] == "伏笔过期")
ok("evidence" in fo and "suggestion" in fo, "Finding 含证据+建议")

# 钩子断档诊断(新线,无开放钩)
w2 = World.create("w2", "W2", genre="都市")
t2 = Thread.create(w2, "l2", "断档线", genre="都市")
for i in range(1, 5):
    t2.add_chapter(f"第{i}章。", f"{i}")
d2 = checks.reflect_diagnose(t2)
ok(any(f["rule"] == "钩子断档" for f in d2["findings"]), "诊断:钩子断档(无开放钩)")
ok(any(f["target"] == "recipe" for f in d2["findings"]), "钩子断档 target=recipe")

# 接进包
pkt = lenses.narrate_prep(w, t)
ok("related_chapters" in pkt, "narrate 包带相关章节反查")
rp = lenses.reflect_prep(w, t)
ok("diagnosis" in rp and rp["diagnosis"]["findings"], "reflect 包带规则化诊断")
nr = lenses.narrate_reflect(w, t)
ok("diagnosis" in nr and any("伏笔过期" in f for f in nr["findings"]), "narrate_reflect 输出诊断(无LLM也给)")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
