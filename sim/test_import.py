"""ST 角色卡导入测试 —— V1/V2/V3 JSON 解析、PNG 内嵌卡、世界书、落成 entity。"""
from __future__ import annotations

import base64
import json
import os
import struct
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_imp_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import importer, util  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# V2 卡(含世界书)
v2 = {"spec": "chara_card_v2", "spec_version": "2.0", "data": {
    "name": "苏晴", "description": "26岁插画师", "personality": "外冷内热", "scenario": "雨夜画室",
    "first_mes": "你来了。", "mes_example": "<START>{{char}}: 啧。", "tags": ["插画师", "都市"],
    "alternate_greetings": ["又是你。"],
    "character_book": {"entries": [
        {"keys": ["画室"], "content": "她的画室在老城区顶楼", "constant": False, "comment": "画室"},
        {"keys": ["规矩"], "content": "这座城讲规矩", "constant": True},
    ]}}}
c2 = importer.parse_card(json.dumps(v2, ensure_ascii=False))
ok(c2["name"] == "苏晴" and c2["personality"] == "外冷内热", "V2 卡字段解析")
ok(c2["character_book"] and len(c2["character_book"]["entries"]) == 2, "V2 带世界书")

# V1 平铺卡
v1 = {"name": "叶无道", "description": "黑道话事人", "personality": "护人", "first_mes": "谁?", "mes_example": ""}
c1 = importer.parse_card(json.dumps(v1, ensure_ascii=False))
ok(c1["name"] == "叶无道" and c1["spec"] == "v1", "V1 平铺卡解析")

# 落成 entity + 世界书并入 world.md
w = World.create("w", "W", genre="都市")
r = importer.import_card(w, c2, role="main")
e = LocalEntity.load(w, r["entity"])
ok(e.exists() and e.card()["name"] == "苏晴", "导入落成 entity")
ok(e.card()["role"] == "main" and e.card()["provenance"]["source"] == "import", "role + import 谱系")
prof = util.read_md(e.dir / "profile.md")
ok("外冷内热" in prof and "雨夜画室" in prof and "啧" in prof, "profile 含身份/场景/声音")
ok(r["lorebook_entries"] == 2 and "导入世界书" in util.read_md(w.dir / "world.md"), "世界书并入 world.md")
ok(e.card().get("tags") == ["插画师", "都市"], "标签带过来")

# 第二个中文名导入不撞 id(slug 都退化成 'x')
r2 = importer.import_card(w, c1, role="secondary")
ok(r2["entity"] != r["entity"], "两个中文名导入 id 不撞")
ok(LocalEntity(w, r2["entity"]).exists() and LocalEntity(w, r["entity"]).exists(), "两个导入实体并存")

# 撤销导入:删实体 + 剥世界书块
before_wm = util.read_md(w.dir / "world.md")
ok("导入世界书" in before_wm, "撤销前 world.md 有世界书块")
importer.undo_import(w, r["entity"])
ok(not LocalEntity(w, r["entity"]).exists(), "撤销:实体已删")
ok("来自角色卡 " + r["entity"] not in util.read_md(w.dir / "world.md"), "撤销:该卡世界书块已剥")
try:
    importer.undo_import(w, "ye-wudao") if False else None
    # 非导入实体不能撤销
    from sv.entity import LocalEntity as LE
    LE.create(w, "manual-x", "手建", role="npc")
    importer.undo_import(w, "manual-x"); ok(False, "非导入实体应拒绝撤销")
except ValueError:
    ok(True, "非导入实体拒绝撤销导入")

# 卡 → 新建独立世界
nw = importer.import_card_new_world(c2, role="main")
from sv.world import World as W2  # noqa: E402
ok(W2(nw["world"]).exists() and nw["new_world"], "卡建独立世界")
ok(LocalEntity(W2.load(nw["world"]), nw["entity"]).exists(), "角色落进新世界")
ok("雨夜画室" in util.read_md(W2.load(nw["world"]).dir / "world.md"), "scenario 进新世界背景")

# 世界融合:把新世界融进 w
from sv import merge  # noqa: E402
mw = World.create("dst-world", "目标", genre="都市")
mr = merge.merge_world(nw["world"], "dst-world")
ok(not W2(nw["world"]).exists() and mr["deleted_src"], "融合后源世界已删")
ok(len(mr["moved_entities"]) >= 1, "实体已搬进目标世界")
ok("融入自" in util.read_md(World.load("dst-world").dir / "world.md"), "源设定并入目标(标记块)")

# PNG 内嵌卡(构造一个带 tEXt 'chara' 的最小 PNG)
def _png_with_card(card_dict):
    sig = b"\x89PNG\r\n\x1a\n"
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + b"\x00\x00\x00\x00"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    b64 = base64.b64encode(json.dumps(card_dict, ensure_ascii=False).encode("utf-8"))
    text = chunk(b"tEXt", b"chara\x00" + b64)
    iend = chunk(b"IEND", b"")
    return sig + ihdr + text + iend

png = _png_with_card(v2)
cp = importer.parse_card(png)
ok(cp["name"] == "苏晴", "PNG 内嵌卡解出角色")

# PNG 卡图 → 头像
w3 = World.create("av-world", "AV", genre="都市")
ra = importer.import_card(w3, cp, role="main", avatar_png=png)
av = LocalEntity.load(w3, ra["entity"])
ok(ra.get("avatar") and av.avatar_rel() == ra["avatar"], "PNG 卡导入设了头像")
ok((av.dir / "avatar.png").exists(), "头像文件落盘")

# 坏数据优雅报错
try:
    importer.parse_card(b"\x89PNG\r\n\x1a\nnotreallypng")
    ok(False, "坏 PNG 应报错")
except ValueError:
    ok(True, "无内嵌卡的 PNG 报 ValueError")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
