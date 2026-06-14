"""narrate 产线测试(stub 路径)—— 审校/反思包、确定性审校、产线编排写→审→落。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_nar_")
os.environ["SV_PROVIDER"] = "stub"

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import lenses  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

w = World.create("w", "W", genre="无限流")
t = Thread.create(w, "t", "线", genre="无限流")
LocalEntity.create(w, "hero", "主角", role="main")

chap = "主角挡在门前。" * 30

# 审校包(交宿主)
rp = lenses.review_prep(w, t, chap)
ok(rp["role"] == "review" and "rubric" in rp and "auto_checks" in rp, "审校包带 rubric + 客观质检")

# 确定性审校(stub 无 LLM:verdict=pass,findings 含客观项)
rv = lenses.narrate_review(w, t, chap)
ok(rv["verdict"] == "pass", "stub 审校 verdict=pass(无 LLM 不强制修订)")
ok("auto_checks" in rv and isinstance(rv["findings"], list), "审校返回 findings + auto_checks")

# 反思包 + stub 反思
fp = lenses.reflect_prep(w, t, 5)
ok(fp["role"] == "reflect" and "focus" in fp, "反思包带 focus")
rf = lenses.narrate_reflect(w, t, 5)
ok(rf["suggested_sediments"] == [] and "note" in rf, "stub 反思:无 LLM 给提示、不瞎补")

# 产线编排:写→审→落(stub 出占位草稿也能跑通整条)
n0 = t.last_chapter_no()
trace = lenses.narrate_run(w, t, intent="开篇")
ok("reviews" in trace and len(trace["reviews"]) >= 1, "产线跑了审校")
ok(trace["revisions"] == 0, "stub 无 LLM 不进修订循环(不死循环)")
ok("receipt" in trace and trace["receipt"]["chapter"] == n0 + 1, "产线落章(章号+1)")
ok(t.last_chapter_no() == n0 + 1, "落盘生效")

# no-commit 模式:不落盘,返回正文
before = t.last_chapter_no()
tr2 = lenses.narrate_run(w, t, intent="试", commit=False)
ok("chapter_text" in tr2 and "receipt" not in tr2, "no-commit:返回正文不落盘")
ok(t.last_chapter_no() == before, "no-commit:章数不变")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
