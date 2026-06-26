"""H1.2 测试 —— provenance 谱系盖章:AIGC 一等公民,每个工件记「谁由什么生成」。"""
from __future__ import annotations

import sys

from sv import clock

clock.use_virtual()

from sv import provenance  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

s = provenance.stamp("forge", prompt="一座塔", from_codex=["c1", "c2"], parent="w/e")
ok(s["source"] == "forge", "记录 source")
ok(s["prompt"] == "一座塔" and s["from_codex"] == ["c1", "c2"] and s["parent"] == "w/e", "记录 prompt/from_codex/parent(血统链)")
ok(bool(s.get("generated_at")), "盖时间戳 generated_at")
s2 = provenance.stamp("manual")
ok(s2["source"] == "manual" and s2["from_codex"] == [] and s2["prompt"] == "" and s2["parent"] == "", "默认值齐全(空 codex/prompt/parent)")
ok(set(s) == {"source", "prompt", "from_codex", "parent", "generated_at"}, "字段集稳定(契约)")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
