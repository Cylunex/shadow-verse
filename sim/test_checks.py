"""确定性文风质检测试 —— 半角标点 / 重复短语 / 长句堆叠 / 题材审校维度。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_chk_")

from sv import checks, recipes  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# 半角标点(中文正文混用半角)
r = checks.check_text("他说,你来了.我知道了.她笑了,没回头.")
ok(r["halfwidth"] >= 3, f"半角标点检出({r['halfwidth']})")
ok(any("半角" in f for f in r["findings"]), "半角标点进 findings")

# 全角正文不误报
r2 = checks.check_text("他说,你来了。我知道了。她笑了,没回头。".replace(",", "，"))
ok(r2["halfwidth"] == 0, "全角正文不误报半角")

# 重复短语(口水/复读)
rep = checks.check_text("他握紧了拳头。" * 4 + "风很冷。")
ok(rep["repetition"], "重复短语检出")
ok(any("重复" in f for f in rep["findings"]), "重复短语进 findings")

# 长句堆叠(节奏单调)
longtext = "。".join(["他在塔的第一层缓慢地走过一条没有尽头的回廊每一步都踩在冰冷的石板上" for _ in range(5)]) + "。"
lr = checks.check_text(longtext)
ok(lr["long_run"] >= 4, f"长句连堆检出({lr['long_run']})")
ok(any("长句" in f for f in lr["findings"]), "长句堆叠进 findings")

# 干净短文不报这些
clean = checks.check_text("夜里很静。他站起身，推门出去。风迎面扑来。")
ok(not any(("半角" in f or "重复" in f or "长句" in f) for f in clean["findings"]), "干净短文不误报新检查")

# 题材审校维度随配方返回
ok("audit_dimensions" in recipes.get("无限流"), "配方带 audit_dimensions")
ok(recipes.get("都市黑道")["audit_dimensions"] == recipes.get("都市")["audit_dimensions"], "审校维度子串匹配(都市黑道→都市)")
ok(recipes.get("未知xyz")["audit_dimensions"] == recipes.AUDIT_DIMS["_default"], "未知题材→默认维度")
ok("pacing" in recipes.get("玄幻"), "配方原字段仍在(附加不破坏)")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
