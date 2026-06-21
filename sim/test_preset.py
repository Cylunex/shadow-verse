"""ST 预设 + 正则脚本 导入测试 —— 采样集/有序模块/组装器 + 正则文本改写($1 反向引用/placement/depth)。"""
from __future__ import annotations

import json
import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_pre_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import importer  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# ---------- 预设 ----------
preset = {
    "temperature": 0.9, "top_p": 0.95, "min_p": 0.05, "seed": 42, "openai_max_tokens": 1200,
    "reasoning_effort": "high", "frequency_penalty": 0.2,
    "prompts": [
        {"identifier": "main", "name": "主提示", "role": "system", "content": "你是冷面叙事者。"},
        {"identifier": "charDescription", "name": "Char Description", "marker": True, "content": ""},
        {"identifier": "style", "name": "文风", "role": "system", "content": "克制、画面感。"},
        {"identifier": "off", "name": "禁用项", "role": "system", "content": "不该出现。"},
    ],
    "prompt_order": [{"character_id": 100001, "order": [
        {"identifier": "main", "enabled": True},
        {"identifier": "charDescription", "enabled": True},
        {"identifier": "style", "enabled": True},
        {"identifier": "off", "enabled": False},
    ]}],
}
pp = importer.parse_preset(preset, name="测试预设")
ok(pp["sampling"]["temperature"] == 0.9 and pp["sampling"]["max_tokens"] == 1200, "采样参数映射(含 max_tokens)")
ok(pp["sampling"]["seed"] == 42 and pp["sampling"]["reasoning_effort"] == "high", "seed/reasoning_effort 带过来")
ok(pp["order"] == ["main", "charDescription", "style"], "禁用项被剔除,顺序保留")
ok(pp["custom_count"] == 2, "自定义模块计数(main+style,marker 不算)")
ok(any(m["marker"] for m in pp["modules"]), "marker 占位模块保留")

# 持久化 + 列出 + 组装器
r = importer.import_preset(preset, name="测试预设")
ok(r["preset"] and importer.list_presets()[0]["name"] == "测试预设", "预设落盘 + 列出")
loaded = importer.load_preset(r["preset"])
asm = importer.assemble_preset(loaded, slots={"charDescription": "苏晴,插画师。"})
ok("你是冷面叙事者" in asm and "苏晴,插画师" in asm and "克制" in asm, "组装器按序拼接 + 填占位槽")
ok("不该出现" not in asm, "禁用模块不进组装")

# 坏格式拒绝
try:
    importer.parse_preset({"foo": 1}); ok(False, "非预设应报错")
except ValueError:
    ok(True, "非预设(缺 prompts)报错")

# ---------- 正则脚本 ----------
rx = {"scriptName": "状态面板", "findRegex": "/<状态>([\\s\\S]*?)<\\/状态>/g",
      "replaceString": "【面板:$1】", "placement": [1], "markdownOnly": True,
      "disabled": False, "trimStrings": [], "minDepth": None, "maxDepth": 5}
scripts = importer.parse_regex(rx)
ok(scripts[0]["name"] == "状态面板" and scripts[0]["placement"] == [1], "正则脚本解析")

# 文本改写:$1 反向引用 + 全局替换
out = importer.apply_regex("前<状态>HP:80</状态>中<状态>金币:5</状态>后", scripts, scope="output")
ok(out == "前【面板:HP:80】中【面板:金币:5】后", "g 全局替换 + $1 反向引用")

# placement 分流:scope=input 不套用 output 脚本
out2 = importer.apply_regex("<状态>X</状态>", scripts, scope="input")
ok(out2 == "<状态>X</状态>", "placement 分流:input 不套 output 脚本")

# depth 门控:depth 超过 maxDepth 不套用
out3 = importer.apply_regex("<状态>X</状态>", scripts, scope="output", depth=9)
ok(out3 == "<状态>X</状态>", "depth>maxDepth 不套用")
out4 = importer.apply_regex("<状态>X</状态>", scripts, scope="output", depth=2)
ok(out4 == "【面板:X】", "depth 在范围内套用")

# $$ 转义 + {{match}} 整体
rx2 = importer.parse_regex({"scriptName": "钱", "findRegex": "/\\d+元/g",
                            "replaceString": "$$[{{match}}]", "placement": [1]})
ok(importer.apply_regex("花了50元", rx2) == "花了$[50元]", "$$ 转义 + {{match}} 整体匹配")

# 持久化 + 汇总加载
importer.import_regex(rx, name="状态面板")
allscripts = importer.load_regex_scripts()
ok(len(allscripts) == 1 and allscripts[0]["name"] == "状态面板", "正则落盘 + 汇总加载")

# 数组形式 + 坏格式
arr = importer.parse_regex([rx, {"scriptName": "B", "findRegex": "/x/", "replaceString": "y", "placement": [1]}])
ok(len(arr) == 2, "数组形式多脚本解析")
try:
    importer.parse_regex({"foo": 1}); ok(False, "非正则应报错")
except ValueError:
    ok(True, "非正则(缺 findRegex)报错")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
