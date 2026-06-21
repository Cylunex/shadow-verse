"""中文写作工艺库测试 —— craft 新增技法 + 注入 narrate/play 包。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_craft_")

from sv import clock, craft  # noqa: E402

clock.use_virtual()

from sv import lenses  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# 工艺库齐全
ok(len(craft.HOOK_TECHNIQUES) == 13, "悬念钩十三式齐全")
ok(len(craft.CHAPTER_OPENERS) == 7, "章首引子七式齐全")
ok(len(craft.EXPANSION_TECHNIQUES) == 6, "扩充六技法齐全")
ok(craft.DIALOGUE_CRAFT and craft.ANTI_WATER and craft.HOOK_ARCS, "对话/防注水/三层弧齐全")
ok("两难抉择" in craft.hook_menu() and "突然揭示" in craft.hook_menu(), "钩子名录可注入")
ok(craft.PLAY_PROTOCOL and any("权限分离" in p for p in craft.PLAY_PROTOCOL), "play 权限分离协议")

# narrate_prep 注入工艺库
w = World.create("w", "W", genre="玄幻")
LocalEntity.create(w, "hero", "主角", role="main")
t = Thread.create(w, "line", "测试线", genre="玄幻")
pkt = lenses.narrate_prep(w, t, focus=["hero"])
ok("craft_library" in pkt, "narrate 包带 craft_library")
lib = pkt["craft_library"]
ok(lib["hook_techniques"] and lib["chapter_openers"] and lib["suspense_curve"], "工艺库字段完整")
ok("hook_arcs" in lib and "expansion" in lib, "三层弧/扩充技法在包内")

# 自检 + 一致性校验(interactive-novel 吸收)
ok(len(craft.OUTPUT_SELF_CHECK) == 6 and any("两段" in x for x in craft.OUTPUT_SELF_CHECK), "输出前6项自检清单")
ok(len(craft.CONSISTENCY_CHECKS) == 5 and any("时间线" in x for x in craft.CONSISTENCY_CHECKS), "一致性5校验")
ok("增量" in craft.VAR_UPDATE_PROTOCOL, "变量增量UPDATE协议")

# play_prep 注入协议
pp = lenses.play_prep(w, t, "雨夜对峙", ["hero"])
ok("protocol" in pp and any("双段输出" in x for x in pp["protocol"]), "play 包带双段输出协议")
ok("self_check" in pp and "var_protocol" in pp, "play 包带自检清单+变量协议")
# review_prep 带一致性
rp = lenses.review_prep(w, t, "测试正文。")
ok("consistency" in rp and len(rp["consistency"]) == 5, "审校包带一致性5校验")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
