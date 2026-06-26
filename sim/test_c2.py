"""C2 测试 —— 名词库(glossary) + 三级大纲(outline):休眠字节等价 + 注入写/审包 + 偏离/命名诊断。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_c2_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import checks, forge, lenses  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

w = World.create("w", "无限塔", genre="无限流")
t = Thread.create(w, "line", "线", genre="无限流")

# ---------- ① 休眠:无 glossary/outline → 写/审包不加 C2 键(字节等价);诊断无 C2 项 ----------
np0 = lenses.narrate_prep(w, t)
ok(not any(k in np0 for k in ("glossary", "chapter_outline", "outline_spine")),
   "休眠:无数据 → narrate_prep 不加 C2 键(字节等价)")
rp0 = lenses.review_prep(w, t, "随便一段正文。")
ok("glossary" not in rp0 and "outline_spine" not in rp0, "休眠:无数据 → review_prep 不加 C2 键")
for i in range(1, 4):
    t.add_chapter(f"第{i}章,苏栀继续登塔,稳扎稳打。", str(i))
rules0 = [f["rule"] for f in checks.reflect_diagnose(t)["findings"]]
ok(not any(r.startswith("偏离细纲") or r == "命名混用" for r in rules0), "休眠:无 outline/glossary → 无 C2 诊断")

# ---------- ② glossary:落盘 → 注入 narrate/review/thread prep ----------
w.save_glossary({"terms": [{"name": "苏栀", "category": "人名", "aliases": ["小栀", "阿栀"], "enabled": True}]})
ok(w.glossary()["terms"][0]["name"] == "苏栀", "glossary 落盘")
np = lenses.narrate_prep(w, t)
ok(np.get("glossary") and np["glossary"][0]["name"] == "苏栀", "narrate_prep 注入 glossary")
ok(lenses.review_prep(w, t, "正文").get("glossary"), "review_prep 注入 glossary")
ok(forge.thread_prep(w, "新线").get("glossary"), "thread_prep(世界已有名词库)注入 glossary")

# ---------- ③ outline:落盘 → 写章注入本章细纲 + 卷/节点脊柱 ----------
t.save_outline({"volumes": [{"id": "v1", "title": "第一卷"}],
                "beats": [{"id": "b1", "title": "开端", "kind": "转折"}],
                "chapters": {"4": {"goal": "破第七层", "cast": ["苏栀", "林晚"], "target_hanzi": 2000}}})
np2 = lenses.narrate_prep(w, t)   # 下一章 = 4(已有 3 章)
ok(np2.get("chapter_outline", {}).get("goal") == "破第七层", "narrate_prep 注入本章(ch4)六元细纲")
ok(np2.get("outline_spine", {}).get("beats"), "narrate_prep 注入卷/节点脊柱")

# ---------- ④ 诊断:偏离细纲(字数/出场) + 命名混用 ----------
t.add_chapter("小栀很短。阿栀也在。", "4")   # 字数远低于 2000 + 缺苏栀/林晚 + 混用小栀/阿栀
rules = [f["rule"] for f in checks.reflect_diagnose(t)["findings"]]
ok("偏离细纲·字数" in rules, "诊断:偏离细纲·字数(ch4 远低于目标)")
ok("偏离细纲·出场" in rules, "诊断:偏离细纲·出场(缺苏栀/林晚)")
ok("命名混用" in rules, "诊断:命名混用(小栀/阿栀)")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
