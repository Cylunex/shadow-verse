"""Run Event Journal 测试 —— seq 单调 / 落账 / 可重放 / narrate_run 接入。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_jr_")
os.environ["SV_LOCAL_CONF"] = tempfile.mktemp(suffix=".conf")   # 隔离本机已配 provider → stub
os.environ.pop("SV_PROVIDER", None)

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import journal, lenses  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

w = World.create("w", "W", genre="玄幻")
LocalEntity.create(w, "hero", "主角", role="main")
t = Thread.create(w, "line", "线", genre="玄幻")

# 基础 journal
jr = journal.open_run(t, run_id="run-x")
e1 = jr.append("start", intent="开篇")
e2 = jr.append("draft", hanzi=1200)
ok(e1["seq"] == 1 and e2["seq"] == 2, "seq 单调递增")
ok(e2["kind"] == "draft" and e2["hanzi"] == 1200, "事件落数据")
ok(len(jr.events()) == 2 and jr.last_seq() == 2, "可重放读全部事件")
s = jr.summary()
ok(s["events"] == 2 and s["kinds"]["draft"] == 1, "summary 统计 kinds")

# narrate_run 接入(stub LLM:走占位草稿+落章)
trace = lenses.narrate_run(w, t, intent="第一章")
ok("run_id" in trace, "narrate_run 返回 run_id")
jr2 = journal.open_run(t, run_id=trace["run_id"])
kinds = [e["kind"] for e in jr2.events()]
ok("start" in kinds and "draft" in kinds and "finish" in kinds, "产线落账 start/draft/finish")
ok("commit" in kinds, "落章事件入账")
ok(jr2.events()[-1]["kind"] == "finish", "末事件是 finish")
ok(trace["run_id"] in journal.list_runs(t), "run 可被列出")
# seq 全程单调
seqs = [e["seq"] for e in jr2.events()]
ok(seqs == sorted(seqs) and seqs[0] == 1, "全程 seq 单调从 1")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
