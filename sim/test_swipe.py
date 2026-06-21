"""swipe(一楼多候选)+ 变量可回滚 + 任意楼重生成 测试。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_swipe_")
os.environ["SV_LOCAL_CONF"] = tempfile.mktemp(suffix=".conf")
os.environ.pop("SV_PROVIDER", None)

from sv import clock  # noqa: E402

clock.use_virtual()

import sv.chat as C  # noqa: E402
from sv import chat  # noqa: E402
from sv.config import append_jsonl  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

w = World.create("w", "W", genre="都市")
e = LocalEntity.create(w, "su", "苏晴", role="main", body="# 苏晴\n## 核心事实\n- 外冷内热")

# 假 LLM:回复带递增编号 + 每次给一个变量增量
_av, _gen = C.llm.available, C.llm.generate
seq = {"n": 0}
C.llm.available = lambda: True
def _fake(system, user, **kw):
    seq["n"] += 1
    return f"回复{seq['n']}\n===变量===\n{{\"好感\":\"+{seq['n']}\"}}"
C.llm.generate = _fake
try:
    # 首轮:turn 写成 swipe 形态
    r = chat.turn(w, e, "在吗")
    h = chat.history(e)
    ok(len(h) == 2 and h[1]["role"] == "char", "turn 落 user+char")
    ok(h[1].get("swipes") == ["回复1"] and h[1]["swipe_id"] == 0, "char 楼是 swipe 形态")
    ok("vars_before" in h[1] and h[1]["vars_before"] == {}, "char 楼记了楼前基线")
    ok(r["reply"] == "回复1" and r["vars"]["好感"] == 1 and r["swipe_n"] == 1, "首候选+变量+1")

    # swipe_add:追加第二候选,变量从基线重放(好感应是 0+2=2,不是 1+2)
    r2 = chat.swipe_add(w, e)
    h = chat.history(e)
    ok(len(h) == 2, "swipe_add 不新增楼(同一 char 楼)")
    ok(h[1]["swipes"] == ["回复1", "回复2"] and h[1]["swipe_id"] == 1, "追加候选并切到新候选")
    ok(r2["reply"] == "回复2" and r2["swipe_n"] == 2, "第二候选")
    ok(chat.vars(e)["好感"] == 2, "变量从楼前基线重放(好感=2,非 1+2=3)")

    # swipe_select 切回候选0:变量回滚到该候选(好感=0+1=1)
    r3 = chat.swipe_select(e, 0)
    ok(r3["reply"] == "回复1" and chat.history(e)[1]["text"] == "回复1", "切回候选0,text 同步")
    ok(chat.vars(e)["好感"] == 1, "切候选→变量回滚(好感=1,不越加)")

    # 再切到候选1:好感回到 2
    chat.swipe_select(e, 1)
    ok(chat.vars(e)["好感"] == 2, "来回切候选变量始终一致")

    # swipe_next 右滑到末尾→自动生成新候选
    r4 = chat.swipe_next(w, e, 1)
    ok(r4["swipe_n"] == 3 and chat.history(e)[1]["swipe_id"] == 2, "右滑到末尾自动生成新候选")

    # regenerate 升级为 swipe_add(追加,不覆盖,旧候选还在)
    n_before = len(chat.history(e)[1]["swipes"])
    rg = chat.regenerate(w, e)
    ok(len(chat.history(e)[1]["swipes"]) == n_before + 1, "regenerate=追加候选(不覆盖)")
    ok(len(chat.history(e)) == 2, "regenerate 不新增楼")

    # 第二轮对话
    vars_at_turn2 = dict(chat.vars(e))
    chat.turn(w, e, "第二句")
    ok(len(chat.history(e)) == 4, "第二轮落盘 user+char")
    base2 = chat.history(e)[3]["vars_before"]
    ok(base2 == vars_at_turn2, "第二楼基线=第一楼结算后的 vars")

    # floor_regenerate:从第 0 楼(user"在吗")重生成 → 截断后续,变量回滚到最初
    seq["n"] = 100
    rf = chat.floor_regenerate(w, e, 0)
    h = chat.history(e)
    ok(len(h) == 2 and h[1]["text"] == "回复101", "任意楼重生成:截断到该楼+重生成")
    ok(chat.vars(e)["好感"] == 101, "floor_regenerate 变量回滚到截断前基线(0)再重放(+101)")
finally:
    C.llm.available, C.llm.generate = _av, _gen

# 旧格式 char 行(无 swipes)lazy 升级不崩
chat.clear(e)
append_jsonl(e.dir / "chat.jsonl", {"role": "user", "text": "嗨", "ts": clock.now_iso()})
append_jsonl(e.dir / "chat.jsonl", {"role": "char", "text": "啧。", "ts": clock.now_iso()})
hh = chat.history(e)
ok(hh[1]["swipes"] == ["啧。"] and hh[1]["swipe_id"] == 0, "旧 char 行 lazy 升级为 swipe 形态")

if os.path.exists(os.environ["SV_LOCAL_CONF"]):
    os.remove(os.environ["SV_LOCAL_CONF"])

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
