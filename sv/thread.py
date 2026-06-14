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

HOOK_TYPES = ("event", "concept")        # 事件钩子(带回收) / 概念阶梯(按层揭)
HOOK_LEVELS = ("α", "主", "中", "细")     # α悬念 > 主钩(卷) > 中钩(数章) > 细钩(章内)
HOOK_STATUS = ("待回收", "进行中", "已回收", "顺延", "放弃")

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

    # ---- 钩子台账(结构化状态机)----
    @property
    def hooks_path(self) -> Path:
        return self.dir / "hooks.json"

    def hooks_data(self) -> dict:
        return load_json(self.hooks_path, {"alpha": "", "hooks": []}) or {"alpha": "", "hooks": []}

    def _save_hooks(self, data: dict) -> None:
        save_json(self.hooks_path, data)
        self._render_hooks_md(data)

    def set_alpha(self, text: str) -> None:
        d = self.hooks_data(); d["alpha"] = text.strip(); self._save_hooks(d)

    def add_hook(self, desc: str, *, type: str = "event", level: str = "中", importance: str = "mid",
                 plant_chapter: int | None = None, payoff_target: int | None = None) -> dict:
        if type not in HOOK_TYPES:
            raise ValueError(f"钩子类型须 ∈ {HOOK_TYPES}")
        if level not in HOOK_LEVELS:
            raise ValueError(f"钩子层级须 ∈ {HOOK_LEVELS}")
        d = self.hooks_data()
        h = {"id": f"hook-{len(d['hooks']) + 1:04d}", "type": type, "desc": desc.strip(),
             "level": level, "importance": importance,
             "plant_chapter": plant_chapter if plant_chapter is not None else (self.last_chapter_no() or None),
             "payoff_target": payoff_target, "status": "待回收",
             "created": clock.now_iso(), "updated": clock.now_iso()}
        d["hooks"].append(h); self._save_hooks(d)
        return h

    def update_hook(self, hid: str, **fields) -> dict:
        d = self.hooks_data()
        for h in d["hooks"]:
            if h["id"] == hid:
                if "status" in fields and fields["status"] not in HOOK_STATUS:
                    raise ValueError(f"状态须 ∈ {HOOK_STATUS}")
                for k in ("status", "payoff_target", "desc", "level", "importance"):
                    if k in fields and fields[k] is not None:
                        h[k] = fields[k]
                h["updated"] = clock.now_iso()
                self._save_hooks(d)
                return h
        raise FileNotFoundError(f"无此钩子:{hid}")

    def open_hooks(self) -> list[dict]:
        return [h for h in self.hooks_data()["hooks"] if h["status"] in ("待回收", "进行中")]

    def overdue_hooks(self, current: int | None = None) -> list[dict]:
        """计划回收章已过、却仍未回收的钩子(确定性揪漏伏笔)。"""
        cur = current if current is not None else self.last_chapter_no()
        out = []
        for h in self.hooks_data()["hooks"]:
            t = h.get("payoff_target")
            if t and t <= cur and h["status"] in ("待回收", "进行中"):
                out.append(h)
        return out

    def _render_hooks_md(self, d: dict) -> None:
        lines = [f"# {self.meta().get('title', self.id)} · 钩子台账", "",
                 f"## α 悬念(全书唯一)\n{d.get('alpha') or '<!-- 未定 -->'}", "", "## 钩子"]
        if not d["hooks"]:
            lines.append("_(暂无)_")
        for h in d["hooks"]:
            tgt = f" → 计划回收 ch{h['payoff_target']}" if h.get("payoff_target") else ""
            plant = f" 埋于 ch{h['plant_chapter']}" if h.get("plant_chapter") else ""
            lines.append(f"- [{h['status']}] **{h['level']}** ({h['type']}) {h['desc']}{plant}{tgt} `{h['id']}`")
        util.write_md(self.dir / "hooks.md", "\n".join(lines))
