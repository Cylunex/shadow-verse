"""导出 —— 把写出来的东西取出来读/分享(纯读,不改数据)。

thread → 单文件全书(把各章拼成一本可读 markdown)。这是"写小说"的产出口。
"""
from __future__ import annotations

from . import util
from .thread import Thread
from .world import World


def compile_thread_book(world: World, thread: Thread) -> dict:
    """把一条线的全部章节拼成一本书(markdown)。返回 {filename, content, chapters, hanzi}。"""
    m = thread.meta()
    wmeta = world.meta()
    parts = [
        f"# {m.get('title', thread.id)}",
        "",
        f"> 世界:{wmeta.get('name', world.id)} ｜ 题材:{m.get('genre', '')} ｜ "
        f"{m.get('chapter_count', 0)} 章 ｜ 透镜:{'、'.join(m.get('lenses', [])) or '—'}",
        "",
    ]
    premise = util.read_md(thread.dir / "thread.md").strip()
    if premise:
        parts += ["## 卷首(立意 / 大纲)", "", premise, "", "---", ""]
    for n in range(1, thread.last_chapter_no() + 1):
        parts.append(thread.chapter_text(n).strip())   # 正文已含「# 第N章」标题
        parts.append("")
    summary = thread.summary().strip()
    if summary:
        parts += ["---", "", "## 全书摘要", "", summary]
    content = "\n".join(parts).strip() + "\n"
    return {
        "filename": f"{world.id}-{thread.id}.md",
        "content": content,
        "chapters": thread.last_chapter_no(),
        "hanzi": util.hanzi_count(content),
    }
