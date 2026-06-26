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
import urllib.request

from . import checks, config, craft, expressions, journal, jsonloose, llm, recipes, skills, util, worldbook
from .config import SUMMARY_EVERY   # 静态默认(函数签名用)
from .entity import LocalEntity
from .lens import commit_core       # 统一写入口(落 beat + 门控沉淀 + 写回状态 + 标记透镜)
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
def _c2_inject(pkg: dict, world: World, thread: Thread, chapter_no=None) -> dict:
    """C2 注入:命名库(命名一致) + 三级大纲(本章细纲 / 卷·节点脊柱)。
    无 glossary/outline 数据时不加任何键 → 休眠,与今日写/审包逐字节一致。"""
    terms = (world.glossary() or {}).get("terms", [])
    if terms:
        pkg["glossary"] = terms
    ol = thread.outline() or {}
    spec = (ol.get("chapters") or {}).get(str(chapter_no)) if chapter_no is not None else None
    if spec:
        pkg["chapter_outline"] = spec                       # 写本章:六元细纲(目标/冲突/钩子/披露/出场/字数)
    if ol.get("volumes") or ol.get("beats"):
        pkg["outline_spine"] = {"volumes": ol.get("volumes", []), "beats": ol.get("beats", [])}
    return pkg


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
    last_tail = thread.chapter_text(nxt - 1)[-1200:] if nxt > 1 else ""
    # 世界书触发:据本章意图+上章结尾+出场角色名,激活相关设定条目
    wb_ctx = "\n".join([brief or "", last_tail, "、".join(b["name"] for b in blocks),
                        " ".join(h.get("desc", "") for h in thread.open_hooks())])
    return _c2_inject({
        "lens": "narrate",
        "thread": {"world": world.id, "id": thread.id, "title": meta.get("title"), "genre": meta.get("genre"), "scale": meta.get("scale")},
        "writing_chapter": nxt, "pacing_contract": meta.get("pacing"), "hanzi_target": meta.get("hanzi_target"),
        "thread_doc": util.read_md(thread.dir / "thread.md"),
        "world_canon": util.read_md(world.dir / "canon.md"),
        "last_summary": thread.summary(),
        "last_chapter_tail": last_tail,
        "worldbook": worldbook.scan(world, wb_ctx),   # 触发的相关世界设定
        "related_chapters": thread.related_chapters(),   # 四维相关章节反查(长篇该回看哪几章)
        "skills": skills.available_menu(),   # 可按需取的写作 skill 短目录(反套话/嗓音/事件摘要…)
        "active_entities": blocks, "craft_checklist": craft.WRITER_CHECKLIST,
        "craft_library": {   # 工艺工具箱(host agent 据此有谱地选技法)
            "hook_techniques": craft.HOOK_TECHNIQUES, "chapter_openers": craft.CHAPTER_OPENERS,
            "expansion": craft.EXPANSION_TECHNIQUES, "dialogue": craft.DIALOGUE_CRAFT,
            "suspense_curve": craft.SUSPENSE_CURVE, "hook_arcs": craft.HOOK_ARCS,
        },
        "recipe": recipes.get(meta.get("genre", "")), "intent": brief,
        "alpha": thread.hooks_data().get("alpha", ""),
        "open_hooks": [{"id": h["id"], "desc": h["desc"], "level": h["level"], "payoff_target": h.get("payoff_target")}
                       for h in thread.open_hooks()],
    }, world, thread, nxt)


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
        f"α 悬念(全书统领):{pkt.get('alpha') or '未定'}",
        "待推进的开放钩子(本章主推其一的下一层):\n" + ("\n".join(
            f"- [{h['level']}] {h['desc']}" + (f"(计划 ch{h['payoff_target']} 回收)" if h.get('payoff_target') else "")
            for h in pkt.get("open_hooks", [])) or "（暂无,可自然埋新钩)"),
        f"钩子技法库(给本章收尾择一,别同质轰炸):{craft.hook_menu()}。{craft.SUSPENSE_CURVE}",
        (f"相关世界设定(按本章上下文触发):\n{pkt['worldbook']['injection']}"
         if pkt.get("worldbook", {}).get("injection") else ""),
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
    raw = llm.generate(sys, "\n\n".join(u for u in user if u))
    return _split_chapter(raw)


def _split_chapter(raw: str) -> dict:
    title, sediments, state_updates = "", [], {}
    prose, _, tail = raw.partition(_SEP)
    if tail.strip():
        j = jsonloose.loads(tail, {})
        sediments = j.get("sediments", []) or []
        state_updates = j.get("state_updates", {}) or {}
    lines = prose.strip().splitlines()
    if lines and lines[0].lstrip().startswith("#"):
        title = lines[0].lstrip("# ").strip()
        prose = "\n".join(lines[1:]).strip()
    return {"chapter_text": prose.strip(), "title": title, "sediments": sediments, "state_updates": state_updates}


def narrate_commit(world: World, thread: Thread, payload: dict) -> dict:
    no = thread.add_chapter(payload.get("chapter_text", ""), payload.get("title", ""))
    where = f"ch:{no:03d}"
    state_updates = {eid: {**upd, "chapter": no} for eid, upd in (payload.get("state_updates") or {}).items()}
    core = commit_core(world, thread, lens="narrate", where=where,
                       beat=payload.get("beat", payload.get("title", f"第{no}章")),
                       sediments=payload.get("sediments", []) or [], state_updates=state_updates)
    if payload.get("summary"):
        thread.write_summary(payload["summary"])
    auto = checks.check_chapter(thread, no)   # 落章即自动质检(字数/去AI味/题材疲劳词)
    return {
        "chapter": no, "hanzi": auto["hanzi"],
        "hanzi_target": thread.meta().get("hanzi_target"),
        "sedimented": core["sedimented"], "skipped": core["skipped"],
        "summary_due": no % SUMMARY_EVERY == 0 and not payload.get("summary"),
        "auto_checks": auto["findings"],
    }


# ========== narrate 产线:审校 / 修订 / 反思 / 编排 ==========
def _parse_json(text: str) -> dict:
    return jsonloose.loads(text, {})


def review_prep(world: World, thread: Thread, chapter_text: str) -> dict:
    """审校包:供宿主 Agent 的审校子代理(冷面、便宜模型)独立查问题。"""
    m = thread.meta()
    return _c2_inject({
        "lens": "narrate", "role": "review",
        "thread": {"world": world.id, "id": thread.id, "title": m.get("title")},
        "chapter_text": chapter_text,
        "canon": util.read_md(world.dir / "canon.md"),
        "pacing_contract": m.get("pacing"), "recipe": recipes.get(m.get("genre", "")),
        "profile": recipes.get_profile(m.get("genre", "")),
        "rubric": craft.REVIEWER_RUBRIC, "discipline": craft.REVIEWER_DISCIPLINE,
        "consistency": craft.CONSISTENCY_CHECKS,
        "auto_checks": checks.check_text(chapter_text, genre=m.get("genre", ""), target=m.get("hanzi_target", 0)),
    }, world, thread)


def narrate_review(world: World, thread: Thread, chapter_text: str) -> dict:
    """审校:确定性质检 + (配了 LLM 则)冷面 rubric 评审。返回 verdict + findings。"""
    m = thread.meta()
    auto = checks.check_text(chapter_text, genre=m.get("genre", ""), target=m.get("hanzi_target", 0))
    findings = [{"dim": "客观", "issue": f} for f in auto["findings"] if "未见明显问题" not in f]
    # 确定性钩子审计:埋了却过期未回收的伏笔
    for h in thread.overdue_hooks():
        findings.append({"dim": "钩子", "issue": f"伏笔「{h['desc']}」计划 ch{h['payoff_target']} 回收却仍『{h['status']}』(漏收或顺延)"})
    verdict = "revise" if any(f["dim"] == "钩子" for f in findings) else "pass"
    if llm.available():
        dims = recipes.get(m.get("genre", "")).get("audit_dimensions", [])
        sys = ("你是暗宇宙的冷面审校,只挑问题、绝不改写正文。" + craft.REVIEWER_DISCIPLINE
               + " 通用 rubric:" + "；".join(craft.REVIEWER_RUBRIC)
               + ("；本题材另查:" + "；".join(dims) if dims else ""))
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
    sys = ("你是暗宇宙写手,据审校意见改稿。保持原情节走向与篇幅,只修指出的问题,去AI味。"
           "扩写处守防注水四问:" + "；".join(craft.ANTI_WATER))
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
        "alpha": thread.hooks_data().get("alpha", ""),
        "book_baseline": checks.check_book(thread),   # 全书纵向基线(确定性,喂横向裁定)
        "diagnosis": checks.reflect_diagnose(thread),   # 规则化诊断(Finding+target writer/recipe)
        "overdue_hooks": [{"id": h["id"], "desc": h["desc"], "payoff_target": h.get("payoff_target")}
                          for h in thread.overdue_hooks()],
    }


def narrate_reflect(world: World, thread: Thread, last_n: int = SUMMARY_EVERY) -> dict:
    """反思:全书纵向基线(确定性,无需 LLM)+ 横向校验全局自洽 + 找漏掉的成长(需 LLM)。"""
    base = checks.check_book(thread)
    diag = checks.reflect_diagnose(thread)
    diag_findings = [f"[{d['target']}] {d['rule']}:{d['evidence']} → {d['suggestion']}" for d in diag["findings"]]
    if not llm.available():
        return {"findings": diag_findings, "suggested_sediments": [], "book_baseline": base, "diagnosis": diag,
                "note": "横向自洽/成长建议需配 SV_PROVIDER(或用 reflect-prep 交宿主模型);规则化诊断已给。"}
    last = thread.last_chapter_no()
    chs = "\n\n".join(f"【第{n}章】\n{thread.chapter_text(n)[:1500]}" for n in range(max(1, last - last_n + 1), last + 1))
    base_hint = ("\n已知客观诊断(请据此重点核查):" + "；".join(diag_findings)) if diag_findings else ""
    sys = "你是暗宇宙的反思者,横向校验全局自洽(时间锚/战力刻度/α进度/配速),并找出写手漏掉的、达到成长时刻判据的成长。" + "；".join(craft.REFLECTOR_FOCUS)
    user = "\n\n".join([
        f"成长时刻判据:{craft.GROWTH_TRIGGERS}",
        f"canon:\n{util.read_md(world.dir / 'canon.md')[:1200]}",
        f"最近章节:\n{chs}{base_hint}",
        '输出 JSON:{"findings":["全局自洽问题…"],"suggested_sediments":[{"entity":"角色id","text":"该补的成长","level":"身份"}]}。',
    ])
    j = _parse_json(llm.generate(sys, user, max_tokens=1500, temperature=0.4))
    findings = diag_findings + [f for f in (j.get("findings", []) or [])]
    return {"findings": findings, "suggested_sediments": j.get("suggested_sediments", []) or [],
            "book_baseline": base, "diagnosis": diag}


def narrate_run(world: World, thread: Thread, *, intent: str = "", focus=None,
                review: bool = True, max_revisions: int = 1, commit: bool = True) -> dict:
    """AIGC 写章产线编排:写手 → 审校 →(修订)→ 落章。返回全过程 trace。

    单机(配 LLM):全自动。stub:产出占位草稿 + 确定性审校 + 落盘(无修订)。
    """
    jr = journal.open_run(thread)   # 产线审计日志(可审计/可重放)
    jr.append("start", intent=intent, focus=focus)
    draft = narrate_generate(world, thread, focus=focus, intent=intent)
    text = draft["chapter_text"]
    trace = {"run_id": jr.path.stem, "title": draft["title"], "draft_hanzi": util.hanzi_count(text),
             "reviews": [], "revisions": 0, "sediments": draft["sediments"]}
    jr.append("draft", title=draft["title"], hanzi=trace["draft_hanzi"])
    if review:
        for i in range(max_revisions + 1):
            rev = narrate_review(world, thread, text)
            trace["reviews"].append(rev)
            jr.append("review", verdict=rev["verdict"], findings=len(rev.get("findings", [])))
            if rev["verdict"] == "pass" or not llm.available() or i == max_revisions:
                break
            text = narrate_revise(world, thread, text, rev["findings"])
            trace["revisions"] += 1
            jr.append("revise", round=trace["revisions"], hanzi=util.hanzi_count(text))
    if commit:
        trace["receipt"] = narrate_commit(world, thread, {
            "chapter_text": text, "title": draft["title"],
            "sediments": draft["sediments"], "state_updates": draft["state_updates"]})
        jr.append("commit", chapter=trace["receipt"].get("chapter"), hanzi=trace["receipt"].get("hanzi"))
    else:
        trace["chapter_text"] = text
    jr.append("finish", committed=commit, revisions=trace["revisions"])
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
            "protocol": craft.PLAY_PROTOCOL, "self_check": craft.OUTPUT_SELF_CHECK,
            "var_protocol": craft.VAR_UPDATE_PROTOCOL,
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
    commit_core(world, thread, lens="play", where=f"play:{sid}",
                beat=f"小剧场 {sid}:{payload.get('scene','')}", mark=True)   # 时间线写入走统一入口
    return {"session": sid, "written_back": written, "candidates": candidates, "skipped": skipped}


def _next_session(thread: Thread) -> str:
    d = thread.sessions_dir
    n = (len(list(d.glob("session-*.md"))) + 1) if d.exists() else 1
    return f"session-{n:03d}"


# ========== simulate(模拟 / 自演化)—— 能力已建,默认关 ==========
def simulate_prep(world: World, thread: Thread) -> dict:
    if not config.SIMULATE_ENABLED:
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
    if not config.SIMULATE_ENABLED:
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
def render_available() -> bool:
    return config.RENDER == "gitee" and bool(config.GITEE_API_KEY)


def render_prep(world: World, subject: str, *, appearance: str = "") -> dict:
    prompt = (appearance + ", " if appearance else "") + subject
    return {"lens": "render", "provider": config.RENDER, "enabled": render_available(),
            "image_prompt": prompt,
            "note": "据此出图(Gitee z-image-turbo,~18s);未配 SV_RENDER=gitee + GITEE_API_KEY 则休眠。"}


def _gen_image(prompt: str, *, seed: int | None = None) -> bytes:
    """调 Gitee z-image 出图,带空白图重试(满分辨率却 <60KB 多为过滤空图,同 Doll)。

    seed 固定 → 同一人换表情时锁脸(立绘表情切换的关键)。
    """
    raw = b""
    payload = {"model": config.IMAGE_MODEL, "prompt": prompt, "size": config.IMAGE_SIZE,
               "num_inference_steps": config.IMAGE_STEPS}
    if seed is not None:
        payload["seed"] = seed
    body = json.dumps(payload).encode("utf-8")
    for _ in range(3):
        req = urllib.request.Request(f"{config.GITEE_BASE_URL}/images/generations", data=body,
                                     headers={"Authorization": f"Bearer {config.GITEE_API_KEY}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode("utf-8"))
        item = (data.get("data") or [{}])[0]
        raw = base64.b64decode(item["b64_json"]) if item.get("b64_json") else urllib.request.urlopen(item["url"], timeout=60).read()
        if len(raw) >= 60_000:
            break
    return raw


def _save_image(dirpath, raw: bytes, stem: str):
    n = len(list(dirpath.glob("*.png"))) + 1 if dirpath.exists() else 1
    out = dirpath / f"{stem}-{n:03d}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
    return out


def render_scene(world: World, thread: Thread, subject: str, *, appearance: str = "") -> dict:
    """生成一张场景图,存到线的 renders/。"""
    if not render_available():
        return {"enabled": False, "note": "多模态渲染未启用:在 sv.conf 设 SV_RENDER=gitee + GITEE_API_KEY。"}
    prompt = (appearance + ", " if appearance else "") + subject
    raw = _gen_image(prompt)
    out = _save_image(thread.renders_dir, raw, "scene")
    thread.mark_lens("render")
    return {"enabled": True, "file": out.name, "bytes": len(raw), "prompt": prompt,
            "rel": f"worlds/{world.id}/threads/{thread.id}/renders/{out.name}"}


def render_entity(world: World, entity, scene: str = "") -> dict:
    """生成一张角色立绘,用实体固定 appearance 锁脸,存到实体 portraits/。entity=LocalEntity。"""
    if not render_available():
        return {"enabled": False, "note": "多模态渲染未启用:在 sv.conf 设 SV_RENDER=gitee + GITEE_API_KEY。"}
    base = entity.appearance or entity.card().get("name", entity.id)
    prompt = base + (", " + scene if scene else ", character portrait")
    raw = _gen_image(prompt)
    out = _save_image(entity.dir / "portraits", raw, "portrait")
    return {"enabled": True, "file": out.name, "bytes": len(raw), "prompt": prompt,
            "rel": f"worlds/{world.id}/entities/{entity.id}/portraits/{out.name}"}


def render_commit(world: World, thread: Thread, subject: str, *, appearance: str = "") -> dict:
    """向后兼容旧命令名 → render_scene。"""
    return render_scene(world, thread, subject, appearance=appearance)


# ========== 立绘表情切换(锁脸预生成一组情绪立绘)==========
def render_expressions(world: World, entity, emotions=None, *, seed: int | None = None) -> dict:
    """为实体预生成一组锁脸表情立绘 → entities/<id>/portraits/<emotion>.png(文件名=情绪标签)。

    同一 appearance + 同一 seed 锁脸,只换情绪子句。seed 存进 card.appearance_seed,后续补图复用。
    """
    if not render_available():
        return {"enabled": False, "note": "多模态渲染未启用:在 sv.conf 设 SV_RENDER=gitee + GITEE_API_KEY。"}
    card = entity.card()
    seed = seed if seed is not None else card.get("appearance_seed")
    if seed is None:
        seed = (abs(hash(entity.id)) % 2_000_000_000) + 1   # 确定性 seed(避免 Math.random,可复现)
    entity.set_card_field("appearance_seed", seed)
    base = entity.appearance or card.get("name", entity.id)
    emos = emotions or expressions.EMOTIONS_CORE
    pdir = entity.dir / "portraits"
    out = {}
    for emo in emos:
        prompt = (f"{base}, {expressions.emotion_clause(emo)}, same character, consistent face, "
                  "upper body portrait, plain background")
        raw = _gen_image(prompt, seed=seed)
        (pdir).mkdir(parents=True, exist_ok=True)
        (pdir / f"{emo}.png").write_bytes(raw)
        out[emo] = f"worlds/{world.id}/entities/{entity.id}/portraits/{emo}.png"
    return {"enabled": True, "seed": seed, "emotions": list(out), "sprites": out}


def expression_sprites(world: World, entity) -> dict:
    """列出该实体已生成的表情立绘(emotion→相对路径),供前端切换/分类限定 label。"""
    pdir = entity.dir / "portraits"
    out = {}
    if pdir.exists():
        for p in sorted(pdir.glob("*.png")):
            if p.stem in expressions.EMOTION_PROMPT:
                out[p.stem] = f"worlds/{world.id}/entities/{entity.id}/portraits/{p.stem}.png"
    return out


def classify_reply_emotion(world: World, entity, text: str) -> dict:
    """对一段回复分类情绪,只在该实体已生成的表情里选;返回 {emotion, sprite}。"""
    sprites = expression_sprites(world, entity)
    labels = list(sprites) or expressions.EMOTIONS_CORE
    emo = expressions.classify_emotion(text, labels)
    return {"emotion": emo, "sprite": sprites.get(emo), "zh": expressions.EMOTION_ZH.get(emo, emo)}
