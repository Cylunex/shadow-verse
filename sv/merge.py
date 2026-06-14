"""世界融合 —— 把一个世界(角色 + 叙事线 + 设定)融进另一个。为暗宇宙多元宇宙铺路。

用途:导入的小卡世界(一个场景)可融进一个大世界;两个世界合一。id 撞了自动改名,
源世界设定并入目标 world.md 的标记块(可见来源)。默认融完删源(及枢纽残留)。
"""
from __future__ import annotations

import shutil

from . import util
from .config import load_json, save_json
from .world import World

MERGE_MARK = "MERGED-FROM"


def _unique_dir(parent, base: str, suffix: str) -> str:
    name = base
    i = 1
    while (parent / name).exists():
        name = f"{base}-{suffix}" if i == 1 else f"{base}-{suffix}{i}"
        i += 1
    return name


def merge_world(src_id: str, dst_id: str, *, delete_src: bool = True) -> dict:
    """src → dst。返回 {moved_entities, moved_threads, deleted_src}。"""
    if src_id == dst_id:
        raise ValueError("不能融进自己")
    src, dst = World.load(src_id), World.load(dst_id)
    dst.entities_dir.mkdir(parents=True, exist_ok=True)
    dst.threads_dir.mkdir(parents=True, exist_ok=True)

    moved_e, moved_t = [], []
    for eid in src.list_entities():
        tgt = _unique_dir(dst.entities_dir, eid, src_id)
        shutil.copytree(src.entities_dir / eid, dst.entities_dir / tgt)
        moved_e.append(tgt)
    for tid in src.list_threads():
        tgt = _unique_dir(dst.threads_dir, tid, src_id)
        shutil.copytree(src.threads_dir / tid, dst.threads_dir / tgt)
        mp = dst.threads_dir / tgt / "meta.json"      # 线的 world 字段改指目标
        m = load_json(mp, {}) or {}
        m["world"] = dst_id; m["id"] = tgt
        save_json(mp, m)
        moved_t.append(tgt)

    # 源世界设定并入目标(标记块,可见来源、可手动剥离)
    block = (f"\n\n<!-- {MERGE_MARK}:{src_id} -->\n## 融入自「{src.meta().get('name', src_id)}」({src_id})\n\n"
             + util.read_md(src.dir / "world.md").strip() + f"\n<!-- /{MERGE_MARK}:{src_id} -->\n")
    wp = dst.dir / "world.md"
    util.write_md(wp, util.read_md(wp).rstrip() + block)

    deleted = False
    if delete_src:
        from . import nexus
        nexus.purge_world(src_id)
        src.delete()
        deleted = True
    return {"src": src_id, "dst": dst_id, "moved_entities": moved_e,
            "moved_threads": moved_t, "deleted_src": deleted}
