"""Run Event Journal —— append-only JSONL,记一次产线运行的全过程(可审计/可重放)。

借鉴 TauriTavern RunEventJournal:seq 单调递增、关键副作用落账、可重放重建 timeline。
shadow-verse 用它给 narrate 产线(写→审→改→落)一条审计线:每步落一个事件,出问题能回溯。
存 `worlds/<w>/threads/<t>/runs/<run_id>.jsonl`。零依赖。
"""
from __future__ import annotations

from . import clock
from .config import append_jsonl, read_jsonl


class Journal:
    def __init__(self, path):
        self.path = path

    def append(self, kind: str, **data) -> dict:
        """落一个事件;seq 单调递增(按已有行数)。kind=start/draft/review/revise/commit/error/finish。"""
        seq = len(self.events()) + 1
        ev = {"seq": seq, "ts": clock.now_iso(), "kind": kind, **data}
        append_jsonl(self.path, ev)
        return ev

    def events(self) -> list[dict]:
        return read_jsonl(self.path)

    def last_seq(self) -> int:
        return len(self.events())

    def summary(self) -> dict:
        evs = self.events()
        from collections import Counter
        return {"events": len(evs), "kinds": dict(Counter(e.get("kind") for e in evs)),
                "first": evs[0] if evs else None, "last": evs[-1] if evs else None}


def _runs_dir(thread):
    return thread.dir / "runs"


def open_run(thread, run_id: str | None = None) -> Journal:
    """为一次产线运行开一本日志。run_id 不给则按已有 run 数自增。"""
    d = _runs_dir(thread)
    if not run_id:
        n = (len(list(d.glob("*.jsonl"))) + 1) if d.exists() else 1
        run_id = f"run-{n:03d}"
    return Journal(d / f"{run_id}.jsonl")


def list_runs(thread) -> list[str]:
    d = _runs_dir(thread)
    return sorted(p.stem for p in d.glob("*.jsonl")) if d.exists() else []
