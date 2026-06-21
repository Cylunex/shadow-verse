"""模式注册表 + 数据互通 测试。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_md_")
os.environ["SV_LOCAL_CONF"] = tempfile.mktemp(suffix=".conf")
os.environ.pop("SV_PROVIDER", None)

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import convert, modes  # noqa: E402
from sv.config import append_jsonl  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# ---- 模式注册表 ----
ml = modes.list_modes()
ok(len(ml) >= 11, "至少 11 个模式注册")
ids = {m["id"] for m in ml}
ok({"tavern-rp", "novel", "cyoa", "screenplay", "comic", "tabletop", "dream"} <= ids, "核心+支柱模式齐全")
ok(len(modes.list_modes("core")) == 3, "三大核心模式")
ok(all(m["lens"] in ("narrate", "play", "simulate", "render", "chat") for m in ml), "每模式复用一个透镜")

# mode_pack(提示模板包)
mp = modes.mode_pack("tabletop", genre="玄幻")
ok(mp["mode"] == "tabletop" and mp["lens"] == "play", "mode_pack:跑团基于 play 透镜")
ok("roll" in mp["output_format"] and mp["recipe"], "mode_pack 带输出格式+题材配方")
mp2 = modes.mode_pack("novel", genre="科幻")
ok(mp2["craft"] and mp2["lens"] == "narrate", "小说模式带写作 craft")
try:
    modes.mode_pack("不存在"); ok(False, "未知模式应报错")
except ValueError:
    ok(True, "未知模式报错")

# ---- 数据互通 ----
w = World.create("w", "W", genre="玄幻")
e = LocalEntity.create(w, "hero", "叶无道", role="main")
# 造对话
append_jsonl(e.dir / "chat.jsonl", {"role": "user", "text": "你要去哪?", "ts": clock.now_iso()})
append_jsonl(e.dir / "chat.jsonl", {"role": "char", "text": "去会会那个人。", "ts": clock.now_iso()})

# chat → 小说
pk = convert.chat_to(w, e, "novel")
ok(pk["from"] == "chat" and pk["to"] == "novel", "chat→novel 转换包")
ok("叶无道:去会会" in pk["material"] and "改写成第三人称小说" in pk["guide"], "转换包含源材料+指引")
ok(pk["target"]["output_format"], "转换包带目标模式格式")

# chat → cyoa
pk2 = convert.chat_to(w, e, "cyoa")
ok(pk2["to"] == "cyoa" and "选项" in pk2["guide"], "chat→cyoa 指引含选项")

# 小说章 → cyoa / screenplay
t = Thread.create(w, "line", "测试线", genre="玄幻")
t.add_chapter("叶无道站在崖边,身后是追兵,身前是深渊。", "抉择")
ck = convert.chapter_to(w, t, 1, "cyoa")
ok(ck["from"] == "novel" and "抉择点" in ck["guide"], "novel→cyoa 转换包")
sk = convert.chapter_to(w, t, 1, "screenplay")
ok(sk["to"] == "screenplay" and "剧本格式" in sk["guide"], "novel→screenplay 转换包")

# beats → 剧本 / 跑团
t.add_beat("初遇对手", lens="narrate", where="ch:001")
t.add_beat("大战三百回合", lens="play", where="play:s1")
bk = convert.beats_to(w, t, "tabletop")
ok(bk["from"] == "beats" and "战役日志" in bk["guide"], "beats→跑团战役日志")
ok("初遇对手" in bk["material"] and "大战" in bk["material"], "beats 源材料汇总")

# 无 LLM 时 run 给提示
ok(convert.run(pk).get("available") is False, "无 LLM:一键转换给提示")

# CYOA 选项解析(文本兜底)
choices = convert.cyoa_choices("场景描述。\n1. 跳下深渊\n2. 转身迎敌\n3. 谈判")
ok(len(choices) == 3 and choices[0]["label"] == "跳下深渊", "CYOA 选项文本解析")

if os.path.exists(os.environ["SV_LOCAL_CONF"]):
    os.remove(os.environ["SV_LOCAL_CONF"])

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
