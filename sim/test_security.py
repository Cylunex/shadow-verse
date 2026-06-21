"""导入器安全三件套 —— 路径遍历过滤 / JSON 体积上限 / 日志脱敏。"""
from __future__ import annotations

import json
import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_sec_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import importer, util  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# 路径遍历过滤
ok(util.safe_name("../../etc/passwd") == "etcpasswd", "剥 ../ 与路径分隔符")
ok(util.safe_name("a/b\\c") == "abc", "剥正反斜杠")
ok(util.safe_name("x" * 500, maxlen=200) == "x" * 200, "限长 200")
ok(util.safe_name("") == "x" and util.safe_name("...") == "x", "空/纯点退化为 x")
ok(util.safe_name("正常名") == "正常名", "正常名保留(含中文)")

# JSON 体积上限
util.guard_size("小数据", limit=1000, what="卡")   # 不抛
ok(True, "小数据不触发上限")
try:
    util.guard_size("x" * 2000, limit=1000, what="卡"); ok(False, "超限应报错")
except ValueError as e:
    ok("过大" in str(e), "超限报 ValueError")
try:
    importer.parse_card("{" + "0" * (9 * 1024 * 1024) + "}"); ok(False, "超大卡应报错")
except ValueError as e:
    ok("过大" in str(e), "parse_card 体积上限生效(>8MB)")

# 日志脱敏
secret = {"name": "x", "OPENAI_API_KEY": "sk-real", "nested": {"token": "abc", "ok": 1},
          "list": [{"password": "p"}]}
red = util.redact(secret)
ok(red["OPENAI_API_KEY"] == "***" and red["nested"]["token"] == "***", "敏感键脱敏")
ok(red["nested"]["ok"] == 1 and red["name"] == "x", "非敏感值保留")
ok(red["list"][0]["password"] == "***", "列表内嵌套脱敏")
ok(secret["OPENAI_API_KEY"] == "sk-real", "脱敏不改原对象")

# 真实卡仍正常导入(安全检查不误伤)
v2 = {"spec": "chara_card_v2", "data": {"name": "苏晴", "description": "插画师", "first_mes": "你来了。"}}
c = importer.parse_card(json.dumps(v2, ensure_ascii=False))
ok(c["name"] == "苏晴", "正常卡导入不受安全检查影响")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
