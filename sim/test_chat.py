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
sysp = chat._system(w, e, chat.player(), {})
ok("苏晴" in sysp and "外冷内热" in sysp and "不伤无辜" in sysp, "人设含名字/档案/底线 anchors")
ok("第一人称" in sysp and "AI" in sysp, "人设要求第一人称扮演、不跳戏")

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

# 头像
e.set_avatar(b"\x89PNG\r\n\x1a\nfake-but-bytes", "png")
ok(e.avatar_rel() == "worlds/w/entities/su/avatar.png", "头像相对路径")
e.set_avatar(b"jpegbytes", "jpg")
ok(e.avatar_rel().endswith("avatar.jpg") and not (e.dir / "avatar.png").exists(), "换头像覆盖旧的")

# 重 roll / 撤回(确定性假 LLM)
import sv.chat as C  # noqa: E402
_av, _gen = C.llm.available, C.llm.generate
seq = {"n": 0}
C.llm.available = lambda: True
def _fake(system, user, **kw):
    seq["n"] += 1; return f"回复{seq['n']}"
C.llm.generate = _fake
try:
    chat.turn(w, e, "在吗")
    h = chat.history(e)
    ok(len(h) == 2 and h[1]["text"] == "回复1", "turn 落 user+char")
    rg = chat.regenerate(w, e)
    h2 = chat.history(e)
    ok(rg["reply"] == "回复2" and len(h2) == 2 and h2[1]["text"] == "回复2" and h2[0]["text"] == "在吗",
       "重 roll 换回复、保留用户消息、不新增轮")
    chat.turn(w, e, "第二句")
    ok(len(chat.history(e)) == 4, "第二轮落盘")
    u = chat.undo_last(e)
    ok(u["remaining"] == 2 and len(chat.history(e)) == 2, "撤回删掉最后一轮")
finally:
    C.llm.available, C.llm.generate = _av, _gen

# 玩家身份(治身份漂移)
ok(chat.player()["name"] == "你", "默认玩家身份")
chat.set_player("阿哲", "苏晴的发小")
ok(chat.player() == {"name": "阿哲", "persona": "苏晴的发小"}, "设玩家身份持久化")
sysp = chat._system(w, e, chat.player(), {})
ok("阿哲" in sysp and "绝不替阿哲说话" in sysp, "系统提示含玩家名 + 不替玩家说话铁律")

# 变量系统
ok(chat.vars(e) == {}, "初始无变量")
chat.set_var(e, "好感度", 10)
ok(chat.vars(e)["好感度"] == 10, "设数值变量")
chat.set_var(e, "好感度", "+5")
ok(chat.vars(e)["好感度"] == 15, "+N 增量")
chat.set_var(e, "好感度", "-3")
ok(chat.vars(e)["好感度"] == 12, "-N 减量")
chat.set_var(e, "心情", "温柔")
ok(chat.vars(e)["心情"] == "温柔", "字符串变量")
chat.del_var(e, "心情")
ok("心情" not in chat.vars(e), "删变量")

# 模型在回复尾部下变量块 → 解析+结算,正文剥干净
_av2, _gen2 = C.llm.available, C.llm.generate
C.llm.available = lambda: True
C.llm.generate = lambda system, user, **kw: '啧,又来了。\n===变量===\n{"好感度":"+5","金钱":"100"}'
try:
    chat.clear(e)
    r = chat.turn(w, e, "我来看你了")
    ok(r["reply"] == "啧,又来了。" and "===" not in r["reply"], "变量块从正文剥离")
    ok(r["vars"]["好感度"] == 17 and r["vars"]["金钱"] == 100, "模型变量块结算(增量+新值)")
    ok(set(r["var_changed"]) == {"好感度", "金钱"}, "var_changed 报告改了哪些")
finally:
    C.llm.available, C.llm.generate = _av2, _gen2

if os.path.exists(os.environ["SV_LOCAL_CONF"]):
    os.remove(os.environ["SV_LOCAL_CONF"])

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
