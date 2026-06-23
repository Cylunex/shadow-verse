"""数值面板模板测试 —— 轮回者多维「攻略式」状态卡:schema 自洽 + 护栏(clamp/step/enum/ro/wildcard关系)+ HUD 可见性。"""
from __future__ import annotations

import os
import sys
import tempfile
import types
from pathlib import Path

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_attr_")

from sv import attrs, varstate  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

panel = attrs.default_panel("楚瑶")
data, rules, meta = panel["data"], panel["rules"], panel["meta"]

# schema 自洽
ok(len(data) >= 20, f"维度够多({len(data)} 个顶层维度,要的就是厚)")
ok(all(k in meta for k in data), "每个数据维度都有 HUD 元数据(label/vis)")
cat_keys = [k for _, ks in attrs.CATEGORIES for k in ks]
ok(all(k in data for k in cat_keys), "类目目录里每个维度都在 data 里")
ok(meta["理智"]["vis"] == "bar" and meta["真实想法"]["vis"] == "hidden", "理智可见为bar、真实想法为隐藏维度")

# 护栏:数值 clamp + step 限幅
e = types.SimpleNamespace(dir=Path(tempfile.mkdtemp()))
attrs.apply_panel(e, "楚瑶")
st = varstate.load(e)
ok(st["data"]["体魄"] == 50 and st["rules"]["评级"]["enum"], "落库:data 补默认 + rules 带评级 enum")
varstate.apply_op(st["data"], "体魄", "+999", st["rules"])
ok(st["data"]["体魄"] == 60, "step 限幅:体魄 +999 被限到一步(+10)→60")
varstate.apply_op(st["data"], "理智", "-200", st["rules"])
ok(st["data"]["理智"] == 0, "clamp 托底:理智 -200 → 0(SAN 归零)")

# enum 护栏
n = varstate.apply_op(st["data"], "评级", "传说", st["rules"])
ok(st["data"]["评级"] == "D" and n, "enum 拒写:评级『传说』不在允许值,保持 D")
varstate.apply_op(st["data"], "评级", "A", st["rules"])
ok(st["data"]["评级"] == "A", "enum 合法值:评级 → A")

# ro 只读:轮回次数 引擎专属,模型写不动
varstate.apply_op(st["data"], "轮回次数", "+1", st["rules"])
ok(st["data"]["轮回次数"] == 0, "ro 护栏:轮回次数 模型/手动写不动")

# 与「你」的关系 = galgame 攻略板:多轴 + 阶段 + 称呼 + 隐藏
rel = st["data"]["关系"]["楚瑶"]
ok(len(attrs.REL_AXES) >= 9, f"关系维度厚({len(attrs.REL_AXES)} 轴:好感/心动/信任/依赖/亲密/默契/安全感/心防/占有欲)")
ok(all(a["key"] in rel for a in attrs.REL_AXES), "默认关系卡含全部攻略轴")
ok(rel["心防"] == 70 and rel["安全感"] == 30, "逆向轴心防起步高(70),安全感低(30)——攻略空间")
ok(rel["阶段"] == "陌生人" and rel["称呼"] == "楚瑶", "关系起步:陌生人 + 初始称呼")
ok(all(h in rel for h in attrs.REL_HIDDEN), "隐藏内在(真心话/隐藏期待/雷区)在数据里、高亲密才解锁")

# 通配关系规则:任意轴 clamp
varstate.apply_op(st["data"], "关系.楚瑶.好感", "+200", st["rules"])
ok(varstate.deep_get(st["data"], "关系.楚瑶.好感") == 100, "通配规则:关系.*.好感 +200 封顶到 100")
varstate.apply_op(st["data"], "关系.楚瑶.心动", "+45", st["rules"])
ok(varstate.deep_get(st["data"], "关系.楚瑶.心动") == 45, "新增轴心动随攻略上涨")
# 关系阶段是 enum:乱写拒绝
n = varstate.apply_op(st["data"], "关系.楚瑶.阶段", "结婚了", st["rules"])
ok(varstate.deep_get(st["data"], "关系.楚瑶.阶段") == "陌生人" and n, "阶段 enum 护栏:非阶梯值拒写")
varstate.apply_op(st["data"], "关系.楚瑶.阶段", "暧昧", st["rules"])
ok(varstate.deep_get(st["data"], "关系.楚瑶.阶段") == "暧昧", "阶段沿阶梯推进 → 暧昧")
varstate.apply_op(st["data"], "关系.沈昭.信任", "80", st["rules"])
ok(varstate.deep_get(st["data"], "关系.沈昭.信任") == 80, "新对象(队友)关系按通配规则建立并受限")

# HUD 可见性:隐藏维度不进面板
vis = {v["name"] for v in varstate.visible(st)}
ok("理智" in vis and "真实想法" not in vis and "执念" not in vis, "HUD:隐藏内在维度不进面板,生存状态进")

# 幂等:再 apply 不覆盖已变的值
varstate.save(e, st)                      # 先把上面改过的状态落盘
attrs.apply_panel(e, "楚瑶")
ok(varstate.load(e)["data"]["评级"] == "A", "apply_panel 幂等:不覆盖已变维度")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
