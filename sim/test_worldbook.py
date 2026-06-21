"""世界书运行时触发引擎测试 —— matchKey / selective 逻辑 / 常驻 / 递归 lore / 预算 / 导入+撤销同步。"""
from __future__ import annotations

import json
import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_wb_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import importer, worldbook  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# ---- 触发原语 ----
ok(worldbook.match_key("他走进画室", "画室"), "中文子串命中")
ok(not worldbook.match_key("他走进书房", "画室"), "未命中不误报")
ok(worldbook.match_key("the cat sat", "cat", whole_word=True), "ASCII 全词命中")
ok(not worldbook.match_key("category here", "cat", whole_word=True), "ASCII 全词不命中子串")
ok(worldbook.match_key("代号 Vega-7 出现", "/Vega-\\d/"), "正则键命中(区分大小写)")
ok(worldbook.match_key("代号 vega-7 出现", "/Vega-\\d/i"), "正则键 i 标志忽略大小写")

# ---- selective 次键逻辑 ----
e = {"keys": ["规矩"], "secondary_keys": ["老城", "顶楼"], "selective": True, "logic": "and_all"}
ok(worldbook.entry_matches(e, "这座城讲规矩,老城区的顶楼尤甚"), "and_all 全中才触发")
ok(not worldbook.entry_matches(e, "这座城讲规矩"), "and_all 缺次键不触发")
e2 = {**e, "logic": "and_any"}
ok(worldbook.entry_matches(e2, "这座城讲规矩,老城区"), "and_any 命中一个即触发")
e3 = {**e, "logic": "not_any"}
ok(not worldbook.entry_matches(e3, "规矩与老城"), "not_any 次键出现则不触发")
ok(worldbook.entry_matches(e3, "只讲规矩"), "not_any 次键不出现才触发")

# ---- 扫描:常驻 + 关键词 + 预算 ----
w = World.create("w", "W", genre="都市")
worldbook.add_entries(w, [
    {"keys": [], "constant": True, "content": "本城以『规矩』运转。", "comment": "总则"},
    {"keys": ["画室"], "content": "她的画室在老城区顶楼。", "comment": "画室"},
    {"keys": ["雨夜"], "content": "雨夜城里灯火模糊。", "comment": "雨夜"},
], source="seed")
r = worldbook.scan(w, "他冒着雨夜来到画室门口")
names = [a["name"] for a in r["activated"]]
ok("总则" in names, "常驻条目恒激活")
ok("画室" in names and "雨夜" in names, "关键词条目按上下文激活")
r2 = worldbook.scan(w, "今天天气不错")
ok([a["name"] for a in r2["activated"]] == ["总则"], "无关键词时只剩常驻")

# ---- 递归 lore(命中内容里的词再触发)----
wr = World.create("wr", "WR", genre="玄幻")
worldbook.add_entries(wr, [
    {"keys": ["玄铁令"], "content": "持玄铁令者可号令『影卫』。", "comment": "玄铁令"},
    {"keys": ["影卫"], "content": "影卫是只听令牌的死士。", "comment": "影卫"},
], source="seed")
rr = worldbook.scan(wr, "他亮出玄铁令")
ok({"玄铁令", "影卫"} <= {a["name"] for a in rr["activated"]}, "递归 lore:玄铁令→影卫被连带激活")

# ---- 预算截断 ----
wb = World.create("wb", "WB", genre="都市")
worldbook.add_entries(wb, [{"keys": ["触发"], "content": "甲" * 600, "comment": "A", "order": 1},
                           {"keys": ["触发"], "content": "乙" * 600, "comment": "B", "order": 2},
                           {"keys": ["触发"], "content": "丙" * 600, "comment": "C", "order": 3}], source="seed")
rb = worldbook.scan(wb, "触发", budget_chars=1000)
ok(rb["count"] < 3 and rb["chars"] <= 1200, "预算截断:不超字符上限")
ok(rb["activated"][0]["name"] == "A", "按 order 排序(A 在前)")

# ---- 导入角色卡 → 结构化世界书,撤销同步剥离 ----
v2 = {"spec": "chara_card_v2", "data": {
    "name": "苏晴", "description": "插画师", "first_mes": "你来了。",
    "character_book": {"entries": [
        {"keys": ["画室"], "content": "顶楼画室", "constant": False, "comment": "画室"},
        {"keys": ["规矩"], "content": "讲规矩", "constant": True}]}}}
c = importer.parse_card(json.dumps(v2, ensure_ascii=False))
wi = World.create("wi", "WI", genre="都市")
res = importer.import_card(wi, c, role="main")
ok(worldbook.summary(wi)["total"] == 2, "导入卡的世界书进了触发引擎")
scan_i = worldbook.scan(wi, "她在画室里")
ok(any(a["name"] == "画室" for a in scan_i["activated"]), "导入条目可被触发")
importer.undo_import(wi, res["entity"])
ok(worldbook.summary(wi)["total"] == 0, "撤销导入:触发引擎条目同步剥离")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
