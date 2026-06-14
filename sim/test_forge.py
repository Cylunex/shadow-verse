"""锻造 + 元件 + 配方测试 —— AIGC 取料、谱系、题材配方。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_forge_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import codex, forge, recipes  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# 元件取料
codex.add("worlds", "rule-tower", "无限规则之塔", tags=["无限流"])
codex.add("mechanics", "qi-debt", "气债守恒", tags=["力量"])
codex.add("conflicts", "inner-mole", "队伍内鬼", tags=["背叛"])
pick = codex.pick("无限流 规则 塔")
ok(len(codex.all_elements()) == 3, "元件入库 3 个")
ok(pick and pick[0]["id"] == "rule-tower", "取料按相关度排序")
ok(codex.pick("", category="mechanics")[0]["category"] == "mechanics", "取料按类别过滤")

# world_prep:无题材→列可选题材;有题材→带配方
wp0 = forge.world_prep("一座塔")
ok("available_genres" in wp0 and len(wp0["codex"]) > 0, "world_prep 无题材:列可选题材+取料")
wp1 = forge.world_prep("一座塔", genre="无限流")
ok(wp1.get("recipe", {}).get("pacing"), "world_prep 带题材:注入配方")

# world_commit:谱系 forge
forge.world_commit("tower", "塔", "# 塔\n规则地狱。\n", genre="无限流", prompt="造塔", from_codex=["rule-tower"])
w = World.load("tower")
ok(w.meta()["provenance"]["source"] == "forge", "world_commit 盖 forge 谱系")
ok(w.meta()["provenance"]["from_codex"] == ["rule-tower"], "谱系记录用了哪些元件")

# entity_commit / thread_prep 配方按世界题材
forge.entity_commit(w, "hero", "主角", "# 主角\n", role="main", prompt="守护者")
ok(LocalEntity.load(w, "hero").card()["provenance"]["source"] == "forge", "entity 盖谱系")
tp = forge.thread_prep(w, "第一次攀登")
ok(tp["recipe"]["pacing"] == recipes.get("无限流")["pacing"], "thread_prep 配方=世界题材配方")

# 配方子串匹配
ok(recipes.get("都市黑道")["pacing"] == recipes.get("都市")["pacing"], "配方子串匹配:都市黑道→都市")
ok(recipes.get("未知题材xyz")["pacing"] == recipes.DEFAULT["pacing"], "未知题材→DEFAULT")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
