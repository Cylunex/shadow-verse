"""skill_api —— 宿主 Agent 调用的 CLI 入口(Model A · AIGC 多元宇宙)。

prep 输出 JSON 包(供子代理消费);commit 读 stdin JSON、落盘、回执;authoring/查询输出可读文本。
写作/生成智力在宿主模型,引擎只取料、组装、落盘、连接。

用法:python -m sv.skill_api <命令> ...   (Windows 建议 PYTHONUTF8=1)
"""
from __future__ import annotations

import argparse
import json
import sys

from . import checks, codex, export, forge, importer, lenses, llm, nexus, recipes, worldbook
from .config import NEXUS_DIR, UNIVERSE
from .entity import LocalEntity
from .nexus import NexusEntity
from .thread import Thread
from .world import World

try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass


def _out(o):
    print(json.dumps(o, ensure_ascii=False, indent=2))


def _in() -> dict:
    d = sys.stdin.read()
    return json.loads(d) if d.strip() else {}


def _csv(s):
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def _wt(world_id, thread_id):
    w = World.load(world_id)
    return w, Thread.load(w, thread_id)


# ---------- 元件库(L0)----------
def cmd_codex_add(a):
    r = codex.add(a.category, a.id, a.summary, tags=_csv(a.tags), body=a.body)
    print(f"✓ 元件入库:[{r['category']}] {r['id']} ｜ 标签 {', '.join(r['tags']) or '—'}")


def cmd_codex_seed(a):
    r = codex.seed_starter()
    print(f"✓ 起始元件库:新增 {r['added']},跳过 {r['skipped']}(已存在),现共 {r['total']} 个")


def cmd_components_seed(a):
    from . import components
    r = components.seed_all()
    print(f"✓ 创作组件库:新增 {r['added']} 组,共 {r['total']} 组 → universe/components/(工艺/配方,缺省回退种子)")


def cmd_codex_list(a):
    els = codex.all_elements()
    print(f"元件库 · {len(els)} 个:")
    for e in els:
        print(f"  · [{e['category']}] {e['id']} — {e['summary'][:40]}")


def cmd_codex_pick(a):
    _out(codex.pick(a.query, category=a.category, tags=_csv(a.tags)))


# ---------- 锻造器(L1 · AIGC)----------
def cmd_world_prep(a):
    _out(forge.world_prep(a.prompt, tags=_csv(a.tags), genre=a.genre))


def cmd_gen_world(a):
    print(forge.generate_world_body(a.prompt, genre=a.genre, tags=_csv(a.tags)))


def cmd_gen_entity(a):
    print(forge.generate_entity_body(World.load(a.world), a.prompt, role=a.role))


def cmd_gen_thread(a):
    print(forge.generate_thread_body(World.load(a.world), a.prompt))


def cmd_gen_chapter(a):
    w, t = _wt(a.world, a.thread)
    _out(lenses.narrate_generate(w, t, intent=a.intent))


def cmd_narrate_run(a):
    w, t = _wt(a.world, a.thread)
    _out(lenses.narrate_run(w, t, intent=a.intent, commit=not a.no_commit, max_revisions=a.max_rev))


def cmd_review_prep(a):
    w, t = _wt(a.world, a.thread)
    _out(lenses.review_prep(w, t, t.chapter_text(a.chapter)))


def cmd_narrate_review(a):
    w, t = _wt(a.world, a.thread)
    _out(lenses.narrate_review(w, t, t.chapter_text(a.chapter)))


def cmd_reflect_prep(a):
    w, t = _wt(a.world, a.thread)
    _out(lenses.reflect_prep(w, t, a.last))


def cmd_narrate_reflect(a):
    w, t = _wt(a.world, a.thread)
    _out(lenses.narrate_reflect(w, t, a.last))


def cmd_recipes(a):
    if a.genre:
        _out(recipes.get(a.genre))
    else:
        print("题材配方:" + " / ".join(recipes.genres()))
        print("查看某题材:python -m sv.skill_api recipes --genre 无限流")


def cmd_world_commit(a):
    p = _in()
    _out(forge.world_commit(p["id"], p.get("name", p["id"]), p.get("body", ""),
                            genre=p.get("genre", ""), scale=p.get("scale", "max"),
                            prompt=p.get("prompt", ""), from_codex=p.get("from_codex")))


def cmd_entity_prep(a):
    _out(forge.entity_prep(World.load(a.world), a.prompt, tags=_csv(a.tags)))


def cmd_card_prep(a):
    _out(forge.card_prep(a.concept, genre=a.genre or "", tags=_csv(a.tags)))


def cmd_worldbook_prep(a):
    _out(forge.worldbook_prep(a.concept, genre=a.genre or ""))


def cmd_gen_card(a):
    _out(forge.gen_card(a.concept, genre=a.genre or "", tags=_csv(a.tags)))


def cmd_entity_commit(a):
    p = _in(); w = World.load(a.world)
    _out(forge.entity_commit(w, p["id"], p.get("name", p["id"]), p.get("body", ""),
                             role=p.get("role", "secondary"), prompt=p.get("prompt", ""), from_codex=p.get("from_codex")))


def cmd_thread_prep(a):
    _out(forge.thread_prep(World.load(a.world), a.prompt, tags=_csv(a.tags)))


def cmd_thread_commit(a):
    p = _in(); w = World.load(a.world)
    _out(forge.thread_commit(w, p["id"], p.get("title", p["id"]), p.get("body", ""),
                             genre=p.get("genre", ""), pacing=p.get("pacing", "每章至少推进一条主线钩子"), prompt=p.get("prompt", "")))


# ---------- 手建(非 AIGC)----------
def _read_card(path):
    """返回 (card, png_bytes_or_None)。PNG 卡的原图用作头像。"""
    from pathlib import Path
    raw = Path(path).read_bytes()
    is_png = path.lower().endswith(".png")
    return importer.parse_card(raw if is_png else raw.decode("utf-8")), (raw if is_png else None)


def cmd_import_card(a):
    card, png = _read_card(a.path)
    r = importer.import_card(World.load(a.world), card, role=a.role, as_id=getattr(a, "as", None), avatar_png=png)
    print(f"✓ 导入角色:{r['name']} → {a.world}/{r['entity']}(世界书 {r['lorebook_entries']} 条{'，含头像' if r.get('avatar') else ''})")


def cmd_import_card_world(a):
    card, png = _read_card(a.path)
    r = importer.import_card_new_world(card, world_id=a.world_id or None,
                                       world_name=a.world_name or None, role=a.role, avatar_png=png)
    print(f"✓ 卡建独立世界:{r['world_name']}({r['world']}),角色 {r['entity']}(世界书 {r['lorebook_entries']} 条{'，含头像' if r.get('avatar') else ''})")


def cmd_import_preset(a):
    from pathlib import Path
    raw = Path(a.path).read_text(encoding="utf-8")
    name = a.name or Path(a.path).stem
    r = importer.import_preset(raw, name=name, pid=a.id or None)
    print(f"✓ 导入预设:{r['name']}({r['preset']})— 模块 {r['module_count']}(自定义 {r['custom_count']})、采样参数 {len(r['sampling'])} 项")


def cmd_import_regex(a):
    from pathlib import Path
    raw = Path(a.path).read_text(encoding="utf-8")
    name = a.name or Path(a.path).stem
    r = importer.import_regex(raw, name=name)
    print(f"✓ 导入正则:{r['regex']}({r['count']} 条:{'、'.join(r['names'][:3])})")


def cmd_presets(a):
    _out({"presets": importer.list_presets(), "regex": importer.list_regex()})


def cmd_undo_import(a):
    importer.undo_import(World.load(a.world), a.entity)
    print(f"✓ 已撤销导入:{a.world}/{a.entity}(删实体 + 剥世界书)")


def cmd_merge_world(a):
    from . import merge
    r = merge.merge_world(a.src, a.dst, delete_src=not a.keep_src)
    print(f"✓ 融合:{a.src} → {a.dst}(实体 {len(r['moved_entities'])},线 {len(r['moved_threads'])},{'删源' if r['deleted_src'] else '留源'})")


def cmd_new_world(a):
    w = World.create(a.id, a.name or a.id, genre=a.genre, scale=a.scale)
    print(f"✓ 世界已建:{w.id}  →  {w.dir / 'world.md'}")


def cmd_new_entity(a):
    e = LocalEntity.create(World.load(a.world), a.id, a.name or a.id, role=a.role)
    print(f"✓ 实体已建:{e.id}(role={e.role}{'·会成长' if e.grows() else '·不写回'})  →  {e.dir / 'profile.md'}")


def cmd_new_thread(a):
    t = Thread.create(World.load(a.world), a.id, a.title or a.id, genre=a.genre, pacing=a.pacing)
    print(f"✓ 线已建:{a.world}/{t.id}  →  {t.dir / 'thread.md'}")


# ---------- 透镜(L3)----------
def cmd_narrate_prep(a):
    w, t = _wt(a.world, a.thread)
    _out(lenses.narrate_prep(w, t, focus=_csv(a.focus) or None, brief=a.intent or ""))


def cmd_narrate_commit(a):
    w, t = _wt(a.world, a.thread)
    _out(lenses.narrate_commit(w, t, _in()))


def cmd_play_prep(a):
    w, t = _wt(a.world, a.thread)
    _out(lenses.play_prep(w, t, a.scene or "", _csv(a.entities)))


def cmd_play_commit(a):
    w, t = _wt(a.world, a.thread)
    _out(lenses.play_commit(w, t, _in()))


def cmd_simulate_prep(a):
    w, t = _wt(a.world, a.thread)
    _out(lenses.simulate_prep(w, t))


def cmd_simulate_commit(a):
    w, t = _wt(a.world, a.thread)
    _out(lenses.simulate_commit(w, t, _in()))


def cmd_render_prep(a):
    _out(lenses.render_prep(World.load(a.world), a.subject or "", appearance=a.appearance or ""))


def cmd_render_entity(a):
    from .entity import LocalEntity
    w = World.load(a.world)
    _out(lenses.render_entity(w, LocalEntity.load(w, a.entity), a.scene or ""))


def cmd_expr_gen(a):
    from .entity import LocalEntity
    w = World.load(a.world)
    emos = [x.strip() for x in a.emotions.split(",") if x.strip()] if a.emotions else None
    _out(lenses.render_expressions(w, LocalEntity.load(w, a.entity), emos))


def cmd_expr_classify(a):
    from . import expressions
    _out({"emotion": expressions.classify_emotion(a.text, expressions.EMOTIONS_CORE)})


def cmd_group_new(a):
    from . import group
    mem = [x.strip() for x in a.members.split(",") if x.strip()]
    g = group.Group.create(a.id, a.name or a.id, a.world, mem)
    print(f"✓ 建群:{g.meta()['name']}({a.id})— 成员 {len(mem)}:{'、'.join(mem)}")


def cmd_group_chat(a):
    from . import group
    _out(group.turn(group.Group.load(a.id), a.message))


def cmd_groups(a):
    from . import group
    _out({"groups": [{"id": gid, **{k: group.Group.load(gid).meta().get(k) for k in ("name", "world", "members")}}
                     for gid in group.Group.list_all()]})


def cmd_branch_new(a):
    from . import branch
    w, t = _wt(a.world, a.thread)
    b = branch.Branch.create(t, a.from_chapter, name=a.name or "", divergence=a.divergence or "")
    print(f"✓ 分支:{b.meta()['name']}({b.bid})— 从第 {b.meta()['from_chapter']} 章分叉")


def cmd_branches(a):
    from . import branch
    w, t = _wt(a.world, a.thread)
    _out({"branches": branch.list_branches(t)})


def cmd_skills(a):
    from . import skills
    if a.read:
        print(skills.read_skill(a.read) or f"(无此 skill:{a.read})")
    else:
        _out({"skills": skills.list_skills()})


def cmd_skill_add(a):
    from . import skills
    r = skills.add_skill(a.name, a.description or "", a.body or "", scope=a.scope or "global")
    print(f"✓ skill:{r['name']}({r['scope']})")


def cmd_skills_seed(a):
    from . import skills
    print(f"✓ 灌入起始写作 skill {skills.seed()} 个(已存在的跳过)")


def cmd_modes(a):
    from . import modes
    if a.mode:
        _out(modes.mode_pack(a.mode, genre=a.genre or ""))
    else:
        _out({"modes": modes.list_modes(a.group or "")})


def cmd_convert(a):
    from . import convert
    w = World.load(a.world)
    if a.entity:
        from .entity import LocalEntity
        pack = convert.chat_to(w, LocalEntity.load(w, a.entity), a.to or "novel")
    elif a.chapter:
        _, t = _wt(a.world, a.thread)
        pack = convert.chapter_to(w, t, a.chapter, a.to or "cyoa")
    else:
        _, t = _wt(a.world, a.thread)
        pack = convert.beats_to(w, t, a.to or "screenplay")
    _out(convert.run(pack) if a.run else pack)


def cmd_render_commit(a):
    w, t = _wt(a.world, a.thread)
    _out(lenses.render_commit(w, t, a.subject or "", appearance=a.appearance or ""))


# ---------- 枢纽(L4 · 强连接)----------
def cmd_ascend(a):
    r = nexus.ascend(World.load(a.world), a.entity, as_id=getattr(a, "as", None))
    print(f"✓ 已升格为跨世界实体:{r['name']}(`{r['nexus_id']}`),起源 {r['origin']}")
    print(f"  起源化身:{r['incarnation']} ｜ anchors:{r['anchors'] or '—'}")


def cmd_summon(a):
    r = nexus.summon(a.nexus_id, World.load(a.world), entry=a.entry)
    print(f"✓ {a.nexus_id} 进入世界 {a.world}(化身已开,{a.entry})。当前化身:{', '.join(r['incarnations'])}")


def cmd_extract(a):
    from . import ascension
    r = ascension.extract(World.load(a.world), a.entity, soul_id=a.as_soul or None)
    print(f"✓ 提取升华:{r['name']} → 魂 `{r['soul']}`(就地抽魂,搬走身份记忆 {r['moved_identity']} 条,已落数值攻略卡)")
    print(f"  锚点(唯一真相):{r['anchors'] or '—'}")


def cmd_summon_soul(a):
    from . import ascension
    r = ascension.summon(a.soul, World.load(a.world), entry=a.entry, as_id=a.as_id or None)
    print(f"✓ 召唤:魂 `{r['soul']}` 降临世界 {r['world']}(化身 {r['incarnation']},{r['entry']}"
          + (f",经『{r['via']}』" if r.get("via") else "") + ")。已落 cross beat 到目标世界线。")


def cmd_create_soul(a):
    from . import ascension
    anchors = [x.strip() for x in (a.anchors or "").split("|") if x.strip()]
    r = ascension.create_soul(World.load(a.world), a.entity, a.name, role=a.role, anchors=anchors)
    print(f"✓ 创造即魂:{r['name']}(`{r['soul']}` @ {r['incarnation']})。锚点:{r['anchors'] or '—'}")


def cmd_link(a):
    e = nexus.link_worlds(a.world_a, a.world_b, a.relation, note=a.note or "")
    print(f"✓ 世界互联:{e['a']} ⇄ {e['b']} :{e['relation']}")


def cmd_nexus(a):
    ents = nexus.kept_entities(); ls = nexus.links()
    print(f"暗宇宙枢纽 · {len(World.list_all())} 世界 / {len(ls)} 连接 / {len(ents)} 跨世界实体")
    for e in ls:
        print(f"  ⇄ {e['a']} — {e['b']} :{e['relation']}")
    for k in ents:
        ne = NexusEntity(k["id"]); incs = "、".join(ne.incarnations()) if ne.exists() else ""
        print(f"  · {k['name']} ({k['id']}) 起源 {k['origin']} ｜ 化身 {incs or '—'}")


# ---------- 质检 / 查询 ----------
def cmd_export_thread(a):
    w, t = _wt(a.world, a.thread)
    print(export.compile_thread_book(w, t)["content"])


def cmd_delete_world(a):
    World.load(a.id)  # 校验存在
    nexus.purge_world(a.id)
    World(a.id).delete()
    print(f"✓ 已删世界 {a.id}(及枢纽残留连接/化身)")


def cmd_delete_thread(a):
    w, t = _wt(a.world, a.thread)
    t.delete()
    print(f"✓ 已删叙事线 {a.world}/{a.thread}")


def cmd_delete_entity(a):
    from .entity import LocalEntity
    LocalEntity.load(World.load(a.world), a.entity).delete()
    print(f"✓ 已删实体 {a.world}/{a.entity}")


def cmd_delete_codex(a):
    ok = codex.remove(a.category, a.id)
    print(f"{'✓ 已删' if ok else '✗ 未找到'}元件 [{a.category}] {a.id}")


def cmd_unlink(a):
    r = nexus.unlink(a.world_a, a.world_b)
    print(f"✓ 已断开 {a.world_a} ⇄ {a.world_b}(移除 {r['removed']} 条)")


def cmd_hooks(a):
    w, t = _wt(a.world, a.thread)
    d = t.hooks_data()
    _out({"alpha": d["alpha"], "hooks": d["hooks"], "overdue": [h["id"] for h in t.overdue_hooks()]})


def cmd_hook_add(a):
    w, t = _wt(a.world, a.thread)
    _out(t.add_hook(a.desc, type=a.type, level=a.level, importance=a.importance,
                    plant_chapter=(a.plant if a.plant >= 0 else None),
                    payoff_target=(a.payoff if a.payoff >= 0 else None)))


def cmd_hook_set(a):
    w, t = _wt(a.world, a.thread)
    f = {}
    if a.status:
        f["status"] = a.status
    if a.payoff >= 0:
        f["payoff_target"] = a.payoff
    if a.desc:
        f["desc"] = a.desc
    _out(t.update_hook(a.hid, **f))


def cmd_hook_alpha(a):
    w, t = _wt(a.world, a.thread)
    t.set_alpha(a.text)
    print("✓ α 悬念已设")


def cmd_check(a):
    w, t = _wt(a.world, a.thread)
    _out(checks.check_chapter(t, a.chapter))


def cmd_check_book(a):
    w, t = _wt(a.world, a.thread)
    _out(checks.check_book(t, last_n=a.last or None))


def cmd_worldbook(a):
    w = World.load(a.world)
    if a.context:
        _out(worldbook.scan(w, a.context))
    else:
        data = worldbook.load(w)
        _out({**worldbook.summary(w),
              "entries": [{"name": e.get("name"), "keys": e.get("keys"),
                           "constant": e.get("constant"), "source": e.get("source")}
                          for e in data.get("entries", [])]})


def cmd_status(a):
    if not a.world:
        ws = World.list_all()
        print(f"暗宇宙 · {len(ws)} 世界 / {len(nexus.links())} 连接 / {len(nexus.kept_entities())} 跨世界实体")
        for wid in ws:
            w = World.load(wid)
            print(f"  · {w.meta().get('name', wid)} ({wid}) — {len(w.list_threads())} 线, {len(w.list_entities())} 实体")
        return
    w = World.load(a.world)
    if not a.thread:
        m = w.meta()
        print(f"世界 {m.get('name')} ({w.id}) ｜ {m.get('genre')} ｜ 尺度 {m.get('scale')} ｜ 连接 {[l['to'] for l in m.get('links',[])] or '—'}")
        for tid in w.list_threads():
            t = Thread.load(w, tid); tm = t.meta()
            print(f"  · {tm.get('title')} ({tid}) — {tm.get('chapter_count')}章 ｜ 透镜 {tm.get('lenses') or '—'}")
        for eid in w.list_entities():
            e = LocalEntity(w, eid)
            print(f"  实体 {e.card().get('name')} ({eid}) role={e.role}")
        return
    t = Thread.load(w, a.thread); m = t.meta()
    print(f"线 {m.get('title')} ({w.id}/{t.id}) ｜ {m.get('genre')} ｜ {m.get('chapter_count')}章 ｜ 透镜 {m.get('lenses')}")
    print(f"  节奏契约:{m.get('pacing')} ｜ beats:{len(t.beats())}")


def cmd_show(a):
    kind, key = a.kind, a.key
    if kind == "world":
        print((World.load(key).dir / "world.md").read_text(encoding="utf-8"))
    elif kind == "thread":
        w, tid = key.split("/", 1)
        print((Thread.load(World.load(w), tid).dir / "thread.md").read_text(encoding="utf-8"))
    elif kind == "entity":
        w, eid = key.split("/", 1)
        print((LocalEntity.load(World.load(w), eid).dir / "profile.md").read_text(encoding="utf-8"))
    elif kind == "nexus":
        print((NexusEntity.load(key).dir / "soul.md").read_text(encoding="utf-8"))
    else:
        print("未知类型:world|thread|entity|nexus")


def cmd_config(a):
    from . import config as cfg
    if a.key and a.value is not None:
        cfg.save_setting({a.key: a.value})
        print(f"✓ 已设 {a.key}(写入 sv.local.conf,即时生效)")
    else:
        _out(cfg.settings_snapshot())


def cmd_doctor(a):
    from .config import RENDER, SIMULATE_ENABLED, EMBED_PROVIDER, PROVIDER, MODEL
    print("ShadowVerse 暗宇宙引擎 · 自检")
    print(f"  universe:{UNIVERSE}  ({'存在' if UNIVERSE.exists() else '将自动创建'})")
    print(f"  世界 {len(World.list_all())} ｜ 跨世界实体 {len(nexus.kept_entities())} ｜ 连接 {len(nexus.links())} ｜ 元件 {len(codex.all_elements())}")
    print(f"  透镜:narrate ✓ ｜ play ✓ ｜ simulate {'ON' if SIMULATE_ENABLED else 'OFF(留接口)'} ｜ render {RENDER}")
    print(f"  题材配方:{len(recipes.genres())} 种({'/'.join(recipes.genres())})")
    llm_desc = "stub(关·占位)" if not llm.available() else f"{PROVIDER}:{MODEL or '默认'}"
    print(f"  LLM 生成:{llm_desc}（单机一键造世界/写章;作为 skill 时走宿主模型）")
    print(f"  向量检索:{EMBED_PROVIDER}（none=bigram 关键词,规模驱动才点亮）")
    print("  生成/写作模型:由宿主 Agent 提供(Model A,引擎不内置、不限尺度)。")


def build_parser():
    p = argparse.ArgumentParser(prog="sv", description="ShadowVerse 暗宇宙引擎 CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, fn, pos=(), opt=()):
        s = sub.add_parser(name)
        for a in pos:
            if isinstance(a, tuple):
                s.add_argument(a[0], **a[1])
            else:
                s.add_argument(a)
        for o in opt:
            s.add_argument(f"--{o[0]}", **o[1])
        s.set_defaults(fn=fn)
        return s

    add("codex-add", cmd_codex_add, ["category", "id"], [("summary", {"default": ""}), ("tags", {"default": ""}), ("body", {"default": ""})])
    add("codex-seed", cmd_codex_seed)
    add("components-seed", cmd_components_seed)
    add("codex-list", cmd_codex_list)
    add("codex-pick", cmd_codex_pick, ["query"], [("category", {"default": ""}), ("tags", {"default": ""})])

    add("world-prep", cmd_world_prep, ["prompt"], [("tags", {"default": ""}), ("genre", {"default": ""})])
    add("recipes", cmd_recipes, [], [("genre", {"default": ""})])
    add("gen-world", cmd_gen_world, ["prompt"], [("genre", {"default": ""}), ("tags", {"default": ""})])
    add("gen-entity", cmd_gen_entity, ["world", "prompt"], [("role", {"default": "secondary"})])
    add("gen-thread", cmd_gen_thread, ["world", "prompt"])
    add("gen-chapter", cmd_gen_chapter, ["world", "thread"], [("intent", {"default": ""})])
    add("narrate-run", cmd_narrate_run, ["world", "thread"], [("intent", {"default": ""}), ("max-rev", {"type": int, "default": 1, "dest": "max_rev"}), ("no-commit", {"action": "store_true", "dest": "no_commit"})])
    add("review-prep", cmd_review_prep, ["world", "thread", ("chapter", {"type": int})])
    add("narrate-review", cmd_narrate_review, ["world", "thread", ("chapter", {"type": int})])
    add("reflect-prep", cmd_reflect_prep, ["world", "thread"], [("last", {"type": int, "default": 5})])
    add("narrate-reflect", cmd_narrate_reflect, ["world", "thread"], [("last", {"type": int, "default": 5})])
    add("world-commit", cmd_world_commit)
    add("entity-prep", cmd_entity_prep, ["world", "prompt"], [("tags", {"default": ""})])
    add("card-prep", cmd_card_prep, ["concept"], [("genre", {"default": ""}), ("tags", {"default": ""})])
    add("worldbook-prep", cmd_worldbook_prep, ["concept"], [("genre", {"default": ""})])
    add("gen-card", cmd_gen_card, ["concept"], [("genre", {"default": ""}), ("tags", {"default": ""})])
    add("entity-commit", cmd_entity_commit, ["world"])
    add("thread-prep", cmd_thread_prep, ["world", "prompt"], [("tags", {"default": ""})])
    add("thread-commit", cmd_thread_commit, ["world"])

    add("import-card", cmd_import_card, ["world", "path"], [("role", {"default": "secondary"}), ("as", {"default": None})])
    add("import-card-world", cmd_import_card_world, ["path"], [("world-id", {"default": "", "dest": "world_id"}), ("world-name", {"default": "", "dest": "world_name"}), ("role", {"default": "main"})])
    add("undo-import", cmd_undo_import, ["world", "entity"])
    add("import-preset", cmd_import_preset, ["path"], [("name", {"default": ""}), ("id", {"default": ""})])
    add("import-regex", cmd_import_regex, ["path"], [("name", {"default": ""})])
    add("presets", cmd_presets)
    add("merge-world", cmd_merge_world, ["src", "dst"], [("keep-src", {"action": "store_true", "dest": "keep_src"})])
    add("new-world", cmd_new_world, ["id"], [("name", {"default": ""}), ("genre", {"default": ""}), ("scale", {"default": "max"})])
    add("new-entity", cmd_new_entity, ["world", "id"], [("name", {"default": ""}), ("role", {"default": "secondary"})])
    add("new-thread", cmd_new_thread, ["world", "id"], [("title", {"default": ""}), ("genre", {"default": ""}), ("pacing", {"default": "每章至少推进一条主线钩子"})])

    add("narrate-prep", cmd_narrate_prep, ["world", "thread"], [("focus", {"default": ""}), ("intent", {"default": ""})])
    add("narrate-commit", cmd_narrate_commit, ["world", "thread"])
    add("play-prep", cmd_play_prep, ["world", "thread"], [("scene", {"default": ""}), ("entities", {"default": ""})])
    add("play-commit", cmd_play_commit, ["world", "thread"])
    add("simulate-prep", cmd_simulate_prep, ["world", "thread"])
    add("simulate-commit", cmd_simulate_commit, ["world", "thread"])
    add("render-prep", cmd_render_prep, ["world"], [("subject", {"default": ""}), ("appearance", {"default": ""})])
    add("render-commit", cmd_render_commit, ["world", "thread"], [("subject", {"default": ""}), ("appearance", {"default": ""})])
    add("render-entity", cmd_render_entity, ["world", "entity"], [("scene", {"default": ""})])
    add("expr-gen", cmd_expr_gen, ["world", "entity"], [("emotions", {"default": ""})])
    add("expr-classify", cmd_expr_classify, ["text"])
    add("group-new", cmd_group_new, ["id", "world", "members"], [("name", {"default": ""})])
    add("group-chat", cmd_group_chat, ["id", "message"])
    add("groups", cmd_groups)
    add("branch-new", cmd_branch_new, ["world", "thread", ("from_chapter", {"type": int})],
        [("name", {"default": ""}), ("divergence", {"default": ""})])
    add("branches", cmd_branches, ["world", "thread"])
    add("skills", cmd_skills, [], [("read", {"default": ""})])
    add("skill-add", cmd_skill_add, ["name"], [("description", {"default": ""}), ("body", {"default": ""}), ("scope", {"default": "global"})])
    add("skills-seed", cmd_skills_seed)
    add("modes", cmd_modes, [], [("mode", {"default": ""}), ("group", {"default": ""}), ("genre", {"default": ""})])
    add("convert", cmd_convert, ["world"], [("entity", {"default": ""}), ("thread", {"default": ""}),
        ("chapter", {"type": int, "default": 0}), ("to", {"default": ""}), ("run", {"action": "store_true"})])

    add("ascend", cmd_ascend, ["world", "entity"], [("as", {"default": None})])
    add("summon", cmd_summon, ["nexus_id", "world"], [("entry", {"default": "本体进"})])
    add("link", cmd_link, ["world_a", "world_b", "relation"], [("note", {"default": ""})])
    add("nexus", cmd_nexus)
    # 魂模型新路径(一魂·多门重设计):提取/创造升华 + 跨世界召唤
    add("extract", cmd_extract, ["world", "entity"], [("as-soul", {"default": None})])
    add("summon-soul", cmd_summon_soul, ["soul", "world"], [("entry", {"default": "本体进"}), ("as-id", {"default": None})])
    add("create-soul", cmd_create_soul, ["world", "entity", "name"],
        [("role", {"default": "main"}), ("anchors", {"default": ""})])

    add("export-thread", cmd_export_thread, ["world", "thread"])
    add("delete-world", cmd_delete_world, ["id"])
    add("delete-thread", cmd_delete_thread, ["world", "thread"])
    add("delete-entity", cmd_delete_entity, ["world", "entity"])
    add("delete-codex", cmd_delete_codex, ["category", "id"])
    add("unlink", cmd_unlink, ["world_a", "world_b"])
    add("hooks", cmd_hooks, ["world", "thread"])
    add("hook-add", cmd_hook_add, ["world", "thread", "desc"], [("type", {"default": "event"}), ("level", {"default": "中"}), ("importance", {"default": "mid"}), ("plant", {"type": int, "default": -1}), ("payoff", {"type": int, "default": -1})])
    add("hook-set", cmd_hook_set, ["world", "thread", "hid"], [("status", {"default": ""}), ("payoff", {"type": int, "default": -1}), ("desc", {"default": ""})])
    add("hook-alpha", cmd_hook_alpha, ["world", "thread", "text"])
    add("check", cmd_check, ["world", "thread", ("chapter", {"type": int})])
    add("check-book", cmd_check_book, ["world", "thread"], [("last", {"type": int, "default": 0})])
    add("worldbook", cmd_worldbook, ["world"], [("context", {"default": ""})])
    add("status", cmd_status, [("world", {"nargs": "?"}), ("thread", {"nargs": "?"})])
    add("show", cmd_show, ["kind", "key"])
    add("config", cmd_config, [("key", {"nargs": "?"}), ("value", {"nargs": "?"})])
    add("doctor", cmd_doctor)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.fn(args)
        return 0
    except (FileNotFoundError, FileExistsError, ValueError, KeyError) as e:
        print(f"✗ {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
