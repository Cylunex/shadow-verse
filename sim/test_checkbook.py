"""全书级 stylestat 测试 —— 句式 tic 章均 / 跨章逐字复读 / 章末短结尾 / 开篇时间词 / 标题问题。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_cb_")

from sv import checks, clock  # noqa: E402

clock.use_virtual()

from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

w = World.create("w", "W", genre="玄幻")
t = Thread.create(w, "line", "测试线", genre="玄幻")

# 样本不足(<3 章)不出基线
t.add_chapter("夜里很静。他推门出去。", "起")
b0 = checks.check_book(t)
ok(b0["chapters"] == 1 and any("样本不足" in f for f in b0["findings"]), "章数<3 跳过基线")

# 构造 5 章:每章开篇时间词 + 章末短结尾 + 同一句逐字复读 + 句式 tic
REPEAT = "他握紧了腰间那柄旧剑没有说话。"   # ≥8 汉字,放进多章
for i in range(2, 7):
    body = (
        f"清晨，山风掠过崖壁。"                       # 开篇时间词
        f"那不是风声而是某种低语，像潮水一般涌来。"      # tic: 不是…而是… + 明喻
        f"{REPEAT}"                                  # 跨章逐字复读
        f"他沉默了。"                                  # tic: 沉默节拍 + 短结尾
    )
    t.add_chapter(body, f"第{i}页")

b = checks.check_book(t)
ok(b["chapters"] == 6, "统计全部 6 章")
ok(b["time_opener_rate"] >= 0.4 and any("开篇时间词" in f for f in b["findings"]), "开篇时间词率检出")
ok(b["short_ending_rate"] >= 0.5 and any("短结尾" in f for f in b["findings"]), "章末短结尾率检出")
ok(b["cross_repeats"] and any("逐字复读" in f for f in b["findings"]), "跨章逐字复读句检出")
ok(any("tic" in f for f in b["findings"]), "句式 tic 章均检出")

# last_n 只看近 N 章
b3 = checks.check_book(t, last_n=3)
ok(b3["chapters"] == 3 and b3["range"] == [4, 6], "last_n 限近 N 章")

# 标题缺失混用:再加一章无标题
t.add_chapter("黄昏。他走了。", "")
b2 = checks.check_book(t)
ok(any("标题缺失" in f for f in b2["title_issues"]), "标题缺失混用检出")

# 干净多样的书不误报
w2 = World.create("w2", "W2", genre="都市")
t2 = Thread.create(w2, "clean", "干净线", genre="都市")
t2.add_chapter("他在地铁口等了十分钟，她终于出现，手里拎着两杯咖啡，笑着递过来一杯。", "重逢")
t2.add_chapter("会议室的空调坏了，所有人挤在走廊，争论着那份预算到底该砍谁的项目。", "争执")
t2.add_chapter("雨突然就下大了，两个人躲进便利店，隔着货架有一搭没一搭地聊起各自的过去。", "避雨")
bc = checks.check_book(t2)
ok(bc["time_opener_rate"] < 0.4 and not bc["cross_repeats"], "干净多样书不误报时间词/复读")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
