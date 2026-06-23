"""P2 测试 —— RP 接入 substrate:每轮 RP 落到【世界线】(thread.beats),门控 SV_RP_COMMIT,关时字节等价。

不放弃世界线:你聊的内容进入世界的时间轴,RP 不再是离线孤岛。
"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_rp_")
os.environ["SV_LOCAL_CONF"] = tempfile.mktemp(suffix=".conf")
os.environ.pop("SV_PROVIDER", None)

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import chat, config  # noqa: E402
from sv.config import load_json  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

w = World.create("tower", "无限之塔", genre="无限流")
e = LocalEntity.create(w, "chuyao", "楚瑶", role="main", body="# 楚瑶\n## 核心事实\n- 不抛下队友\n")

# 确定性假 LLM
chat.llm.available = lambda: True
chat.llm.generate = lambda s, u, **k: "我在,别怕。"

# RP_COMMIT 关(默认):不落世界线,行为同今天
config.RP_COMMIT = False
chat.clear(e)
chat.turn(w, e, "在吗")
ok(not Thread(w, "rp-chuyao").exists(), "RP_COMMIT 关:不建世界线 thread,字节等价旧逻辑")
ok(len(chat.history(e)) == 2, "RP_COMMIT 关:对话历史照常(user+char)")

# RP_COMMIT 开:RP 一轮落世界线
config.RP_COMMIT = True
try:
    chat.turn(w, e, "你还好吗")
    t = Thread(w, "rp-chuyao")
    ok(t.exists(), "RP_COMMIT 开:自动建/绑世界线 rp-<eid>(落在世界 threads/ 下)")
    bts = t.beats()
    ok(bts and bts[-1]["lens"] == "play" and bts[-1]["where"] == "play:rp-chuyao",
       "RP 一轮落到世界线 beats(lens=play)——进入世界时间轴")
    ok("play" in t.meta().get("lenses", []), "世界线标记 play 透镜")
    ok(load_json(chat._meta_path(e), {}).get("thread_id") == "rp-chuyao", "chat_meta 记下世界线 thread_id")
    n0 = len(t.beats())
    chat.turn(w, e, "再聊聊")
    ok(len(t.beats()) == n0 + 1, "复用同一条世界线累积事件,不每轮新建")
finally:
    config.RP_COMMIT = False

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
