"""通用工具:id/slug、markdown 文件读写、汉字计数、bigram 相似度(零依赖)。"""
from __future__ import annotations

import re
from pathlib import Path

_HANZI = re.compile(r"[一-鿿]")
_NON_ID = re.compile(r"[^a-z0-9]+")


def slug(text: str) -> str:
    """把任意文本转成稳定的 kebab-case id。中文用拼音不可靠,故中文标题应显式给 id。"""
    s = _NON_ID.sub("-", text.strip().lower()).strip("-")
    return s or "x"


def is_id(text: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9][a-z0-9-]*", text or ""))


def hanzi_count(text: str) -> int:
    """纯汉字字数(产线统一口径,不含标点/空白/英文)。"""
    return len(_HANZI.findall(text or ""))


def read_md(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")


def _bigrams(s: str) -> set[str]:
    s = re.sub(r"\s+", "", s or "")
    return {s[i : i + 2] for i in range(len(s) - 1)} if len(s) >= 2 else ({s} if s else set())


def similarity(a: str, b: str) -> float:
    """无 embedding 时的关键词相关度:汉字 bigram Jaccard。范围 0-1。"""
    ba, bb = _bigrams(a), _bigrams(b)
    if not ba or not bb:
        return 0.0
    return len(ba & bb) / len(ba | bb)


def next_chapter_no(chapters_dir: Path) -> int:
    """扫描 chapters/ 取下一章号(三位补零文件名)。"""
    if not chapters_dir.exists():
        return 1
    mx = 0
    for p in chapters_dir.glob("*.md"):
        m = re.match(r"(\d+)", p.stem)
        if m:
            mx = max(mx, int(m.group(1)))
    return mx + 1
