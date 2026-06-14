"""L0 元件库(创世素材)—— 无限生成的"元素周期表"。

不存某作设定,存可复用的抽象元件(为什么有效/结构/可变体),每个带 AI摘要(喂生成器的食材)+ 标签。
锻造器(forge)按需取料组合成世界/角色/事件。继承旧 ReferenceLibrary 的抽象思路,落成引擎数据。
"""
from __future__ import annotations

from pathlib import Path

from . import clock, util
from .config import CODEX_DIR, load_json, save_json

# 元件类别(元素周期表的"族")
CATEGORIES = (
    "worlds",         # 世界母题/类型
    "mechanics",      # 力量/规则机制
    "characters",     # 角色原型
    "conflicts",      # 冲突结构
    "organizations",  # 势力/组织
    "scenes",         # 场景/桥段
    "themes",         # 母题/主题
)


def _idx_path() -> Path:
    return CODEX_DIR / "index.json"


def _load_index() -> dict:
    return load_json(_idx_path(), {"elements": []}) or {"elements": []}


def add(category: str, eid: str, summary: str, *, tags: list[str] | None = None, body: str = "") -> dict:
    """加一个元件。summary=AI摘要(食材说明),body=完整拆解(可选)。"""
    if category not in CATEGORIES:
        raise ValueError(f"类别必须 ∈ {CATEGORIES}:{category!r}")
    if not util.is_id(eid):
        raise ValueError(f"元件 id 必须 kebab-case:{eid!r}")
    rec = {"id": eid, "category": category, "summary": summary.strip(), "tags": tags or [], "added": clock.now_iso()}
    md = f"# {eid}\n\n> 类别:{category} ｜ 标签:{', '.join(tags or []) or '—'}\n\n## AI摘要(食材)\n{summary.strip()}\n\n## 拆解(为什么有效/结构/可变体)\n{body.strip() or '<!-- 待填 -->'}\n"
    util.write_md(CODEX_DIR / category / f"{eid}.md", md)
    idx = _load_index()
    idx["elements"] = [e for e in idx["elements"] if not (e["id"] == eid and e["category"] == category)]
    idx["elements"].append(rec)
    save_json(_idx_path(), idx)
    return rec


def all_elements() -> list[dict]:
    return _load_index().get("elements", [])


def remove(category: str, eid: str) -> bool:
    """删一个元件(索引 + md 文件)。返回是否删到。"""
    idx = _load_index()
    before = len(idx["elements"])
    idx["elements"] = [e for e in idx["elements"] if not (e["category"] == category and e["id"] == eid)]
    save_json(_idx_path(), idx)
    p = CODEX_DIR / category / f"{eid}.md"
    if p.exists():
        p.unlink()
    return len(idx["elements"]) < before


def seed_starter() -> dict:
    """幂等灌入起始元件库(已存在的同 类别+id 跳过)。返回 {added, skipped, total}。"""
    from . import codex_starter
    existing = {(e["category"], e["id"]) for e in all_elements()}
    added = 0
    for cat, eid, summary, tags, body in codex_starter.STARTER:
        if (cat, eid) in existing:
            continue
        add(cat, eid, summary, tags=list(tags), body=body)
        added += 1
    return {"added": added, "skipped": len(codex_starter.STARTER) - added, "total": len(all_elements())}


def pick(query: str = "", *, category: str = "", tags: list[str] | None = None, k: int = 8) -> list[dict]:
    """为生成取料:按 query(bigram 相关度)/类别/标签挑 top-k 元件喂锻造器。"""
    tags = tags or []
    scored = []
    for e in all_elements():
        if category and e["category"] != category:
            continue
        rel = util.similarity(query, e["summary"] + " " + " ".join(e["tags"])) if query else 0.0
        tag_hit = len(set(tags) & set(e["tags"])) * 0.5
        scored.append((rel + tag_hit, e))
    scored.sort(key=lambda x: x[0], reverse=True)
    picked = [e for s, e in scored if s > 0][:k]
    return picked or [e for _, e in scored[:k]]   # 无命中则返回前 k 个保底
