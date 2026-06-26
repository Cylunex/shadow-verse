"""C1 测试 —— 创作工艺/配方外化为组件:缺数据字节等价 + 灌种后可编辑生效(4 类 kind)。"""
from __future__ import annotations

import os
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_comp_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import components, craft, recipes  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# ---------- ① 缺数据 = 逐字节回退种子(字节等价) ----------
ok(all(getattr(craft, a) == craft._SEED[a] for a in craft._BY_ATTR),
   "craft 全部 16 个 UPPER 缺数据=内置种子(字节等价)")
ok(craft.hook_menu() == "、".join(craft._SEED["HOOK_TECHNIQUES"].keys()), "hook_menu 缺数据=种子名录")
seedwc = craft._SEED["WRITER_CHECKLIST"]
ok(components.load_group("craft", "writer_checklist", "list", seedwc) is seedwc,
   "load_group 缺文件原样回种子(同一对象,零重建)")
R, A, D, PR, PD = recipes.RECIPES, recipes.AUDIT_DIMS, recipes.DEFAULT, recipes.PROFILES, recipes.PROFILE_DEFAULT
ok(recipes.get("无限流") == {**R["无限流"], "audit_dimensions": A["无限流"]}, "recipes.get 缺数据=常量配方+审校维度")
ok(recipes.get("都市黑道") == recipes.get("都市"), "recipes.get 子串匹配(都市黑道→都市)")
ok(recipes.get("未知xyz") == {**D, "audit_dimensions": A["_default"]}, "recipes.get 未知→DEFAULT")
ok(recipes.get_profile("无限流") == PR["无限流"] and recipes.get_profile("未知") == PD, "recipes.get_profile 缺数据=常量")
ok(recipes.genres() == list(R.keys()), "recipes.genres 缺数据=常量序")

# ---------- ② 灌种(幂等)----------
r = components.seed_all()
ok(r["added"] == r["total"] and r["total"] >= 19, f"seed_all 写出全部组(total={r['total']})")
ok(components.seed_all()["added"] == 0, "seed_all 幂等(再灌 0 新增)")

# ---------- ③ 编辑生效:4 类 kind ----------
components.upsert("craft", "writer_checklist", {"id": "0", "text": "X-去AI味-改写"})
ok(craft.WRITER_CHECKLIST[0] == "X-去AI味-改写", "list:upsert 一条 → 写手注入随之变")
components.upsert("craft", "hook_techniques", {"key": "突然揭示", "desc": "改后释义"})
ok(craft.HOOK_TECHNIQUES["突然揭示"] == "改后释义", "menu:upsert 改 desc 生效")
components.upsert("craft", "hook_techniques", {"key": "新钩型", "desc": "新增"})
ok(craft.HOOK_TECHNIQUES.get("新钩型") == "新增", "menu:新增一条生效")
components.upsert("craft", "growth_triggers", {"text": "新成长判据"})
ok(craft.GROWTH_TRIGGERS == "新成长判据", "note:upsert 单条生效")
components.upsert("recipes", "genres", {"key": "玄幻", "forbidden": ["新疲劳词"]})
ok(recipes.forbidden_words("玄幻") == ["新疲劳词"], "record:改 forbidden → checks 疲劳词随之变")
ok("pacing" in recipes.get("玄幻"), "record:改一字段不抹掉其余字段")

# ---------- ④ 删除 + 闭集白名单 ----------
components.delete("craft", "writer_checklist", "0")
ok(all(x != "X-去AI味-改写" for x in craft.WRITER_CHECKLIST), "delete 一条 → 注入少一条")
try:
    components.get_group("craft", "不存在的组"); ok(False, "未登记组应报错")
except ValueError:
    ok(True, "未登记 family/group 报错(闭集白名单)")
ok(len(components.list_groups()) >= 19, "list_groups 列出全部组(供管理台)")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
import sys  # noqa: E402
sys.exit(1 if F else 0)
