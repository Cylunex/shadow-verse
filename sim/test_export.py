"""H1.2 测试 —— export 全书导出:thread → 单文件可读 markdown(纯读,不改数据)。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_export_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import export  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

w = World.create("w", "无限塔", genre="无限流")
t = Thread.create(w, "line", "登塔记", genre="无限流")
t.add_chapter("苏栀踏上第一层,规则浮现。", "初入")
t.add_chapter("第二层,她看穿了缝隙。", "破局")

book = export.compile_thread_book(w, t)
ok(set(book) == {"filename", "content", "chapters", "hanzi"}, "返回 {filename,content,chapters,hanzi}")
ok(book["filename"] == "w-line.md", "文件名 = 世界-线.md")
ok(book["chapters"] == 2, "章数对")
ok(book["content"].startswith("# 登塔记"), "书名作一级标题")
ok("# 第 1 章" in book["content"] and "# 第 2 章" in book["content"], "各章正文拼入(含章标题)")
ok("苏栀踏上第一层" in book["content"] and "看穿了缝隙" in book["content"], "正文内容齐")
ok(book["hanzi"] > 0, "统计汉字数")
ok(not (w.dir / "exported.md").exists(), "纯读,不落新文件")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
