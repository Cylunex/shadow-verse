"""元件库测试 —— 起始库灌入、幂等、数据自洽、取料相关度。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_codex_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import codex, codex_starter  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

S = codex_starter.STARTER
# 数据自洽
ok(len(S) >= 30, f"起始库规模足({len(S)} 个)")
ok(all(c in codex.CATEGORIES for c, *_ in S), "所有元件类别合法")
keys = [(c, i) for c, i, *_ in S]
ok(len(keys) == len(set(keys)), "元件 类别+id 全局唯一")
ok(all(i == i.lower() and " " not in i for _, i, *_ in S), "id 全为 kebab-case")
ok(all(summary.strip() for _, _, summary, *_ in S), "每个元件都有 AI摘要")
ok(all(tags for *_, tags, _ in S), "每个元件都有标签")
cats = {c for c, *_ in S}
ok(len(cats) == len(codex.CATEGORIES), f"覆盖全部 {len(codex.CATEGORIES)} 个类别")

# 灌入 + 幂等
r1 = codex.seed_starter()
ok(r1["added"] == len(S) and r1["total"] == len(S), "首次灌入全部新增")
r2 = codex.seed_starter()
ok(r2["added"] == 0 and r2["skipped"] == len(S), "再次灌入幂等(全跳过)")

# 取料相关度(锻造器会这样取)——用贴合某元件 AI摘要的查询,命中应靠前
ok(any(e["id"] == "conservation-cost" for e in codex.pick("越界用力必付等价代价 力量守恒")[:3]),
   "取料命中『守恒代价』元件(前3)")
ok(any(e["id"] == "rule-paradox-survival" for e in codex.pick("照做活违则死 矛盾处藏生路")[:3]),
   "取料命中『规则悖论生存』元件(前3)")
ok(codex.pick("", category="themes") and all(e["category"] == "themes" for e in codex.pick("", category="themes")),
   "按类别取料只返回该类")
ok(any(e["id"] == "cold-protector" for e in codex.pick("外冷内热 守护 护人", category="characters")),
   "角色取料命中守护者原型")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
