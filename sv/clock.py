"""可控时钟 — 让时间相关逻辑(新近度衰减/章节时间戳)可确定性测试。

默认走真实时间;测试用 use_virtual()/advance() 或 env SV_SIM_NOW(ISO 本地时间)固定。
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta

_virtual: datetime | None = None


def use_virtual(when: datetime | None = None) -> None:
    global _virtual
    _virtual = when or datetime(2026, 6, 14, 9, 0, 0)


def advance(**kw) -> None:
    global _virtual
    if _virtual is None:
        use_virtual()
    _virtual = _virtual + timedelta(**kw)  # type: ignore[operator]


def use_real() -> None:
    global _virtual
    _virtual = None


def now() -> datetime:
    if _virtual is not None:
        return _virtual
    env = os.environ.get("SV_SIM_NOW")
    if env:
        try:
            return datetime.fromisoformat(env)
        except ValueError:
            pass
    return datetime.now()


def now_iso() -> str:
    return now().replace(microsecond=0).isoformat()
