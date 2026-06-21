"""线分支测试 —— 从某章分叉 / 共享母线前 N 章 / 蝴蝶效应 divergence / Scene-Beat 图。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_br_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import branch  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

w = World.create("w", "W", genre="玄幻")
t = Thread.create(w, "line", "母线", genre="玄幻")
for i in range(1, 6):
    t.add_chapter(f"母线第{i}章:主角选择了正道。", f"{i}")

# 从第 3 章分叉
b = branch.Branch.create(t, 3, name="魔道线", divergence="主角本该入正道,这里改为堕入魔道")
ok(b.exists() and b.meta()["from_chapter"] == 3, "分支建立(从第3章)")
ok(branch.list_branches(t)[0]["id"] == b.bid, "分支进 index")

# 前 3 章共享母线
ok("母线第2章" in b.chapter_text(2), "分支共享母线前 N 章(ch2 读母线)")
# 分叉后写自己的
no = b.add_chapter("魔道线第4章:主角杀伐果断。", "堕落")
ok(no == 4 and "魔道" in b.chapter_text(4), "分叉后写分支自己的章(ch4)")
ok("母线第4章" not in b.chapter_text(4), "分支 ch4 不是母线内容")
ok(b.last_chapter_no() == 4, "分支最新章号")
# 母线不受影响
ok("正道" in t.chapter_text(4), "母线 ch4 不受分支影响")

# 蝴蝶效应 divergence
divs = b.divergences()
ok(len(divs) == 1 and "魔道" in divs[0]["summary"], "建分支时记了首个偏离点")
b.add_divergence("拒绝师门召回", chapter=4, original="回宗门请罪", actual="灭了宗门",
                 ripple=["与同门反目", "被通缉"])
ok(len(b.divergences()) == 2, "追加偏离点")
d2 = b.divergences()[1]
ok(d2["ripple_effects"] == ["与同门反目", "被通缉"] and d2["original"] == "回宗门请罪", "偏离点含原走向+涟漪")

# 第二条分支
b2 = branch.Branch.create(t, 2, name="退隐线")
ok(len(branch.list_branches(t)) == 2, "两条分支并存")

# 删分支
b2.delete()
ok(len(branch.list_branches(t)) == 1 and not b2.exists(), "删分支:目录+index 同步")

# Scene/Beat 图
bt = branch.beat("b1", "你推开门。", nxt={"type": "choice", "choices": [
    branch.choice("进去", effect="advance-beat", target="b2"),
    branch.choice("离开", effect="change-scene", target="街道"),
]})
ok(bt["next"]["type"] == "choice" and len(bt["next"]["choices"]) == 2, "Beat 节点带 choice 边")
ok(bt["next"]["choices"][1]["effect"] == "change-scene", "choice 带 change-scene 分叉效果")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
