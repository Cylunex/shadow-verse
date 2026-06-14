"""实时对话测试 —— stub 引导、人设组装、历史落盘、清空。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_chat_")
os.environ["SV_LOCAL_CONF"] = tempfile.mktemp(suffix=".conf")
for k in ("SV_PROVIDER",):
    os.environ.pop(k, None)

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import chat, config, llm  # noqa: E402
from sv.config import save_json  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

w = World.create("w", "W", genre="都市")
e = LocalEntity.create(w, "su", "苏晴", role="main", body="# 苏晴\n## 核心事实\n- 外冷内热\n- 不伤无辜")

# 默认 stub:不真聊,给引导,不落历史
r = chat.turn(w, e, "在吗")
ok(r["available"] is False and "设置" in r["reply"], "stub 时引导去配 LLM")
ok(chat.history(e) == [], "stub 不落对话历史")

# 开场白
ok(chat.greeting(e), "有开场白(无 first_mes 时给默认)")
e2 = LocalEntity.create(w, "ye", "叶无道", role="main")
card = e2.card(); card["greeting"] = "谁?"; save_json(e2.card_path, card)
ok(chat.greeting(e2) == "谁?", "card.greeting 作开场白")

# 人设组装含档案 + anchors(不打网络)
sysp = chat._persona(w, e)
ok("苏晴" in sysp and "外冷内热" in sysp and "不伤无辜" in sysp, "人设含名字/档案/底线 anchors")
ok("第一人称" in sysp and "不报" not in sysp[:0] and "AI" in sysp, "人设要求第一人称扮演、不跳戏")

# 配 openai+假key → available 翻 True(真聊只差真 key;不在测试里打网络)
config.save_setting({"SV_PROVIDER": "openai", "OPENAI_API_KEY": "sk-fake"})
ok(llm.available() is True, "配 provider 后 available()=True(真 key 即可对话)")
config.save_setting({"SV_PROVIDER": ""})  # 回 stub 免误打网络

# 历史落盘(直接喂一条 char/user 记录验证读写)
from sv.config import append_jsonl  # noqa: E402
append_jsonl(e.dir / "chat.jsonl", {"role": "user", "text": "嗨", "ts": clock.now_iso()})
append_jsonl(e.dir / "chat.jsonl", {"role": "char", "text": "啧。", "ts": clock.now_iso()})
ok(len(chat.history(e)) == 2 and chat.history(e, 1)[0]["text"] == "啧。", "对话历史读写 + 窗口")
chat.clear(e)
ok(chat.history(e) == [], "清空对话")

if os.path.exists(os.environ["SV_LOCAL_CONF"]):
    os.remove(os.environ["SV_LOCAL_CONF"])

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
