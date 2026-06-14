"""L2 · 叙事线(Thread)—— 世界里"发生的事"的单元。

一条线可被多个透镜体验:读(narrate→chapters)/玩(play→sessions)/模拟(simulate→beats)/可视化(render→renders)。
beats.jsonl 是跨透镜共享的事件日志:无论怎么体验,发生的事都落同一条时间线,实体记得。
meta.json 管结构态(题材/尺度/节奏契约/触达的透镜/章数/谱系)。thread.md 是立意+大纲(创作内容)。
"""
from __future__ import annotations

from pathlib import Path

from . import clock, provenance, util
from .config import DEFAULT_SCALE, HANZI_TARGET, append_jsonl, load_json, read_jsonl, save_json
from .world import World

THREAD_TEMPLATE = """# {title} · 叙事线

> 线 id:`{id}` ｜ 世界:{world} ｜ 题材:{genre} ｜ 尺度:{scale}

## 立意 / 一句话
<!-- 这条线在讲什么 -->

## 节奏契约(每章/每段必须推进什么)
- {pacing}

## 大纲(beats / 钩子 / 爽点 / 悬念)
<!-- α 悬念统领;一章主推一条钩子的下一层 -->

## 钩子台账
<!-- 事件钩子(状态机)/ 概念阶梯 -->
"""


class Thread:
    def __init__(self, world: World, tid: str):
        self.world = world
        self.id = tid
        self.dir = world.threads_dir / tid

    @property
    def meta_path(self) -> Path:
        return self.dir / "meta.json"

    @property
    def chapters_dir(self) -> Path:
        return self.dir / "chapters"

    @property
    def sessions_dir(self) -> Path:
        return self.dir / "sessions"

    @property
    def renders_dir(self) -> Path:
        return self.dir / "renders"

    @property
    def beats_path(self) -> Path:
        return self.dir / "beats.jsonl"

    def exists(self) -> bool:
        return self.meta_path.exists()

    def meta(self) -> dict:
        return load_json(self.meta_path, {}) or {}

    def save_meta(self, meta: dict) -> None:
        save_json(self.meta_path, meta)

    def update_meta(self, **kw) -> dict:
        m = self.meta()
        m.update(kw)
        self.save_meta(m)
        return m

    def mark_lens(self, lens: str) -> None:
        m = self.meta()
        if lens not in m.get("lenses", []):
            m.setdefault("lenses", []).append(lens)
            self.save_meta(m)

    @classmethod
    def create(
        cls, world: World, tid: str, title: str, *, genre: str = "", scale: str = "",
        pacing: str = "每章至少推进一条主线钩子", hanzi_target: int = HANZI_TARGET,
        prov: dict | None = None,
    ) -> "Thread":
        if not util.is_id(tid):
            raise ValueError(f"线 id 必须 kebab-case:{tid!r}")
        t = cls(world, tid)
        if t.exists():
            raise FileExistsError(f"线已存在:{world.id}/{tid}")
        wmeta = world.meta()
        scale = scale or wmeta.get("scale", DEFAULT_SCALE)
        genre = genre or wmeta.get("genre", "")
        t.save_meta({
            "id": tid, "world": world.id, "title": title, "genre": genre, "scale": scale,
            "pacing": pacing, "lenses": [], "status": "open",
            "chapter_count": 0, "summary_through": 0, "hanzi_target": hanzi_target,
            "provenance": prov or provenance.stamp("manual"), "created": clock.now_iso(),
        })
        util.write_md(t.dir / "thread.md", THREAD_TEMPLATE.format(
            id=tid, world=world.id, title=title, genre=genre or "未定", scale=scale, pacing=pacing))
        util.write_md(t.dir / "summary.md", f"# {title} · 摘要\n\n<!-- 每 N 章压缩 -->\n")
        return t

    @classmethod
    def load(cls, world: World, tid: str) -> "Thread":
        t = cls(world, tid)
        if not t.exists():
            raise FileNotFoundError(f"线不存在:{world.id}/{tid}")
        return t

    def delete(self) -> None:
        import shutil
        if self.dir.exists():
            shutil.rmtree(self.dir)

    # ---- 跨透镜事件日志 ----
    def add_beat(self, text: str, *, lens: str, where: str = "") -> dict:
        beat = {"id": f"beat-{len(read_jsonl(self.beats_path)) + 1:04d}", "ts": clock.now_iso(),
                "lens": lens, "where": where, "text": text.strip()}
        append_jsonl(self.beats_path, beat)
        return beat

    def beats(self) -> list[dict]:
        return read_jsonl(self.beats_path)

    # ---- narrate 透镜:章节 ----
    def add_chapter(self, text: str, title: str = "") -> int:
        no = util.next_chapter_no(self.chapters_dir)
        header = f"# 第 {no} 章" + (f" · {title}" if title else "") + "\n\n"
        util.write_md(self.chapters_dir / f"{no:03d}.md", header + text.strip())
        self.update_meta(chapter_count=no)
        self.mark_lens("narrate")
        return no

    def chapter_text(self, no: int) -> str:
        return util.read_md(self.chapters_dir / f"{no:03d}.md")

    def last_chapter_no(self) -> int:
        return util.next_chapter_no(self.chapters_dir) - 1

    def summary(self) -> str:
        return util.read_md(self.dir / "summary.md")

    def write_summary(self, text: str) -> None:
        util.write_md(self.dir / "summary.md", text)
        self.update_meta(summary_through=self.last_chapter_no())
