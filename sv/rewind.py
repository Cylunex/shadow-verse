"""回溯(Rewind)—— 拨回一个【世界】的时钟。执钟人(薇拉)人设的引擎实质。

`snapshot` 存一份世界的可恢复态;`rollback` 先自动备份当前(可 redo)、再从快照恢复,
并在世界线补一条「⟲ 回溯」beat —— **回溯本身也留痕,因果不虚**(业不虚,可回溯重演)。

边界(青莲在时钟之上):魂的身份记忆(`souls/<id>/identity.jsonl`)是跨世界不变量、
在单个世界的时钟之上 —— 回溯一个世界**不抹魂的身份**(「我永远记得的事」)。
拨的是那个世界的钟,不是魂的永恒。世界本地态(实体 state/经历/数值、世界线 beats、
钩子、章节、世界书)才随快照回滚。
"""
from __future__ import annotations

import re
import shutil

from . import clock
from .config import load_json, save_json
from .thread import Thread
from .world import World

SNAP_DIRNAME = "snapshots"
_SNAP_RE = re.compile(r"snap-(\d+)")


def _snaps_dir(world: World):
    return world.dir / SNAP_DIRNAME


def _restorable(world: World):
    """世界目录下除 snapshots/ 外的全部(实体/线/设定/世界书)——文本为主,小。"""
    return [p for p in world.dir.iterdir() if p.name != SNAP_DIRNAME]


def _next_id(world: World) -> str:
    sd = _snaps_dir(world)
    nums = [int(m.group(1)) for d in sd.iterdir() for m in [_SNAP_RE.fullmatch(d.name)] if m] if sd.exists() else []
    return f"snap-{(max(nums) + 1) if nums else 1:03d}"


def _beat_count(world: World) -> int:
    n = 0
    for tid in world.list_threads():
        try:
            n += len(Thread(world, tid).beats())
        except Exception:  # noqa: BLE001
            pass
    return n


def _worldline(world: World) -> Thread:
    tid = "worldline"
    if not Thread(world, tid).exists():
        Thread.create(world, tid, f"{world.meta().get('name', world.id)} · 世界线",
                      genre=world.meta().get("genre", ""))
    return Thread(world, tid)


def snapshot(world: World, label: str = "", *, auto: bool = False) -> dict:
    """给世界拍一份可恢复快照(全量复制 snapshots/ 外的文本与资产)。返回快照元信息。"""
    sd = _snaps_dir(world)
    sd.mkdir(parents=True, exist_ok=True)
    sid = _next_id(world)
    dst = sd / sid
    dst.mkdir()
    for p in _restorable(world):
        if p.is_dir():
            shutil.copytree(p, dst / p.name)
        else:
            shutil.copy2(p, dst / p.name)
    meta = {"id": sid, "label": label or ("回溯前自动备份" if auto else ""),
            "ts": clock.now_iso(), "auto": auto, "beats": _beat_count(world)}
    save_json(dst / "_snap.json", meta)
    return meta


def snapshots(world: World) -> list[dict]:
    """列出该世界的全部快照(按 id 升序)。"""
    sd = _snaps_dir(world)
    if not sd.exists():
        return []
    out = [load_json(d / "_snap.json", {}) for d in sd.iterdir() if (d / "_snap.json").exists()]
    return sorted([m for m in out if m], key=lambda m: m.get("id", ""))


def rollback(world: World, snap_id: str) -> dict:
    """拨回时钟:先自动备份当前(可 redo),再从快照恢复世界本地态,世界线补一条回溯 beat。"""
    src = _snaps_dir(world) / snap_id
    if not (src / "_snap.json").exists():
        raise FileNotFoundError(f"快照不存在:{snap_id}")
    snap_meta = load_json(src / "_snap.json", {}) or {}
    backup = snapshot(world, label=f"回溯前(→{snap_id})", auto=True)   # 先备份当前(snapshots/ 不被 wipe)
    for p in _restorable(world):                                       # 清当前世界本地态
        shutil.rmtree(p) if p.is_dir() else p.unlink()
    for p in src.iterdir():                                            # 从快照恢复(不含 snapshots/)
        if p.name == "_snap.json":
            continue
        shutil.copytree(p, world.dir / p.name) if p.is_dir() else shutil.copy2(p, world.dir / p.name)
    rewind_beat = False                                               # 回溯本身留痕(恢复后追加,不被覆盖)
    try:
        b = _worldline(world).add_beat(
            f"⟲ 世界被拨回到「{snap_meta.get('label') or snap_id}」(执钟人回溯)",
            lens="cross", where="rewind:")
        rewind_beat = bool(b)
    except Exception:  # noqa: BLE001 — 留痕失败不阻断回溯本身
        pass
    return {"restored": snap_id, "label": snap_meta.get("label"), "backup": backup["id"],
            "rewind_beat": rewind_beat}
