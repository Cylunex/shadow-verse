"""LLM 输出的容错 JSON 解析 —— 模型常返回带围栏/思考前缀/缺闭合符/中文标点的"脏 JSON"。

逐级降解(任一级成功即返回):
  ① 直解 → ② 去 BOM/思考块/代码围栏后直解 → ③ 对象切片(首个 { 或 [ 配平到末尾) →
  ④ 修复(去尾逗号 + 补缺失闭合符) → ⑤ 最后一搏(结构态中文标点归一)。

借鉴 InfiPlot parseJsonLoose(四级降解) + Novel-Auto-Generator parserService(修复管线)。
**人在环原则**:解析失败返回 default(默认 {}),绝不把异常抛给上层炸产线。零依赖。
"""
from __future__ import annotations

import json
import re

_FENCE = re.compile(r"```(?:json|JSON)?\s*(.*?)```", re.S)
_THINK = re.compile(r"<think(?:ing)?>.*?</think(?:ing)?>", re.S | re.I)
_TRAILING_COMMA = re.compile(r",(\s*[}\]])")
# 仅当作结构分隔时才会被归一的"全角/弯引号"(最后一搏,可能误伤值内中文引号,故放最末级)
_STRUCT_QUOTES = {"“": '"', "”": '"', "‘": "'", "’": "'", "，": ",", "：": ":"}

_OPEN = {"{": "}", "[": "]"}
_CLOSE = {"}", "]"}


def _strip(text: str) -> str:
    """去 BOM / 思考块 / 代码围栏,留最可能含 JSON 的片段。"""
    s = (text or "").lstrip("﻿").strip()
    s = _THINK.sub("", s)
    m = _FENCE.search(s)
    if m and m.group(1).strip():
        return m.group(1).strip()
    return s


def _balanced_span(s: str) -> str | None:
    """从首个 { 或 [ 起,按括号栈(尊重字符串/转义)切出配平片段;未闭合则补齐缺失闭合符。"""
    start = -1
    for i, ch in enumerate(s):
        if ch in _OPEN:
            start = i
            break
    if start < 0:
        return None
    stack: list[str] = []
    in_str = False
    esc = False
    end = -1
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in _OPEN:
            stack.append(_OPEN[ch])
        elif ch in _CLOSE:
            if stack and stack[-1] == ch:
                stack.pop()
                if not stack:
                    end = i
                    break
            # 不匹配的闭合符:忽略(容错)
    frag = s[start : (end + 1 if end >= 0 else len(s))]
    if end < 0:
        # 未闭合:按栈补齐(字符串未闭合先补引号)
        if in_str:
            frag += '"'
        frag += "".join(reversed(stack))
    return frag


def _attempt(s: str):
    try:
        return json.loads(s), True
    except Exception:
        return None, False


def loads(text, default=None):
    """容错解析:返回 dict/list;全失败返回 default(None→{})。text 可为已解析对象(原样过)。"""
    if default is None:
        default = {}
    if isinstance(text, (dict, list)):
        return text
    if not isinstance(text, str):
        return default

    # ① 直解
    val, ok = _attempt(text)
    if ok:
        return val
    # ② 去壳直解
    s = _strip(text)
    val, ok = _attempt(s)
    if ok:
        return val
    # ③ 对象切片
    frag = _balanced_span(s)
    if frag is None:
        return default
    val, ok = _attempt(frag)
    if ok:
        return val
    # ④ 修复:去尾逗号 + 再切片配平
    repaired = _TRAILING_COMMA.sub(r"\1", frag)
    repaired = _balanced_span(repaired) or repaired
    val, ok = _attempt(repaired)
    if ok:
        return val
    # ⑤ 最后一搏:结构态中文标点归一(可能误伤值内引号,仅当前面全败才用)
    last = repaired
    for a, b in _STRUCT_QUOTES.items():
        last = last.replace(a, b)
    last = _TRAILING_COMMA.sub(r"\1", last)
    last = _balanced_span(last) or last
    val, ok = _attempt(last)
    return val if ok else default
