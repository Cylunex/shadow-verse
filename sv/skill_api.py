"""skill_api —— 宿主 Agent 调用的 CLI 入口(Model A · AIGC 多元宇宙)。

prep 输出 JSON 包(供子代理消费);commit 读 stdin JSON、落盘、回执;authoring/查询输出可读文本。
写作/生成智力在宿主模型,引擎只取料、组装、落盘、连接。

用法:python -m sv.skill_api <命令> ...   (Windows 建议 PYTHONUTF8=1)
"""
from __future__ import annotations

import argparse
import json
import sys

from . import checks, codex, export, forge, lenses, llm, nexus, recipes
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


def cmd_check(a):
    w, t = _wt(a.world, a.thread)
    _out(checks.check_chapter(t, a.chapter))


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
    add("entity-commit", cmd_entity_commit, ["world"])
    add("thread-prep", cmd_thread_prep, ["world", "prompt"], [("tags", {"default": ""})])
    add("thread-commit", cmd_thread_commit, ["world"])

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

    add("ascend", cmd_ascend, ["world", "entity"], [("as", {"default": None})])
    add("summon", cmd_summon, ["nexus_id", "world"], [("entry", {"default": "本体进"})])
    add("link", cmd_link, ["world_a", "world_b", "relation"], [("note", {"default": ""})])
    add("nexus", cmd_nexus)

    add("export-thread", cmd_export_thread, ["world", "thread"])
    add("delete-world", cmd_delete_world, ["id"])
    add("delete-thread", cmd_delete_thread, ["world", "thread"])
    add("delete-entity", cmd_delete_entity, ["world", "entity"])
    add("delete-codex", cmd_delete_codex, ["category", "id"])
    add("unlink", cmd_unlink, ["world_a", "world_b"])
    add("check", cmd_check, ["world", "thread", ("chapter", {"type": int})])
    add("status", cmd_status, [("world", {"nargs": "?"}), ("thread", {"nargs": "?"})])
    add("show", cmd_show, ["kind", "key"])
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
