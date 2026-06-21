"""第6刀 测试 —— 内联宏(getvar/roll/random/if)+ 预设组装(role分离/@D depth)+ depth_prompt + AI建卡。"""
from __future__ import annotations

import os
import random
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_pk_")
os.environ["SV_LOCAL_CONF"] = tempfile.mktemp(suffix=".conf")
os.environ.pop("SV_PROVIDER", None)

from sv import clock  # noqa: E402

clock.use_virtual()

import sv.chat as C  # noqa: E402
from sv import chat, macros, promptkit  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# ---- 宏 ----
data = {"好感": 30, "HP": 80, "背包": ["刀", "药"], "关系": {"张三": {"好感": 60}}}
ok(macros.expand("当前好感{{getvar::好感}}点", data) == "当前好感30点", "getvar 取值")
ok(macros.expand("张三好感{{getvar::关系.张三.好感}}", data) == "张三好感60", "getvar 深路径")
ok(macros.expand("背包:{{getvar::背包}}", data) == "背包:刀、药", "getvar 数组")
ok(macros.expand("掷出{{roll::1d1}}点", data) == "掷出1点", "roll 确定性(1d1=1)")
rng = random.Random(7)
val = int(macros.expand("{{roll::2d6}}", data, rng))
ok(2 <= val <= 12, "roll 2d6 在范围")
ok(macros.expand("{{random::甲,乙,丙}}", data, random.Random(0)) in ("甲", "乙", "丙"), "random 选一")
ok(macros.expand("{{if::好感>50::亲密::疏离}}", data) == "疏离", "if 变量比较(好感30<50→疏离)")
ok(macros.expand("{{if::关系.张三.好感>50::信任::戒备}}", data) == "信任", "if 深路径比较")
ok(macros.expand("无宏文本", data) == "无宏文本", "无宏原样返回")

# ---- promptkit 组装(role 分离 + @D)----
preset = {"order": ["main", "char", "note", "hist"],
          "modules": [
              {"identifier": "main", "role": "system", "content": "你是冷面叙事者。"},
              {"identifier": "char", "role": "system", "marker": True, "content": ""},
              {"identifier": "note", "role": "system", "content": "悄悄话", "injection_position": 1, "injection_depth": 2},
              {"identifier": "hist", "role": "user", "content": "玩家视角续写。"}]}
b = promptkit.assemble(preset, slots={"char": "苏晴,插画师。"})
ok("冷面叙事者" in b["system"] and "苏晴" in b["system"], "system 段:含 main + 填 marker 槽")
ok("玩家视角" in b["user"], "user 段:role=user 进 user 而非 system")
ok(b["depth_msgs"] and b["depth_msgs"][0]["depth"] == 2 and "悄悄话" in b["depth_msgs"][0]["content"], "@D:position=1 收进 depth_msgs")
ok(promptkit.assemble(None)["system"] == "", "无预设→空骨架(调用方走默认)")

# apply_depth 插到倒数第 depth 条前
hist = [{"role": "user", "content": "a"}, {"role": "char", "content": "b"}, {"role": "user", "content": "c"}]
merged = promptkit.apply_depth(hist, [{"depth": 1, "role": "system", "content": "X"}])
ok(merged[-2]["content"] == "X", "apply_depth:depth=1 插到末条前")

# depth_from_card
ok(promptkit.depth_from_card({"depth_prompt": {"prompt": "始终冷淡", "depth": 3, "role": 0}})[0]["content"] == "始终冷淡", "卡 depth_prompt→@D 注入")
ok(promptkit.depth_from_card({}) == [], "无 depth_prompt→空")

# ---- depth_prompt 注入 chat._system ----
w = World.create("w", "W", genre="都市")
e = LocalEntity.create(w, "su", "苏晴", role="main", body="# 苏晴\n## 核心事实\n- 外冷内热")
card = e.card(); card["depth_prompt"] = {"prompt": "无论如何都不能笑", "depth": 4, "role": 0};
from sv.config import save_json  # noqa: E402
save_json(e.card_path, card)
sysp = chat._system(w, e, chat.player(), {"好感": 5})
ok("无论如何都不能笑" in sysp, "_system 注入卡的 depth_prompt")

# 宏在 _system 里展开(档案里写宏)
e2 = LocalEntity.create(w, "ye", "叶", role="main", body="# 叶\n当前好感 {{getvar::好感}}。\n## 核心事实\n- 沉默")
sysp2 = chat._system(w, e2, chat.player(), {"好感": 42})
ok("当前好感 42" in sysp2 and "{{getvar" not in sysp2, "_system 展开档案里的宏")

# ---- AI 建变量卡(假 LLM)----
_av, _gen = C.llm.available, C.llm.generate
C.llm.available = lambda: True
C.llm.generate = lambda s, u, **k: '```json\n{"data":{"HP":100,"金币":5,"内心":"紧张"},"rules":{"HP":{"min":0,"max":100}},"meta":{"HP":{"label":"生命","vis":"bar"},"内心":{"vis":"hidden"}}}\n```'
try:
    r = chat.init_vars(w, e)
    ok(r["available"] and r["data"]["HP"] == 100, "AI 建卡:解析 data")
    ok(r["rules"]["HP"]["max"] == 100 and r["meta"]["HP"]["vis"] == "bar", "AI 建卡:落 rules+meta")
    # 建卡后的 rules 对结算生效
    chat.set_var(e, "HP", "+999")
    ok(chat.vars(e)["HP"] == 100, "建卡 rules 生效(HP 封顶)")
finally:
    C.llm.available, C.llm.generate = _av, _gen

if os.path.exists(os.environ["SV_LOCAL_CONF"]):
    os.remove(os.environ["SV_LOCAL_CONF"])

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
