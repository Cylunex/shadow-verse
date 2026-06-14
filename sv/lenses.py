"""L3 · 体验透镜(可插拔)—— 同一条线可被多种方式体验,共享同一基质。

- narrate(读):长篇叙事(小说)。prep 组装写作包 → 宿主写 → commit 落章 + 沉淀。
- play(玩):介入式 RP。prep 场景包 → 互动 → commit 落 session + 条件成长写回。
- simulate(模拟·自演化):实体自主行动/世界呼吸。能力已建,默认关(SV_SIMULATE)。
- render(可视化·多模态):从实体/场景描述生成图像。可插拔,未配则休眠(零依赖 urllib,同 Doll)。

无论哪个透镜,发生的事都落进 thread.beats(跨透镜时间线)+ 触动的实体记忆(核心循环铁律)。
"""
from __future__ import annotations

import base64
import json
import re
import urllib.request

from . import checks, craft, llm, recipes, util
from .config import (
    GITEE_API_KEY, GITEE_BASE_URL, IMAGE_MODEL, IMAGE_SIZE, IMAGE_STEPS,
    RENDER, SIMULATE_ENABLED, SUMMARY_EVERY,
)
from .entity import LocalEntity
from .thread import Thread
from .world import World


def _active(world: World, ids):
    out = []
    for eid in (ids or world.list_entities()):
        e = LocalEntity(world, eid)
        if e.exists():
            out.append(e)
    return out


# ========== narrate(读 / 小说)==========
def narrate_prep(world: World, thread: Thread, *, focus=None, brief: str = "") -> dict:
    meta = thread.meta()
    nxt = thread.last_chapter_no() + 1
    blocks = []
    for e in _active(world, focus):
        rb = e.rebuild()
        q = brief or rb["state"].get("goal", "") or e.card().get("name", "")
        blocks.append({
            "id": e.id, "name": e.card().get("name", e.id), "role": e.role,
            "state": rb["state"], "anchors": rb["anchors"],
            "recent": [x["text"] for x in rb["recent"]],
            "recalled": [x["text"] for x in e.retrieve(q)],
        })
    return {
        "lens": "narrate",
        "thread": {"world": world.id, "id": thread.id, "title": meta.get("title"), "genre": meta.get("genre"), "scale": meta.get("scale")},
        "writing_chapter": nxt, "pacing_contract": meta.get("pacing"), "hanzi_target": meta.get("hanzi_target"),
        "thread_doc": util.read_md(thread.dir / "thread.md"),
        "world_canon": util.read_md(world.dir / "canon.md"),
        "last_summary": thread.summary(),
        "last_chapter_tail": thread.chapter_text(nxt - 1)[-1200:] if nxt > 1 else "",
        "active_entities": blocks, "craft_checklist": craft.WRITER_CHECKLIST,
        "recipe": recipes.get(meta.get("genre", "")), "intent": brief,
    }


_SEP = "===沉淀==="


def narrate_generate(world: World, thread: Thread, *, focus=None, intent: str = "") -> dict:
    """AIGC 写下一章:据写作包让 LLM 写正文 + 结构化沉淀。返回供人审后 narrate_commit。"""
    pkt = narrate_prep(world, thread, focus=focus, brief=intent)
    rec = pkt["recipe"]
    sys = ("你是暗宇宙的写手,文笔克制有画面、去AI味。守:" + "；".join(craft.WRITER_CHECKLIST))
    ents = pkt["active_entities"]
    user = [
        f"为《{pkt['thread']['title']}》写第 {pkt['writing_chapter']} 章。题材:{pkt['thread']['genre']}。",
        f"节奏契约:{pkt['pacing_contract']}",
        f"题材配方——爽点:{rec.get('climax')};慎用疲劳词:{('、'.join(rec.get('forbidden', [])) or '无')}",
        f"目标字数(纯汉字):约 {pkt['hanzi_target']}",
        f"本章意图:{intent or '顺势推进一条主线钩子'}",
        f"上章结尾:\n{pkt['last_chapter_tail'] or '(开篇)'}",
        "出场角色(状态/锚点/该想起):\n" + "\n".join(
            f"- {e['name']}[{e['role']}] 此刻{json.dumps(e['state'], ensure_ascii=False)};锚点:{'、'.join(e['anchors'])};该想起:{'/'.join(e['recalled']) or '—'}"
            for e in ents),
        "输出格式:先写章标题(单独一行,以『# 』开头),再写正文;"
        f"全部正文写完后另起一行写 `{_SEP}`,其下输出一个 JSON:"
        '{"sediments":[{"entity":"id","text":"这章他经历/留下什么","level":"瞬时|持久|身份"}],'
        '"state_updates":{"id":{"location":"","mood":"","goal":""}}}。'
        "sediments 只给主/次角(客串不写);没有就给空数组。",
    ]
    raw = llm.generate(sys, "\n\n".join(user))
    return _split_chapter(raw)


def _split_chapter(raw: str) -> dict:
    title, sediments, state_updates = "", [], {}
    prose, _, tail = raw.partition(_SEP)
    if tail.strip():
        try:
            m = re.search(r"\{.*\}", tail, re.S)
            j = json.loads(m.group(0)) if m else {}
            sediments = j.get("sediments", []) or []
            state_updates = j.get("state_updates", {}) or {}
        except Exception:
            pass
    lines = prose.strip().splitlines()
    if lines and lines[0].lstrip().startswith("#"):
        title = lines[0].lstrip("# ").strip()
        prose = "\n".join(lines[1:]).strip()
    return {"chapter_text": prose.strip(), "title": title, "sediments": sediments, "state_updates": state_updates}


def narrate_commit(world: World, thread: Thread, payload: dict) -> dict:
    no = thread.add_chapter(payload.get("chapter_text", ""), payload.get("title", ""))
    where = f"ch:{no:03d}"
    sedimented, skipped = [], []
    for s in payload.get("sediments", []) or []:
        e = LocalEntity(world, s.get("entity"))
        if not e.exists():
            skipped.append({"entity": s.get("entity"), "why": "实体不存在"}); continue
        ent = e.sediment(s.get("text", ""), level=s.get("level", "持久"), where=where, trace=s.get("trace", ""), tags=s.get("tags", []))
        if ent is None:
            skipped.append({"entity": e.id, "why": f"role={e.role} 不写回"})
        else:
            sedimented.append({"entity": e.id, "id": ent["id"], "level": ent["level"]})
    for eid, upd in (payload.get("state_updates") or {}).items():
        e = LocalEntity(world, eid)
        if e.exists():
            upd = dict(upd); upd["chapter"] = no; e.update_state(upd)
    thread.add_beat(payload.get("beat", payload.get("title", f"第{no}章")), lens="narrate", where=where)
    if payload.get("summary"):
        thread.write_summary(payload["summary"])
    auto = checks.check_chapter(thread, no)   # 落章即自动质检(字数/去AI味/题材疲劳词)
    return {
        "chapter": no, "hanzi": auto["hanzi"],
        "hanzi_target": thread.meta().get("hanzi_target"),
        "sedimented": sedimented, "skipped": skipped,
        "summary_due": no % SUMMARY_EVERY == 0 and not payload.get("summary"),
        "auto_checks": auto["findings"],
    }


# ========== narrate 产线:审校 / 修订 / 反思 / 编排 ==========
def _parse_json(text: str) -> dict:
    try:
        m = re.search(r"\{.*\}", text, re.S)
        return json.loads(m.group(0)) if m else {}
    except Exception:
        return {}


def review_prep(world: World, thread: Thread, chapter_text: str) -> dict:
    """审校包:供宿主 Agent 的审校子代理(冷面、便宜模型)独立查问题。"""
    m = thread.meta()
    return {
        "lens": "narrate", "role": "review",
        "thread": {"world": world.id, "id": thread.id, "title": m.get("title")},
        "chapter_text": chapter_text,
        "canon": util.read_md(world.dir / "canon.md"),
        "pacing_contract": m.get("pacing"), "recipe": recipes.get(m.get("genre", "")),
        "rubric": craft.REVIEWER_RUBRIC,
        "auto_checks": checks.check_text(chapter_text, genre=m.get("genre", ""), target=m.get("hanzi_target", 0)),
    }


def narrate_review(world: World, thread: Thread, chapter_text: str) -> dict:
    """审校:确定性质检 + (配了 LLM 则)冷面 rubric 评审。返回 verdict + findings。"""
    m = thread.meta()
    auto = checks.check_text(chapter_text, genre=m.get("genre", ""), target=m.get("hanzi_target", 0))
    findings = [{"dim": "客观", "issue": f} for f in auto["findings"] if "未见明显问题" not in f]
    verdict = "pass"
    if llm.available():
        sys = "你是暗宇宙的冷面审校,只挑问题、绝不改写正文。" + "；".join(craft.REVIEWER_RUBRIC)
        user = "\n\n".join([
            f"题材:{m.get('genre')};节奏契约:{m.get('pacing')}",
            f"canon 硬事实:\n{util.read_md(world.dir / 'canon.md')[:1500]}",
            f"待审正文:\n{chapter_text}",
            '按 rubric 找问题。输出 JSON:{"verdict":"pass"或"revise","findings":[{"dim":"OOC/连续性/钩子/去AI味/节奏","issue":"具体问题"}]}。没问题就 verdict=pass、findings 空数组。',
        ])
        j = _parse_json(llm.generate(sys, user, max_tokens=1200, temperature=0.3))
        for f in j.get("findings", []) or []:
            findings.append({"dim": f.get("dim", "审校"), "issue": f.get("issue", "")})
        verdict = j.get("verdict", "pass")
    return {"verdict": verdict, "findings": findings, "auto_checks": auto["findings"]}


def narrate_revise(world: World, thread: Thread, chapter_text: str, findings: list) -> str:
    """据审校意见改稿(需 LLM)。保持情节与篇幅,只修问题。返回修订后正文。"""
    issues = "；".join(f.get("issue", "") for f in findings if f.get("issue"))
    sys = "你是暗宇宙写手,据审校意见改稿。保持原情节走向与篇幅,只修指出的问题,去AI味。"
    user = f"原正文:\n{chapter_text}\n\n审校意见:{issues}\n\n输出修订后的完整正文(只正文,不要任何解释)。"
    return llm.generate(sys, user).strip()


def reflect_prep(world: World, thread: Thread, last_n: int = SUMMARY_EVERY) -> dict:
    """反思包:供反思子代理横向校验最近 N 章全局自洽 + 找漏掉的成长。"""
    last = thread.last_chapter_no()
    chapters = {n: thread.chapter_text(n) for n in range(max(1, last - last_n + 1), last + 1)}
    return {
        "lens": "narrate", "role": "reflect",
        "thread": {"world": world.id, "id": thread.id},
        "chapters": chapters, "summary": thread.summary(),
        "canon": util.read_md(world.dir / "canon.md"),
        "focus": craft.REFLECTOR_FOCUS, "growth_triggers": craft.GROWTH_TRIGGERS,
    }


def narrate_reflect(world: World, thread: Thread, last_n: int = SUMMARY_EVERY) -> dict:
    """反思:横向校验最近数章全局自洽 + 提出写手漏掉的成长沉淀建议(需 LLM)。"""
    if not llm.available():
        return {"findings": [], "suggested_sediments": [], "note": "反思需配 SV_PROVIDER(或用 reflect-prep 交宿主模型)。"}
    last = thread.last_chapter_no()
    chs = "\n\n".join(f"【第{n}章】\n{thread.chapter_text(n)[:1500]}" for n in range(max(1, last - last_n + 1), last + 1))
    sys = "你是暗宇宙的反思者,横向校验全局自洽(时间锚/战力刻度/α进度/配速),并找出写手漏掉的、达到成长时刻判据的成长。" + "；".join(craft.REFLECTOR_FOCUS)
    user = "\n\n".join([
        f"成长时刻判据:{craft.GROWTH_TRIGGERS}",
        f"canon:\n{util.read_md(world.dir / 'canon.md')[:1200]}",
        f"最近章节:\n{chs}",
        '输出 JSON:{"findings":["全局自洽问题…"],"suggested_sediments":[{"entity":"角色id","text":"该补的成长","level":"身份"}]}。',
    ])
    j = _parse_json(llm.generate(sys, user, max_tokens=1500, temperature=0.4))
    return {"findings": j.get("findings", []) or [], "suggested_sediments": j.get("suggested_sediments", []) or []}


def narrate_run(world: World, thread: Thread, *, intent: str = "", focus=None,
                review: bool = True, max_revisions: int = 1, commit: bool = True) -> dict:
    """AIGC 写章产线编排:写手 → 审校 →(修订)→ 落章。返回全过程 trace。

    单机(配 LLM):全自动。stub:产出占位草稿 + 确定性审校 + 落盘(无修订)。
    """
    draft = narrate_generate(world, thread, focus=focus, intent=intent)
    text = draft["chapter_text"]
    trace = {"title": draft["title"], "draft_hanzi": util.hanzi_count(text),
             "reviews": [], "revisions": 0, "sediments": draft["sediments"]}
    if review:
        for i in range(max_revisions + 1):
            rev = narrate_review(world, thread, text)
            trace["reviews"].append(rev)
            if rev["verdict"] == "pass" or not llm.available() or i == max_revisions:
                break
            text = narrate_revise(world, thread, text, rev["findings"])
            trace["revisions"] += 1
    if commit:
        trace["receipt"] = narrate_commit(world, thread, {
            "chapter_text": text, "title": draft["title"],
            "sediments": draft["sediments"], "state_updates": draft["state_updates"]})
    else:
        trace["chapter_text"] = text
    return trace


# ========== play(玩 / RP)==========
def play_prep(world: World, thread: Thread, scene: str, entity_ids) -> dict:
    blocks = []
    for e in _active(world, entity_ids):
        rb = e.rebuild()
        blocks.append({"id": e.id, "name": e.card().get("name", e.id), "role": e.role,
                       "state": rb["state"], "anchors": rb["anchors"],
                       "recalled": [x["text"] for x in e.retrieve(scene)]})
    return {"lens": "play", "thread": {"world": world.id, "id": thread.id},
            "scene": scene, "scale": thread.meta().get("scale"),
            "active_entities": blocks, "growth_triggers": craft.GROWTH_TRIGGERS,
            "note": "平行可能性,默认不动小说 canon;仅触发成长时刻才回写实体记忆。"}


def play_commit(world: World, thread: Thread, payload: dict) -> dict:
    sid = payload.get("session") or _next_session(thread)
    written, candidates, skipped = [], [], []
    for g in payload.get("growth", []) or []:
        e = LocalEntity(world, g.get("entity"))
        if not e.exists():
            skipped.append({"entity": g.get("entity"), "why": "实体不存在"}); continue
        if not g.get("trigger"):
            candidates.append({"entity": e.id, "text": g.get("text", "")}); continue
        ent = e.sediment(g.get("text", ""), level="身份", where=f"play:{sid}", trace=g.get("trace", ""))
        skipped.append({"entity": e.id, "why": f"role={e.role} 不写回"}) if ent is None else written.append({"entity": e.id, "id": ent["id"]})
    md = [f"# 小剧场 · {sid}", "", f"> 场景:{payload.get('scene','')}", "", payload.get("transcript", "").strip()]
    if candidates:
        md += ["", "## 成长苗头候选(待拍板,未写回)"] + [f"- [{c['entity']}] {c['text']}" for c in candidates]
    util.write_md(thread.sessions_dir / f"{sid}.md", "\n".join(md))
    thread.add_beat(f"小剧场 {sid}:{payload.get('scene','')}", lens="play", where=f"play:{sid}")
    thread.mark_lens("play")
    return {"session": sid, "written_back": written, "candidates": candidates, "skipped": skipped}


def _next_session(thread: Thread) -> str:
    d = thread.sessions_dir
    n = (len(list(d.glob("session-*.md"))) + 1) if d.exists() else 1
    return f"session-{n:03d}"


# ========== simulate(模拟 / 自演化)—— 能力已建,默认关 ==========
def simulate_prep(world: World, thread: Thread) -> dict:
    if not SIMULATE_ENABLED:
        return {"lens": "simulate", "enabled": False,
                "note": "自演化默认关闭(SV_SIMULATE=off)。开启后:世界 pulse 推进 + 实体按欲望自主行动,生成下一个 beat。"}
    blocks = []
    for e in _active(world, None):
        rb = e.rebuild()
        blocks.append({"id": e.id, "name": e.card().get("name", e.id), "state": rb["state"],
                       "desire_hint": rb["anchors"], "recent": [x["text"] for x in rb["recent"]]})
    return {"lens": "simulate", "enabled": True, "thread": {"world": world.id, "id": thread.id},
            "world_pulse": util.read_md(world.dir / "pulse.md"),
            "recent_beats": [b["text"] for b in thread.beats()[-8:]],
            "autonomous_entities": blocks,
            "note": "据各实体欲望生成它们的下一步自主行动(beat);触发成长时刻则沉淀。"}


def simulate_commit(world: World, thread: Thread, payload: dict) -> dict:
    if not SIMULATE_ENABLED:
        return {"enabled": False, "note": "自演化未开启,不落盘。"}
    written = []
    for b in payload.get("beats", []) or []:
        beat = thread.add_beat(b.get("text", ""), lens="simulate", where="sim")
        eid = b.get("entity")
        if eid:
            e = LocalEntity(world, eid)
            if e.exists() and b.get("sediment"):
                e.sediment(b["text"], level=b.get("level", "持久"), where=f"beat:{beat['id']}")
        written.append(beat["id"])
    return {"enabled": True, "beats": written}


# ========== render(可视化 / 多模态)—— 可插拔,未配则休眠 ==========
def render_prep(world: World, subject: str, *, appearance: str = "") -> dict:
    prompt = (appearance + ", " if appearance else "") + subject
    return {"lens": "render", "provider": RENDER,
            "enabled": RENDER != "none" and bool(GITEE_API_KEY),
            "image_prompt": prompt,
            "note": "render-commit 据此出图(Gitee z-image-turbo,~18s);未配 GITEE_API_KEY 则休眠。"}


def render_commit(world: World, thread: Thread, subject: str, *, appearance: str = "") -> dict:
    if RENDER != "gitee" or not GITEE_API_KEY:
        return {"enabled": False, "note": "多模态渲染未启用:在 sv.conf 设 SV_RENDER=gitee + GITEE_API_KEY。"}
    prompt = (appearance + ", " if appearance else "") + subject
    body = json.dumps({"model": IMAGE_MODEL, "prompt": prompt, "size": IMAGE_SIZE,
                       "num_inference_steps": IMAGE_STEPS}).encode("utf-8")
    req = urllib.request.Request(f"{GITEE_BASE_URL}/images/generations", data=body,
                                 headers={"Authorization": f"Bearer {GITEE_API_KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8"))
    item = (data.get("data") or [{}])[0]
    raw = base64.b64decode(item["b64_json"]) if item.get("b64_json") else urllib.request.urlopen(item["url"], timeout=60).read()
    n = len(list(thread.renders_dir.glob("*.png"))) + 1 if thread.renders_dir.exists() else 1
    out = thread.renders_dir / f"render-{n:03d}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
    thread.mark_lens("render")
    return {"enabled": True, "file": str(out), "bytes": len(raw), "prompt": prompt}
