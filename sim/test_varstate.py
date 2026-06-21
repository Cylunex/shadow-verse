"""变量三段式引擎测试 —— 深路径 / 五 op / validate 护栏(clamp/step/ro/enum)/ 可见性 / 迁移。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_vs_")

from sv import clock, varstate  # noqa: E402

clock.use_virtual()

from sv import chat  # noqa: E402
from sv.config import save_json  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# ---- 深路径 ----
d = {}
varstate.deep_set(d, "关系.张三.好感", 30)
ok(varstate.deep_get(d, "关系.张三.好感") == 30, "深路径 set/get(自动建中间层)")
varstate.deep_set(d, "背包[0]", "匕首")
varstate.deep_set(d, "背包[1]", "绷带")
ok(varstate.deep_get(d, "背包[1]") == "绷带", "数组下标 set/get")
varstate.deep_del(d, "关系.张三.好感")
ok(varstate.deep_get(d, "关系.张三.好感") is None, "深路径 del")

# ---- 五 op + 护栏 ----
data = {"HP": 80, "金币": 5, "背包": ["匕首"], "等级": 3}
rules = {"HP": {"min": 0, "max": 100, "step": 20}, "金币": {"min": 0}, "等级": {"ro": True},
         "态度": {"enum": ["友好", "警惕", "敌对"]}}
ok(varstate.apply_op(data, "HP", "+10", rules) is None and data["HP"] == 90, "inc 数值增量")
n = varstate.apply_op(data, "HP", "+50", rules)
ok(data["HP"] == 100 and n, "step 限幅 + max 封顶(+50→step20→100)")
varstate.apply_op(data, "金币", "-99", rules)
ok(data["金币"] == 0, "min 托底(金币不为负)")
ok(varstate.apply_op(data, "等级", "+1", rules) and data["等级"] == 3, "ro 只读拒写")
ok(varstate.apply_op(data, "态度", "暧昧", rules) and "态度" not in data, "enum 不匹配拒写")
ok(varstate.apply_op(data, "态度", "警惕", rules) is None and data["态度"] == "警惕", "enum 匹配通过")
varstate.apply_op(data, "背包", "+绷带", rules)
ok(data["背包"] == ["匕首", "绷带"], "数组 push(+x)")
varstate.apply_op(data, "背包", "-匕首", rules)
ok(data["背包"] == ["绷带"], "数组 pop(-x)")
varstate.apply_op(data, "心情", "平静", rules)
ok(data["心情"] == "平静", "set 新字符串变量")
varstate.apply_op(data, "心情", None, rules)
ok("心情" not in data, "del(spec=None)")

# 通配规则
data2 = {"关系": {"张三": {"好感": 50}}}
rules2 = {"关系.*.好感": {"min": -100, "max": 100}}
varstate.apply_op(data2, "关系.张三.好感", "+80", rules2)
ok(varstate.deep_get(data2, "关系.张三.好感") == 100, "通配规则 `关系.*.好感` clamp 生效")

# replay(swipe 回滚)
base = {"HP": 50}
d3, _ = varstate.replay(base, {"HP": "+10"}, {"HP": {"max": 100}})
ok(d3["HP"] == 60 and base["HP"] == 50, "replay 从基线深拷贝不污染原基线")

# 可见性
state = {"data": {"HP": 80, "内心好感": 99, "背包": ["刀"]},
         "rules": {"HP": {"min": 0, "max": 100}},
         "meta": {"HP": {"label": "生命", "vis": "bar"}, "内心好感": {"vis": "hidden"}}}
vis = varstate.visible(state)
names = [x["name"] for x in vis]
ok("HP" in names and "内心好感" not in names, "hidden 变量不进 HUD")
hp = next(x for x in vis if x["name"] == "HP")
ok(hp["vis"] == "bar" and hp["max"] == 100 and hp["label"] == "生命", "HUD 渲染提示(vis/min/max/label)")
bag = next(x for x in vis if x["name"] == "背包")
ok(bag["vis"] == "list", "数组默认 vis=list")

# ---- 与 chat 集成 + 旧扁平迁移 ----
w = World.create("w", "W", genre="都市")
e = LocalEntity.create(w, "su", "苏晴", role="main")
# 旧扁平 vars.json
save_json(e.dir / "vars.json", {"好感度": 12})
ok(chat.vars(e) == {"好感度": 12}, "旧扁平 vars.json 迁移后 data 视图不变")
chat.set_var(e, "好感度", "+5")
ok(chat.vars(e)["好感度"] == 17, "迁移后 set_var 仍工作")
st = chat.var_state(e)
ok("data" in st and "rules" in st and "meta" in st, "存成三段式")
# AI 建卡式落 rules+meta
chat.set_rules_meta(e, rules={"HP": {"min": 0, "max": 100}}, meta={"HP": {"vis": "bar"}},
                    data={"好感度": 17, "HP": 100})
chat.set_var(e, "HP", "-999")
ok(chat.vars(e)["HP"] == 0, "建卡后的 rules 对后续结算生效(HP 托底)")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
