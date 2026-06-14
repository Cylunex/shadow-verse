"""核心循环的记忆机制 —— 铁律的代码实现。

> **rebuild(状态重建) ≠ retrieve(记忆检索)**,两个函数物理隔离,绝不混成"加载历史"。
> - rebuild():确定性、范围小 —— state + 近期 N 条 experiences + anchors,回答"现在什么样"。
> - retrieve():加权、全历史 —— anchors 常驻 + experiences 按相关度/新近度/重要度加权挑,回答"该想起什么"。

经历(experiences.jsonl)只追加,带 id/level/trace;状态(state.json)可回写。
向量检索是 retrieve() 里规模驱动才点亮的接口(现走 bigram 关键词),不影响铁律。
"""
from __future__ import annotations

import math
from pathlib import Path

from . import clock, util
from .config import (
    LEVEL_IMPORTANCE,
    RECENCY_TAU_DAYS,
    RECENT_EXP_REBUILD,
    RETRIEVE_TOP_K,
    W_IMPORTANCE,
    W_RECENCY,
    W_RELEVANCE,
    append_jsonl,
    load_json,
    read_jsonl,
    save_json,
)


def _exp_path(char_dir: Path) -> Path:
    return char_dir / "experiences.jsonl"


def _state_path(char_dir: Path) -> Path:
    return char_dir / "state.json"


# ---- 经历沉淀(只追加)----
def append_experience(
    char_dir: Path,
    text: str,
    *,
    level: str = "持久",
    where: str = "",
    trace: str = "",
    tags: list[str] | None = None,
) -> dict:
    """追加一条经历。level ∈ 瞬时/持久/身份。返回写入的条目(含 id)。"""
    if level not in LEVEL_IMPORTANCE:
        level = "持久"
    existing = read_jsonl(_exp_path(char_dir))
    entry = {
        "id": f"exp-{len(existing) + 1:04d}",
        "ts": clock.now_iso(),
        "where": where,
        "level": level,
        "text": text.strip(),
        "trace": trace.strip(),
        "tags": tags or [],
    }
    append_jsonl(_exp_path(char_dir), entry)
    return entry


def all_experiences(char_dir: Path) -> list[dict]:
    return read_jsonl(_exp_path(char_dir))


def recent_experiences(char_dir: Path, n: int = RECENT_EXP_REBUILD) -> list[dict]:
    return read_jsonl(_exp_path(char_dir))[-n:]


# ---- 状态(此刻)----
def read_state(char_dir: Path) -> dict:
    return load_json(_state_path(char_dir), {}) or {}


def write_state(char_dir: Path, updates: dict) -> dict:
    """合并式更新 state(只覆盖给到的键),盖时间戳。"""
    st = read_state(char_dir)
    st.update({k: v for k, v in (updates or {}).items() if v is not None})
    st["updated"] = clock.now_iso()
    save_json(_state_path(char_dir), st)
    return st


# ---- ① 状态重建(确定性、范围小)----
def rebuild(char_dir: Path, anchors: list[str] | None = None) -> dict:
    """"现在什么样":state + 近期经历 + anchors。不做加权、不扫全历史。"""
    return {
        "state": read_state(char_dir),
        "recent": recent_experiences(char_dir),
        "anchors": anchors or [],
    }


# ---- ② 记忆检索(加权、全历史)----
def _recency_weight(ts: str) -> float:
    try:
        dt = clock.now() - __import__("datetime").datetime.fromisoformat(ts)
        days = max(0.0, dt.total_seconds() / 86400.0)
    except Exception:
        days = 0.0
    return math.exp(-days / RECENCY_TAU_DAYS)


def retrieve(char_dir: Path, query: str, k: int = RETRIEVE_TOP_K) -> list[dict]:
    """"该想起什么":全历史 experiences 按 相关度×新近度×重要度 加权和挑 top-k。

    现走 bigram 关键词相关度;向量语义召回是规模驱动才点亮的接口(EMBED_PROVIDER)。
    """
    exps = read_jsonl(_exp_path(char_dir))
    if not exps:
        return []
    scored = []
    for e in exps:
        rel = util.similarity(query, e.get("text", "") + " " + " ".join(e.get("tags", [])))
        rec = _recency_weight(e.get("ts", ""))
        imp = LEVEL_IMPORTANCE.get(e.get("level", "持久"), 0.6)
        score = W_RELEVANCE * rel + W_RECENCY * rec + W_IMPORTANCE * imp
        scored.append((score, e))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in scored[:k]]
