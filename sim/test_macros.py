"""H1.2 测试 —— macros 内联宏:{{getvar}} 取值(深路径) / {{roll::NdM}} 骰子(可复现) / {{random}} / {{if}}。"""
from __future__ import annotations

import random
import sys

from sv import macros

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# getvar:浅 + 深路径
ok(macros.expand("好感{{getvar::好感}}", {"好感": 80}) == "好感80", "getvar 浅路径取值")
ok(macros.expand("{{getvar::关系.张三.好感}}", {"关系": {"张三": {"好感": 7}}}) == "7", "getvar 深路径取值")
ok(macros.expand("{{getvar::不存在}}", {}) == "", "getvar 缺失 → 空串")

# roll:NdM + 单面,且可复现(注入 rng)
out = macros.expand("掷骰:{{roll::3d6}}", {}, random.Random(42))
val = int(out.replace("掷骰:", ""))
ok(3 <= val <= 18, f"roll 3d6 落在 [3,18]({val})")
ok(macros.expand("{{roll::3d6}}", {}, random.Random(42)) == macros.expand("{{roll::3d6}}", {}, random.Random(42)),
   "同 seed → 同结果(可复现)")
ok(1 <= int(macros.expand("{{roll::20}}", {}, random.Random(1))) <= 20, "roll 单面 d20")

# random:从候选选一
ok(macros.expand("{{random::甲,乙,丙}}", {}, random.Random(0)) in {"甲", "乙", "丙"}, "random 选一")

# if:变量/字面量比较
ok(macros.expand("{{if::好感>50::亲密::疏离}}", {"好感": 80}) == "亲密", "if 真分支")
ok(macros.expand("{{if::好感>50::亲密::疏离}}", {"好感": 20}) == "疏离", "if 假分支")
ok(macros.expand("{{if::5>=5::是::否}}", {}) == "是", "if 字面量比较")

# 无宏直通 + 不写变量(只读)
ok(macros.expand("纯文本无宏") == "纯文本无宏", "无宏文本原样返回")
d = {"好感": 80}
macros.expand("{{getvar::好感}}", d)
ok(d == {"好感": 80}, "宏只读,不改 data")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
