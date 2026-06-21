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


# ---------- 外部文件安全(导入不可信 ST 卡/世界书/预设时用;借 MimirLink SECURITY_FIXES)----------
_UNSAFE = re.compile(r"[\\/]|\.\.")
_SECRET_KEY = re.compile(r"(pass(word)?|api[_-]?key|token|secret|authorization|x-api-key)", re.I)


def safe_name(name: str, *, maxlen: int = 200) -> str:
    """清洗外部来源的文件名/id:剥路径分隔符与 `..`,限长(防路径遍历 + DoS)。"""
    s = _UNSAFE.sub("", str(name or "")).strip().strip(".")
    return s[:maxlen] or "x"


def guard_size(data, *, limit: int, what: str = "数据") -> None:
    """外部 JSON 体积上限(防 JSON.parse 炸弹 DoS)。data 为 str/bytes 时校验字节数。"""
    n = len(data.encode("utf-8")) if isinstance(data, str) else (len(data) if isinstance(data, (bytes, bytearray)) else 0)
    if n > limit:
        raise ValueError(f"{what}过大:{n} 字节 > 上限 {limit}(疑似恶意/损坏文件)")


def redact(obj):
    """递归脱敏:把含 password/apiKey/token/secret 的键的值替成 ***(写日志/回执前用)。"""
    if isinstance(obj, dict):
        return {k: ("***" if _SECRET_KEY.search(str(k)) else redact(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(x) for x in obj]
    return obj


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
