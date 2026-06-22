"""记忆核心循环测试 —— 铁律 rebuild≠retrieve + 沉淀门控 + 检索打分。"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_mem_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import memory  # noqa: E402
from sv.config import RECENT_EXP_REBUILD  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

w = World.create("w", "W", genre="都市")
e = LocalEntity.create(w, "e", "E", role="main")

# 追加 + 只追加
for i in range(8):
    clock.advance(hours=1)
    memory.append_experience(e.dir, f"经历{i}", level="持久", where=f"ch:{i}")
allx = memory.all_experiences(e.dir)
ok(len(allx) == 8, "只追加:8 条全在")
ok(all(x["id"].startswith("exp-") for x in allx) and len({x["id"] for x in allx}) == len(allx),
   "经历每条都带唯一 id(uuid 后缀:免并发追加重复)")

# ① rebuild:确定性、范围小
e.update_state({"location": "茶馆", "mood": "平静"})
rb = e.rebuild()
ok(rb["state"]["location"] == "茶馆", "rebuild 拿到此刻状态")
ok(len(rb["recent"]) == RECENT_EXP_REBUILD, f"rebuild 近期经历限 {RECENT_EXP_REBUILD} 条(范围小)")
ok("anchors" in rb, "rebuild 带 anchors 槽")

# ② retrieve:加权、全历史,相关度主导
memory.append_experience(e.dir, "在码头查到了走私线索", level="持久", where="ch:9", tags=["走私", "码头"])
memory.append_experience(e.dir, "今天天气不错喝了茶", level="瞬时", where="ch:10")
ret = memory.retrieve(e.dir, "走私 码头")
ok(ret and "走私" in ret[0]["text"], "retrieve 相关度命中并排第一")
ok(len(memory.read_jsonl(e.dir / "experiences.jsonl")) == 10, "retrieve 不改动历史(仍 10 条)")

# 相关度 > 重要度:一个无关的'身份'级不该挤掉相关的'持久'级
memory.append_experience(e.dir, "完全无关的身份大事", level="身份", where="ch:11")
ret2 = memory.retrieve(e.dir, "走私 码头")
ok(ret2[0]["text"].find("走私") >= 0, "相关度主导:无关身份级不挤掉相关项")

# 状态合并(只覆盖给到的键)
e.update_state({"mood": "警觉"})
ok(memory.read_state(e.dir)["location"] == "茶馆", "状态合并更新:未给的键保留")

# 沉淀门控:cameo 不写回
cam = LocalEntity.create(w, "cam", "客", role="cameo")
ok(cam.sediment("客串经历") is None, "cameo 沉淀返回 None(门控)")
ok(len(memory.all_experiences(cam.dir)) == 0, "cameo 经历未落盘")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
