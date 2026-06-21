"""创作包测试 —— 角色卡生成包(8字段) + 四类世界书内容规范 + gen_card(假LLM)。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_cr_")
os.environ["SV_LOCAL_CONF"] = tempfile.mktemp(suffix=".conf")
os.environ.pop("SV_PROVIDER", None)

from sv import clock  # noqa: E402

clock.use_virtual()

import sv.forge as forge  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# 角色卡生成包
cp = forge.card_prep("一个外冷内热的赏金猎人", genre="赛博朋克")
ok(cp["kind"] == "card" and len(cp["required_fields"]) == 8, "卡生成包:8 必填字段")
ok(cp["required_fields"][0] == "name" and "appearance" in cp["required_fields"], "字段含 name/appearance")
ok("recipe" in cp and "field_specs" in cp, "带题材配方+字段规范")

# 世界书生成包
wp = forge.worldbook_prep("末日废土城市", genre="科幻")
ok(wp["order"] == ["STATUS", "USER_SETTING", "WORLD_VIEW", "SUPPLEMENT"], "世界书四类生成顺序")
ok(wp["classes"]["STATUS"]["constant"] is True and wp["classes"]["STATUS"]["order"] == 1, "STATUS 常驻 order=1")
ok(wp["classes"]["SUPPLEMENT"]["constant"] is False and wp["classes"]["SUPPLEMENT"]["position"] == 2, "SUPPLEMENT 关键词触发 position=2")
ok("≥5 条" in wp["classes"]["SUPPLEMENT"]["spec"] or "5" in wp["classes"]["SUPPLEMENT"]["spec"], "SUPPLEMENT 规范含数量要求")

# gen_card(假 LLM)
_av, _gen = forge.llm.available, forge.llm.generate
forge.llm.available = lambda: True
forge.llm.generate = lambda s, u, **k: '```json\n{"name":"莉拉","description":"赏金猎人","personality":"外冷内热","scenario":"霓虹街","first_mes":"找我?","mes_example":"<START>{{char}}: 哼。","tags":["赛博朋克"],"appearance":"silver hair, cyber eyes"}\n```'
try:
    card = forge.gen_card("赏金猎人", genre="赛博朋克")
    ok(card["name"] == "莉拉" and card["appearance"] == "silver hair, cyber eyes", "gen_card 解析 8 字段")
    ok(card["tags"] == ["赛博朋克"] and card["_genre"] == "赛博朋克", "tags 数组 + 元信息")
finally:
    forge.llm.available, forge.llm.generate = _av, _gen

if os.path.exists(os.environ["SV_LOCAL_CONF"]):
    os.remove(os.environ["SV_LOCAL_CONF"])

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
