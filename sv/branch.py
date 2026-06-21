"""线分支 —— 从某章/某楼分叉出平行可能性,带蝴蝶效应追踪(线分支 backlog)。

借鉴 infiplot(Scene/Beat 分支图:continue/choice 边)+ interactive-novel(蝴蝶效应 divergence_points)。
轻做法(同 Luker checkpoint):分支共享母线前 N 章,从分叉点起写自己的章;divergence.jsonl 记每个偏离点的后果链。
存 `worlds/<w>/threads/<t>/branches/<bid>/`。零依赖。
"""
from __future__ import annotations

from . import clock, util
from .config import append_jsonl, load_json, read_jsonl, save_json
from .thread import Thread


def _branches_root(thread: Thread):
    return thread.dir / "branches"


def index_path(thread: Thread):
    return _branches_root(thread) / "index.json"


def list_branches(thread: Thread) -> list[dict]:
    return load_json(index_path(thread), []) or []


class Branch:
    def __init__(self, thread: Thread, bid: str):
        self.thread = thread
        self.bid = bid
        self.dir = _branches_root(thread) / bid

    @property
    def meta_path(self):
        return self.dir / "meta.json"

    @property
    def chapters_dir(self):
        return self.dir / "chapters"

    @property
    def divergence_path(self):
        return self.dir / "divergence.jsonl"

    def exists(self) -> bool:
        return self.meta_path.exists()

    def meta(self) -> dict:
        return load_json(self.meta_path, {}) or {}

    @classmethod
    def create(cls, thread: Thread, from_chapter: int, *, name: str = "",
               divergence: str = "", parent: str = "main", bid: str | None = None) -> "Branch":
        """从母线第 from_chapter 章后分叉。divergence=这次偏离的一句话(原走向→新走向)。"""
        existing = list_branches(thread)
        bid = util.safe_name(bid or f"branch-{len(existing) + 1:03d}")
        b = cls(thread, bid)
        if b.exists():
            raise FileExistsError(f"分支已存在:{bid}")
        from_chapter = max(0, min(int(from_chapter), thread.last_chapter_no()))
        b.dir.mkdir(parents=True, exist_ok=True)
        save_json(b.meta_path, {"id": bid, "name": name or bid, "thread": thread.id,
                                "world": thread.world.id, "from_chapter": from_chapter,
                                "parent": parent, "created": clock.now_iso()})
        entry = {"id": bid, "name": name or bid, "from_chapter": from_chapter,
                 "parent": parent, "created": clock.now_iso()}
        save_json(index_path(thread), existing + [entry])
        if divergence.strip():
            b.add_divergence(divergence, chapter=from_chapter)
        return b

    @classmethod
    def load(cls, thread: Thread, bid: str) -> "Branch":
        b = cls(thread, bid)
        if not b.exists():
            raise FileNotFoundError(f"无此分支:{bid}")
        return b

    # ---- 分支章节(前 from_chapter 章共享母线,之后写自己的)----
    def last_chapter_no(self) -> int:
        own = util.next_chapter_no(self.chapters_dir) - 1
        return max(self.meta().get("from_chapter", 0), own)

    def add_chapter(self, text: str, title: str = "") -> int:
        no = max(self.meta().get("from_chapter", 0), util.next_chapter_no(self.chapters_dir) - 1) + 1
        header = f"# 第 {no} 章" + (f" · {title}" if title else "") + "\n\n"
        util.write_md(self.chapters_dir / f"{no:03d}.md", header + text.strip())
        return no

    def chapter_text(self, no: int) -> str:
        """≤from_chapter 读母线,之后读分支自己的。"""
        if no <= self.meta().get("from_chapter", 0):
            return self.thread.chapter_text(no)
        p = self.chapters_dir / f"{no:03d}.md"
        return util.read_md(p) if p.exists() else ""

    # ---- 蝴蝶效应 divergence_points ----
    def add_divergence(self, summary: str, *, chapter: int | None = None,
                       original: str = "", actual: str = "", ripple: list | None = None) -> dict:
        d = {"id": f"div-{len(self.divergences()) + 1:03d}", "ts": clock.now_iso(),
             "chapter": chapter, "summary": summary.strip(),
             "original": original, "actual": actual, "ripple_effects": ripple or []}
        append_jsonl(self.divergence_path, d)
        return d

    def divergences(self) -> list[dict]:
        return read_jsonl(self.divergence_path)

    def delete(self) -> None:
        import shutil
        if self.dir.exists():
            shutil.rmtree(self.dir)
        idx = [e for e in list_branches(self.thread) if e.get("id") != self.bid]
        save_json(index_path(self.thread), idx)


# ========== Scene/Beat 分支图(play/互动叙事的节点模型,借 infiplot)==========
# 轻量 dataclass 化:beat 节点 + continue/choice 边 + advance-beat/change-scene 双效果。
def beat(bid: str, text: str, *, speaker: str = "", nxt=None) -> dict:
    """一个剧情节点。nxt = {"type":"continue","to":bid} 或 {"type":"choice","choices":[...]}。"""
    return {"id": bid, "text": text, "speaker": speaker, "next": nxt or {"type": "end"}}


def choice(label: str, *, effect: str = "advance-beat", target: str = "") -> dict:
    """一个选项。effect∈advance-beat(同场推进)/change-scene(切场/分叉新线)。"""
    return {"label": label, "effect": effect, "target": target}
