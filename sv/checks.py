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
# 中文正文里混用半角句读(宜全角，。！？)
HALFWIDTH = re.compile(r"[一-鿿][,.;:!?](?=[一-鿿])")
# 句子切分
_SENT = re.compile(r"[^。！？!?\n]*[。！？!?]")


def _repetition(body: str, n: int = 5, min_count: int = 3) -> dict[str, int]:
    """重复短语:长度 n 的汉字窗口出现 ≥min_count 次(揪复读/口水)。"""
    s = "".join(re.findall(r"[一-鿿]", body))
    if len(s) < n:
        return {}
    counts: dict[str, int] = {}
    for i in range(len(s) - n + 1):
        g = s[i : i + n]
        counts[g] = counts.get(g, 0) + 1
    return {g: c for g, c in counts.items() if c >= min_count}


def _long_run(body: str, long_len: int = 22) -> int:
    """最长连续长句段数(长句堆叠=节奏偏慢/单调)。"""
    run = best = 0
    for s in _SENT.findall(body):
        if util.hanzi_count(s) >= long_len:
            run += 1; best = max(best, run)
        else:
            run = 0
    return best


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
    halfwidth = len(HALFWIDTH.findall(body))
    reps = _repetition(body)
    long_run = _long_run(body)

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
    if halfwidth >= 3:
        findings.append(f"半角标点 {halfwidth} 处(中文正文宜用全角，。！?)")
    if reps:
        top = "、".join(f"「{g}」×{c}" for g, c in sorted(reps.items(), key=lambda x: -x[1])[:4])
        findings.append(f"重复短语:{top}(复读/口水,换说法)")
    if long_run >= 4:
        findings.append(f"长句连堆 {long_run} 句(节奏偏慢/单调,穿插短句)")

    return {
        "hanzi": hanzi, "hanzi_target": target,
        "ai_flavor_hits": flavor_hits, "paren_count": len(parens),
        "halfwidth": halfwidth, "repetition": reps, "long_run": long_run,
        "findings": findings or ["客观检查未见明显问题"],
    }


def check_chapter(inst: "Thread", chapter_no: int) -> dict:
    r = check_text(inst.chapter_text(chapter_no),
                   genre=inst.meta().get("genre", ""), target=inst.meta().get("hanzi_target", 0))
    r["chapter"] = chapter_no
    return r


# ========== 全书级纵向基线(单章 check_text 查不出的"整本一个调子")==========
# 借鉴 ainovel-cli/stylestat.go:把"句式 tic 章均频次 / 跨章逐字复读 / 章末同构 / 开篇套路"
# 这些只有累积多章才显形的 AI 味,从代码侧客观统计(零幻觉),喂反思子代理做横向裁定。

# 全书句式 tic(整本反复出现才是问题;放进 check_book 看章均,不进单章质检以免误伤)
BOOK_TICS = {
    "不是…而是…": re.compile(r"不是[^，。！？\n]{1,20}而是"),
    "明喻(像/如/仿佛…一般/似的)": re.compile(r"(?:像|如同?|仿佛|犹如)[^，。！？\n]{1,18}(?:一般|似的|一样|般)"),
    "沉默节拍": re.compile(r"沉默(?:了|片刻|良久)?|没有(?:说话|应答|回答)|陷入(?:沉默|寂静)"),
    "的…的…的堆叠": re.compile(r"[一-鿿]的[一-鿿]{1,6}的[一-鿿]{1,6}的"),
}
# 章首时间词(每章都"清晨/夜里/三天后"开篇 = 套路化转场)
TIME_OPENERS = (
    "清晨", "早晨", "凌晨", "拂晓", "天亮", "黎明", "正午", "午后", "黄昏", "傍晚", "入夜",
    "夜里", "夜晚", "深夜", "子夜", "翌日", "次日", "隔日", "三天后", "几天后", "数日后",
    "良久", "许久", "这一天", "那一天", "这天", "那天", "当夜", "当晚", "半个时辰",
)
_CH_HEADER = re.compile(r"#\s*第\s*\d+\s*章(?:\s*[·:：、]\s*(.+))?")


def _chapter_parts(inst: "Thread", no: int) -> tuple[str, str]:
    """拆一章 → (标题, 去标题正文)。标题从『# 第 N 章 · 标题』头行解析。"""
    title, body = "", []
    for ln in inst.chapter_text(no).splitlines():
        s = ln.strip()
        if s.startswith("#"):
            m = _CH_HEADER.match(s)
            if m and m.group(1):
                title = m.group(1).strip()
            continue
        body.append(ln)
    return title, "\n".join(body).strip()


def _c2_diagnose(inst: "Thread") -> list:
    """C2 规则化诊断:偏离细纲(字数/出场) + 命名混用。无 outline/glossary 数据则空(休眠)。"""
    out: list = []
    chapters_spec = (inst.outline() or {}).get("chapters") or {}
    terms = (inst.world.glossary() or {}).get("terms", [])
    for no in range(1, inst.last_chapter_no() + 1):
        _, body = _chapter_parts(inst, no)
        if not body:
            continue
        spec = chapters_spec.get(str(no))
        if spec:
            tgt = spec.get("target_hanzi") or 0
            if tgt:
                actual = util.hanzi_count(body)
                if abs(actual - tgt) / tgt > 0.4:
                    out.append({"rule": "偏离细纲·字数", "target": "writer",
                                "evidence": f"ch{no} 实际 {actual} 字 vs 细纲目标 {tgt} 字",
                                "suggestion": "贴近细纲目标字数,或修订该章细纲"})
            missing = [c for c in (spec.get("cast") or []) if c and c not in body]
            if missing:
                out.append({"rule": "偏离细纲·出场", "target": "writer",
                            "evidence": f"ch{no} 细纲计划出场未见:{'、'.join(missing)}",
                            "suggestion": "让计划出场的角色到场,或修订细纲出场表"})
        for t in terms:   # 命名混用:同一词条本章出现 ≥2 个不同别名 = 称呼不一致(低噪)
            aliases = sorted({a for a in (t.get("aliases") or []) if a and a in body})
            if len(aliases) >= 2:
                out.append({"rule": "命名混用", "target": "writer",
                            "evidence": f"ch{no} 同一对象混用别名「{'/'.join(aliases[:3])}」",
                            "suggestion": f"统一为规范名「{t.get('name', '')}」"})
    return out


def reflect_diagnose(inst: "Thread") -> dict:
    """规则化诊断(吸收 ainovel-cli/diag):聚合全书基线 + 钩子台账 → Finding{rule,evidence,suggestion,target}。

    target 指向 writer(改稿)还是 recipe(调题材配方/节奏)——让反思不只报问题、还指明该往哪改。
    """
    findings = []
    for f in check_book(inst)["findings"]:
        if "未见明显问题" in f or "样本不足" in f:
            continue
        findings.append({"rule": "文风基线", "evidence": f, "suggestion": "换说法/补多样性", "target": "writer"})
    for h in inst.overdue_hooks():
        findings.append({"rule": "伏笔过期", "target": "writer",
                         "evidence": f"「{h.get('desc', '')}」计划 ch{h.get('payoff_target')} 未回收",
                         "suggestion": "尽快回收或顺延 payoff_target"})
    if inst.last_chapter_no() >= 3 and not inst.open_hooks():
        findings.append({"rule": "钩子断档", "target": "recipe",
                         "evidence": "当前无开放钩子", "suggestion": "埋新钩牵引追读(见 HOOK_TAXONOMY)"})
    findings.extend(_c2_diagnose(inst))   # C2:偏离细纲 / 命名混用(无 outline/glossary 则空)
    from collections import Counter
    return {"findings": findings, "profile": recipes.get_profile(inst.meta().get("genre", "")),
            "target_summary": dict(Counter(f["target"] for f in findings))}


def check_book(inst: "Thread", *, last_n: int | None = None) -> dict:
    """全书纵向基线:句式 tic 章均频次 / 跨≥3章逐字复读句 / 章末短结尾率 / 开篇时间词率 / 标题缺失或重复。

    last_n 限近 N 章(长篇增量审,省 token)。<3 章不出基线(样本不足)。
    """
    last = inst.last_chapter_no()
    start = max(1, last - last_n + 1) if last_n else 1
    nos = list(range(start, last + 1))
    n = len(nos)
    if n < 3:
        return {"chapters": n, "tics": {}, "cross_repeats": {}, "time_opener_rate": 0.0,
                "short_ending_rate": 0.0, "title_issues": [],
                "findings": [f"章数 {n}<3,样本不足,跳过全书基线(继续累积章节)"]}

    tics = {name: 0 for name in BOOK_TICS}
    sent_chapters: dict[str, set[int]] = {}   # 长句 → 出现的章号集合(跨章逐字复读)
    time_openers = 0
    short_endings = 0
    titles: list[str] = []

    for no in nos:
        title, body = _chapter_parts(inst, no)
        titles.append(title)
        for name, pat in BOOK_TICS.items():
            tics[name] += len(pat.findall(body))
        sents = [s.strip() for s in _SENT.findall(body) if s.strip()]
        # 开篇时间词
        head = body.lstrip()[:8]
        if any(head.startswith(w) for w in TIME_OPENERS):
            time_openers += 1
        # 章末短结尾
        if sents and util.hanzi_count(sents[-1]) <= 6:
            short_endings += 1
        # 跨章逐字复读(≥8 汉字的整句,同一句出现在多章)
        for s in set(sents):
            if util.hanzi_count(s) >= 8:
                sent_chapters.setdefault(s, set()).add(no)

    cross = {s: sorted(chs) for s, chs in sent_chapters.items() if len(chs) >= 3}
    time_rate = time_openers / n
    short_rate = short_endings / n
    filled = [t for t in titles if t]
    dup_titles = sorted({t for t in filled if filled.count(t) >= 2})
    title_issues = []
    if filled and len(filled) != n:
        title_issues.append(f"标题缺失混用:{len(filled)}/{n} 章有标题(要么都给要么都不给)")
    if dup_titles:
        title_issues.append("重复章标题:" + "、".join(dup_titles[:5]))

    findings = []
    hot_tics = {k: v for k, v in tics.items() if v / n >= 1.5}
    if hot_tics:
        top = "、".join(f"{k} 章均{v / n:.1f}" for k, v in sorted(hot_tics.items(), key=lambda x: -x[1]))
        findings.append(f"句式 tic 章均偏高:{top}(整本一个腔调,换说法)")
    if cross:
        sample = "、".join(f"「{s[:14]}…」(ch{'/'.join(map(str, chs))})" for s, chs in list(cross.items())[:3])
        findings.append(f"跨章逐字复读句 {len(cross)} 条:{sample}")
    if time_rate >= 0.4:
        findings.append(f"开篇时间词率 {time_rate:.0%}(过半用『清晨/夜里/三天后』套路转场)")
    if short_rate >= 0.5:
        findings.append(f"章末短结尾率 {short_rate:.0%}(总爱用一句短话收尾,结构同构)")
    findings += title_issues

    return {
        "chapters": n, "range": [start, last], "tics": tics,
        "cross_repeats": cross, "time_opener_rate": round(time_rate, 3),
        "short_ending_rate": round(short_rate, 3), "title_issues": title_issues,
        "findings": findings or ["全书纵向基线未见明显问题"],
    }
