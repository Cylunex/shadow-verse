"""T2.4 测试 —— webapp 跨世界只读投影:overview.souls + api_soul_incarnations(化身对照页数据)。
   只验薄路由投影形状(引擎逻辑由 test_ascension 覆盖);不开 HTTP,直接调投影函数。"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_webproj_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import ascension, nexus, webapp  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# 建两世界 + 一角色,提取为魂,连门,召唤过去 —— 造出一魂两化身
w1 = World.create("tower", "无限之塔", genre="无限流")
e = LocalEntity.create(w1, "suzhi", "苏栀", role="main",
                       body="# 苏栀\n## 核心事实\n- 绷紧护人\n- 不伤无辜\n")
e.sediment("第一层替你挡了一刀", level="持久", where="ch:1")
e.sediment("认定:护住该护的人", level="身份", where="ch:2")
ascension.extract(w1, "suzhi")
w2 = World.create("linjiang", "临江", genre="都市黑道")
nexus.link_worlds("tower", "linjiang", "裂隙")
ascension.summon("suzhi", w2, entry="本体进")

# ---------- overview.souls(星图/角色页用)----------
ov = webapp.api_overview()
ok("souls" in ov and isinstance(ov["souls"], list), "overview 暴露 souls 列表")
ok("worlds" in ov and "nexus" in ov, "overview 既有 worlds/nexus 契约不变(附加而非替换)")
soul = next((s for s in ov["souls"] if s["id"] == "suzhi"), None)
ok(soul is not None, "overview.souls 含被提取的魂")
ok(soul and set(soul.get("worlds", [])) == {"tower", "linjiang"}, "soul.worlds 投影为两化身世界 id(供星图连线)")
ok(soul and soul.get("incarnations") == ["tower/suzhi", "linjiang/suzhi"], "soul.incarnations 为 world/entity 引用")

# ---------- api_soul_incarnations(化身对照页)----------
d = webapp.api_soul_incarnations("suzhi")
ok(d["id"] == "suzhi" and d["name"] == "苏栀", "incarnations:魂 id/名")
ok(d["anchors"] == ["绷紧护人", "不伤无辜"], "incarnations:共享锚点(跨世界一致)")
ok(isinstance(d["identity"], list) and any("护住该护的人" in t for t in d["identity"]),
   "incarnations:共享身份记忆(所有化身)")
incs = d["incarnations"]
ok(len(incs) == 2, "incarnations:两具化身")
by_world = {i.get("world"): i for i in incs}
ok("tower" in by_world and "linjiang" in by_world, "incarnations:两世界都在")
t = by_world["tower"]
ok(t.get("world_name") == "无限之塔" and t.get("genre") == "无限流", "incarnations:带世界名/题材")
ok("state" in t and "experiences" in t and "exp_count" in t, "incarnations:带 state/experiences/exp_count")
ok(t.get("exp_count", 0) >= 1, "incarnations:起源化身保留本地经历(持久级)")

# ---------- 化身所在世界被删 → 优雅标记 missing,不抛错 ----------
shutil.rmtree(World("linjiang").dir)
d2 = webapp.api_soul_incarnations("suzhi")
miss = [i for i in d2["incarnations"] if i.get("missing")]
ok(len(miss) == 1 and miss[0]["world"] == "linjiang", "化身世界缺失 → 标记 missing 不报错")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
