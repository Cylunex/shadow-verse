"""容错 JSON 解析测试 —— 直解 / 去围栏/思考块 / 对象切片 / 补闭合符 / 中文标点兜底。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_jl_")

from sv import jsonloose  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# ① 干净 JSON 直解
ok(jsonloose.loads('{"a":1,"b":[2,3]}') == {"a": 1, "b": [2, 3]}, "干净 JSON 直解")

# 已是对象/列表则原样过
ok(jsonloose.loads({"x": 1}) == {"x": 1}, "dict 原样返回")
ok(jsonloose.loads([1, 2]) == [1, 2], "list 原样返回")

# ② 代码围栏 + 前置说明文字
fenced = '好的,这是结果:\n```json\n{"verdict":"pass","findings":[]}\n```\n以上。'
ok(jsonloose.loads(fenced) == {"verdict": "pass", "findings": []}, "去围栏+说明文字")

# 思考块 <think>...</think> 剥离
think = '<think>我先想想钩子</think>\n{"sediments":[],"state_updates":{}}'
ok(jsonloose.loads(think) == {"sediments": [], "state_updates": {}}, "剥思考块")

# ③ 对象切片(前后有噪声)
noisy = '垃圾前缀 {"name":"叶无道","role":"main"} 垃圾后缀 还有别的'
ok(jsonloose.loads(noisy) == {"name": "叶无道", "role": "main"}, "切片去前后噪声")

# 嵌套对象里有 } 不被提前截断
nested = 'x {"a":{"b":1},"c":[{"d":2}]} y'
ok(jsonloose.loads(nested) == {"a": {"b": 1}, "c": [{"d": 2}]}, "嵌套不提前截断")

# 字符串内的括号不干扰配平
instr = '{"text":"他说:{这是个陷阱}","n":1}'
ok(jsonloose.loads(instr) == {"text": "他说:{这是个陷阱}", "n": 1}, "字符串内括号不干扰")

# ④ 缺失闭合符(模型被 max_tokens 截断)
truncated = '{"sediments":[{"entity":"ye","text":"他守住了底线"'
r = jsonloose.loads(truncated)
ok(r.get("sediments") and r["sediments"][0]["entity"] == "ye", "截断缺闭合符可修复")

# 去尾逗号
trailing = '{"a":1,"b":2,}'
ok(jsonloose.loads(trailing) == {"a": 1, "b": 2}, "去尾逗号")

# ⑤ 列表顶层
ok(jsonloose.loads('结果:[1,2,3]') == [1, 2, 3], "顶层列表切片")

# 彻底无法解析 → default
ok(jsonloose.loads("完全没有 JSON 的一段话") == {}, "无 JSON 返回默认 {}")
ok(jsonloose.loads("nope", default={"fallback": True}) == {"fallback": True}, "自定义 default")
ok(jsonloose.loads(None) == {}, "None 返回默认")

# 真实场景:变量结算尾块(chat.py 用法)
varblock = '好感度涨了。\n{"好感度":"+5","HP":"-3"}'
ok(jsonloose.loads(varblock) == {"好感度": "+5", "HP": "-3"}, "变量结算尾块")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
