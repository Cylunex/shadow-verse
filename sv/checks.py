"""确定性质检 —— 把客观检查从模型卸给代码(产线可靠性,立即可用)。

字数(纯汉字)/ 去AI味词命中 / 术语-canon 一致(简易)。不替代审校子代理的判断,
而是给它一份客观底稿。继承旧 sv-novel/scripts/check.py 的思路。
"""
from __future__ import annotations

import re

from . import recipes, util
from .thread import Thread

# 去AI味:高频 AI 腔词/句式(命中即提示人工复核,不强删)
AI_FLAVOR = [
    "仿佛", "像是", "似乎", "彷佛", "不由得", "不禁", "心中", "暗自",
    "一丝", "一抹", "一缕", "深深地", "缓缓地", "轻轻地", "默默地",
    "五味杂陈", "百感交集", "心如刀绞", "无法言喻", "难以名状",
]
# 括号内心理旁白/解释(AI 味重灾区)
PAREN = re.compile(r"[（(][^）)]{0,40}[）)]")


def check_text(text: str, *, genre: str = "", target: int = 0) -> dict:
    """对一段正文跑确定性质检(产线中途未落盘也能审)。"""
    body = "\n".join(l for l in text.splitlines() if not l.startswith("#"))
    hanzi = util.hanzi_count(body)
    # 通用 AI 腔词 + 本题材高频疲劳词(配方驱动)
    words = AI_FLAVOR + recipes.forbidden_words(genre)
    flavor_hits = {}
    for w in dict.fromkeys(words):
        c = body.count(w)
        if c:
            flavor_hits[w] = c
    parens = PAREN.findall(body)

    findings = []
    if target and hanzi < target * 0.8:
        findings.append(f"字数偏少:{hanzi} / 目标 {target}(冷文风可预留扩写)")
    if target and hanzi > target * 1.6:
        findings.append(f"字数偏多:{hanzi} / 目标 {target}")
    if flavor_hits:
        top = "、".join(f"{w}×{c}" for w, c in sorted(flavor_hits.items(), key=lambda x: -x[1])[:6])
        findings.append(f"AI味词命中:{top}(复核是否可换具体动作/感官)")
    if len(parens) >= 3:
        findings.append(f"括号旁白 {len(parens)} 处(疑似心理解释,考虑落成动作/对话)")

    return {
        "hanzi": hanzi, "hanzi_target": target,
        "ai_flavor_hits": flavor_hits, "paren_count": len(parens),
        "findings": findings or ["客观检查未见明显问题"],
    }


def check_chapter(inst: "Thread", chapter_no: int) -> dict:
    r = check_text(inst.chapter_text(chapter_no),
                   genre=inst.meta().get("genre", ""), target=inst.meta().get("hanzi_target", 0))
    r["chapter"] = chapter_no
    return r
