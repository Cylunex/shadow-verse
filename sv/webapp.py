"""暗宇宙 · 网页控制台(零依赖,stdlib http.server)。

`universe/` 文件的视图层 + 操作层(读同一批文件,直接调引擎)。
GET 读(总览/世界/线/实体/枢纽/元件 + prep 取包);POST 写(建/编/锻造落盘/升格/召唤/连接)。
写正文/生成的智力仍是宿主模型:页面给你"写作包",你(或你的 LLM)写好正文回填提交。
默认只绑 127.0.0.1(单机本地工具)。跑:python -m sv.webapp [--port 8787]
"""
from __future__ import annotations

import argparse
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import base64

from . import chat as chatmod
from . import codex, config, export, forge, importer, lenses, llm, memory, nexus, recipes, util, varstate
from .config import UNIVERSE, read_jsonl
from .entity import LocalEntity
from .nexus import NexusEntity
from .thread import Thread
from .world import World

WEB_DIR = Path(__file__).resolve().parent / "web"


# ================= GET：读 =================
def api_overview() -> dict:
    worlds = []
    for wid in World.list_all():
        w = World.load(wid); m = w.meta()
        worlds.append({"id": wid, "name": m.get("name", wid), "genre": m.get("genre", ""),
                       "scale": m.get("scale", ""), "threads": len(w.list_threads()),
                       "entities": len(w.list_entities()), "links": m.get("links", []),
                       "provenance": m.get("provenance", {}).get("source", "")})
    nx = {"entities": [], "links": nexus.links()}
    for k in nexus.kept_entities():
        ne = NexusEntity(k["id"])
        nx["entities"].append({"id": k["id"], "name": k["name"], "origin": k["origin"],
                               "incarnations": ne.incarnations() if ne.exists() else []})
    cats: dict[str, int] = {}
    for e in codex.all_elements():
        cats[e["category"]] = cats.get(e["category"], 0) + 1
    return {"worlds": worlds, "nexus": nx, "codex": {"count": len(codex.all_elements()), "by_category": cats},
            "genres": recipes.genres(),
            "llm": {"provider": config.PROVIDER, "available": llm.available()}}


def api_world(wid: str) -> dict:
    w = World.load(wid); m = w.meta()
    ents = [{"id": eid, "name": LocalEntity(w, eid).card().get("name", eid),
             "role": LocalEntity(w, eid).card().get("role", ""),
             "provenance": LocalEntity(w, eid).card().get("provenance", {}).get("source", "")}
            for eid in w.list_entities()]
    threads = []
    for tid in w.list_threads():
        t = Thread.load(w, tid); tm = t.meta()
        threads.append({"id": tid, "title": tm.get("title", tid), "genre": tm.get("genre", ""),
                        "chapters": tm.get("chapter_count", 0), "lenses": tm.get("lenses", [])})
    return {"meta": m, "world_md": util.read_md(w.dir / "world.md"),
            "canon_md": util.read_md(w.dir / "canon.md"), "entities": ents, "threads": threads,
            "nexus_here": [k["id"] for k in nexus.kept_entities()
                           if wid in (NexusEntity(k["id"]).incarnations() if NexusEntity(k["id"]).exists() else [])]}


def api_thread(wid: str, tid: str) -> dict:
    w = World.load(wid); t = Thread.load(w, tid); m = t.meta()
    chapters = []
    for n in range(1, t.last_chapter_no() + 1):
        raw = t.chapter_text(n); first = raw.splitlines()[0] if raw else ""
        mt = re.match(r"# 第 \d+ 章(?: · (.+))?", first)
        title = mt.group(1) if mt and mt.group(1) else ""
        body = "\n".join(raw.splitlines()[1:]).strip()
        chapters.append({"no": n, "title": title, "text": body, "hanzi": _hanzi(body)})
    sessions = [{"id": p.stem, "text": p.read_text(encoding="utf-8")}
                for p in sorted(t.sessions_dir.glob("*.md"))] if t.sessions_dir.exists() else []
    renders = [f"worlds/{wid}/threads/{tid}/renders/{p.name}" for p in sorted(t.renders_dir.glob("*.png"))] if t.renders_dir.exists() else []
    hd = t.hooks_data(); overdue = {h["id"] for h in t.overdue_hooks()}
    return {"meta": m, "thread_md": util.read_md(t.dir / "thread.md"), "summary_md": t.summary(),
            "chapters": chapters, "beats": t.beats(), "sessions": sessions, "renders": renders,
            "hooks": {"alpha": hd["alpha"], "items": hd["hooks"], "overdue": list(overdue)},
            "recipe": recipes.get(m.get("genre", "")),
            "entities": [{"id": e, "name": LocalEntity(w, e).card().get("name", e),
                          "role": LocalEntity(w, e).card().get("role", "")} for e in w.list_entities()]}


def api_entity(wid: str, eid: str) -> dict:
    w = World.load(wid); e = LocalEntity.load(w, eid)
    pd = e.dir / "portraits"
    portraits = [f"worlds/{wid}/entities/{eid}/portraits/{p.name}" for p in sorted(pd.glob("*.png"))] if pd.exists() else []
    return {"card": e.card(), "profile_md": util.read_md(e.dir / "profile.md"),
            "state": memory.read_state(e.dir), "anchors": e.anchors(),
            "appearance": e.appearance, "avatar": e.avatar_rel(), "portraits": portraits,
            "experiences": memory.all_experiences(e.dir)}


def api_nexus_entity(nid: str) -> dict:
    ne = NexusEntity.load(nid); m = ne.meta()
    incs = [{"world": wid, "state": memory.read_state(ne.incarnation_dir(wid)),
             "experiences": read_jsonl(ne.incarnation_dir(wid) / "experiences.jsonl")}
            for wid in ne.incarnations()]
    return {"meta": m, "soul_md": util.read_md(ne.dir / "soul.md"), "anchors": ne.anchors(), "incarnations": incs}


def api_codex() -> dict:
    return {"elements": codex.all_elements(), "categories": list(codex.CATEGORIES)}


def api_export_thread(wid: str, tid: str) -> dict:
    w = World.load(wid)
    return export.compile_thread_book(w, Thread.load(w, tid))


def api_config() -> dict:
    return config.settings_snapshot()


def _regex_render(text: str, scripts: list | None = None) -> str:
    """显示前套用已导入的 ST 正则脚本(scope=output);不改 chat.jsonl 原文(非破坏性)。
    scripts 可由调用方一次性 load 后传入,免在循环里每行重读 universe/regex/*.json。"""
    if not text:
        return text
    try:
        if scripts is None:
            scripts = importer.load_regex_scripts()
        return importer.apply_regex(text, scripts, scope="output")
    except Exception:  # noqa: BLE001 — 正则渲染绝不阻断对话
        return text


def _regex_out(d: dict) -> dict:
    """聊天响应里的 reply 字段套正则(给前端展示用)。"""
    if isinstance(d, dict) and d.get("reply"):
        d["reply"] = _regex_render(d["reply"])
    return d


def api_chat(wid: str, eid: str) -> dict:
    w = World.load(wid); e = LocalEntity.load(w, eid)
    scripts = importer.load_regex_scripts()     # 一次读盘:历史 N 行 + 主开场白 + alt 开场白 共用
    st = chatmod.var_state(e)                   # 一次 load:vars/var_view/var_meta/base_chars 全用它
    pl = chatmod.player()
    hist = chatmod.history(e)
    for h in hist:                              # 历史里 char 行显示前套正则(原文不动)
        if h.get("role") == "char" and h.get("text"):
            h["text"] = _regex_render(h["text"], scripts)
    return {"world": wid, "entity": eid, "name": e.card().get("name", eid),
            "greeting": _regex_render(chatmod.greeting(e), scripts), "history": hist,
            "greetings": [_regex_render(g, scripts) for g in chatmod.greetings(e)], "greeting_id": chatmod.greeting_id(e),
            "avatar": e.avatar_rel(), "player": pl, "vars": st["data"],
            "var_view": varstate.visible(st),   # HUD 用(已滤 hidden + 带 vis)
            "var_meta": st.get("meta", {}),
            "author_note": chatmod.author_note(e).get("text", ""),
            "quick_replies": chatmod.quick_replies(),
            "base_chars": len(chatmod._system(w, e, pl, st["data"])),  # 上下文表的基线(系统提示长度)
            "preset_active": config.PRESET,
            "llm_available": llm.available(),
            "history_window": chatmod.HISTORY_WINDOW}   # 前端 token 表只该数最近这么多条


def post_chat_edit(b: dict) -> dict:
    w = World.load(b["world"]); e = LocalEntity.load(w, b["entity"])
    return chatmod.edit_floor(e, int(b["floor"]), b.get("text", ""))


def post_chat_delete(b: dict) -> dict:
    w = World.load(b["world"]); e = LocalEntity.load(w, b["entity"])
    return chatmod.delete_floor(e, int(b["floor"]))


def post_chat_set_greeting(b: dict) -> dict:
    w = World.load(b["world"]); e = LocalEntity.load(w, b["entity"])
    r = chatmod.set_greeting(e, int(b["idx"]))
    r["greeting"] = _regex_render(r.get("greeting", ""))
    return r


def post_author_note(b: dict) -> dict:
    w = World.load(b["world"]); e = LocalEntity.load(w, b["entity"])
    return {"ok": True, **chatmod.set_author_note(e, b.get("text", ""))}


def post_quick_replies(b: dict) -> dict:
    return {"ok": True, "quick_replies": chatmod.set_quick_replies(b.get("items", []))}


def api_timeline(wid: str) -> dict:
    """世界故事时间线:所有线的 beats(跨透镜)+ 各实体的身份级成长时刻,按时间合并。"""
    w = World.load(wid)
    events = []
    for tid in w.list_threads():
        t = Thread.load(w, tid)
        title = t.meta().get("title", tid)
        for b in t.beats():
            events.append({"ts": b.get("ts", ""), "kind": "beat", "thread": tid, "thread_title": title,
                           "lens": b.get("lens", ""), "where": b.get("where", ""), "text": b.get("text", "")})
    for eid in w.list_entities():
        e = LocalEntity(w, eid)
        nm = e.card().get("name", eid)
        for x in memory.all_experiences(e.dir):
            if x.get("level") == "身份":
                events.append({"ts": x.get("ts", ""), "kind": "growth", "entity": eid, "name": nm,
                               "where": x.get("where", ""), "text": x.get("text", "")})
    events.sort(key=lambda x: x.get("ts", ""))
    # 在本世界有化身的跨世界实体
    cross = [k["id"] for k in nexus.kept_entities()
             if wid in (NexusEntity(k["id"]).incarnations() if NexusEntity(k["id"]).exists() else [])]
    return {"world": wid, "name": w.meta().get("name", wid), "events": events,
            "threads": w.list_threads(), "entity_count": len(w.list_entities()), "cross_world": cross}


def api_narrate_prep(q: dict) -> dict:
    w = World.load(q["world"]); t = Thread.load(w, q["thread"])
    return lenses.narrate_prep(w, t, brief=q.get("intent", ""))


def api_play_prep(q: dict) -> dict:
    w = World.load(q["world"]); t = Thread.load(w, q["thread"])
    return lenses.play_prep(w, t, q.get("scene", ""), [x for x in q.get("entities", "").split(",") if x])


def api_world_prep(q: dict) -> dict:
    return forge.world_prep(q.get("prompt", ""), genre=q.get("genre", ""))


def api_recipe(q: dict) -> dict:
    return recipes.get(q.get("genre", ""))


# ================= POST：写 =================
def post_world_create(b: dict) -> dict:
    w = World.create(b["id"], b.get("name", b["id"]), genre=b.get("genre", ""),
                     scale=b.get("scale", "max"), body=b.get("world_md") or None)
    return {"ok": True, "id": w.id}


def post_world_save_md(b: dict) -> dict:
    w = World.load(b["world"]); util.write_md(w.dir / "world.md", b["world_md"]); return {"ok": True}


def post_entity_create(b: dict) -> dict:
    w = World.load(b["world"])
    e = LocalEntity.create(w, b["id"], b.get("name", b["id"]), role=b.get("role", "secondary"),
                           appearance=b.get("appearance", ""))
    if b.get("profile_md"):
        util.write_md(e.dir / "profile.md", b["profile_md"])
    return {"ok": True, "id": e.id}


def post_render_entity(b: dict) -> dict:
    w = World.load(b["world"]); e = LocalEntity.load(w, b["entity"])
    if b.get("appearance") is not None and b.get("appearance") != "":
        e.set_appearance(b["appearance"])
    return lenses.render_entity(w, e, b.get("scene", ""))


def post_render_scene(b: dict) -> dict:
    w = World.load(b["world"]); t = Thread.load(w, b["thread"])
    return lenses.render_scene(w, t, b.get("subject", ""), appearance=b.get("appearance", ""))


def post_config(b: dict) -> dict:
    """保存设置到 sv.local.conf 并热加载(免重启)。只接受空字符串才清除某键。"""
    config.save_setting(b or {})
    return {"ok": True, **config.settings_snapshot()}


def post_llm_test(b: dict) -> dict:
    """探活当前 LLM:生成一小段。stub 也返回(占位)。"""
    try:
        out = llm.generate("你是测试助手,只回最短的话。", "回复两个字:在的", max_tokens=24, temperature=0.0)
        return {"ok": True, "provider": config.PROVIDER, "stub": config.PROVIDER == "stub", "sample": out[:160]}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "provider": config.PROVIDER, "error": str(e)}


def post_thread_create(b: dict) -> dict:
    w = World.load(b["world"])
    t = Thread.create(w, b["id"], b.get("title", b["id"]), genre=b.get("genre", ""),
                      pacing=b.get("pacing", "每章至少推进一条主线钩子"))
    if b.get("thread_md"):
        util.write_md(t.dir / "thread.md", b["thread_md"])
    return {"ok": True, "id": t.id}


def post_codex_create(b: dict) -> dict:
    r = codex.add(b["category"], b["id"], b.get("summary", ""),
                  tags=[x.strip() for x in b.get("tags", "").split(",") if x.strip()], body=b.get("body", ""))
    return {"ok": True, "id": r["id"]}


def post_codex_seed(b: dict) -> dict:
    return {"ok": True, **codex.seed_starter()}


# ---- 删除 / 管理 ----
def post_delete_world(b: dict) -> dict:
    World.load(b["id"]); nexus.purge_world(b["id"]); World(b["id"]).delete()
    return {"ok": True}


def post_delete_thread(b: dict) -> dict:
    Thread.load(World.load(b["world"]), b["thread"]).delete()
    return {"ok": True}


def post_delete_entity(b: dict) -> dict:
    LocalEntity.load(World.load(b["world"]), b["entity"]).delete()
    return {"ok": True}


def post_delete_codex(b: dict) -> dict:
    return {"ok": codex.remove(b["category"], b["id"])}


def post_unlink(b: dict) -> dict:
    return {"ok": True, **nexus.unlink(b["a"], b["b"])}


def _thr(b):
    w = World.load(b["world"]); return w, Thread.load(w, b["thread"])


def post_hook_add(b: dict) -> dict:
    _, t = _thr(b)
    return t.add_hook(b["desc"], type=b.get("type", "event"), level=b.get("level", "中"),
                      importance=b.get("importance", "mid"),
                      plant_chapter=b.get("plant_chapter"), payoff_target=b.get("payoff_target"))


def post_hook_set(b: dict) -> dict:
    _, t = _thr(b)
    return t.update_hook(b["hid"], status=b.get("status"), payoff_target=b.get("payoff_target"), desc=b.get("desc"))


def post_hook_alpha(b: dict) -> dict:
    _, t = _thr(b); t.set_alpha(b.get("text", "")); return {"ok": True}


def post_chat(b: dict) -> dict:
    w = World.load(b["world"]); e = LocalEntity.load(w, b["entity"])
    return _regex_out(chatmod.turn(w, e, b.get("message", "")))


def post_chat_clear(b: dict) -> dict:
    w = World.load(b["world"]); chatmod.clear(LocalEntity.load(w, b["entity"]))
    return {"ok": True}


def post_chat_regenerate(b: dict) -> dict:
    w = World.load(b["world"]); e = LocalEntity.load(w, b["entity"])
    return _regex_out(chatmod.regenerate(w, e))


def api_modes() -> dict:
    from . import modes
    return {"modes": modes.list_modes(), "by_group": {
        g: modes.list_modes(g) for g in ("core", "pillar", "world")}}


def api_groups() -> dict:
    from . import group
    return {"groups": [{"id": gid, "name": group.Group.load(gid).meta().get("name", gid),
                        "world": group.Group.load(gid).meta().get("world"),
                        "members": group.Group.load(gid).meta().get("members", [])}
                       for gid in group.Group.list_all()]}


def api_group(gid: str) -> dict:
    from . import group, varstate
    g = group.Group.load(gid)
    return {"id": gid, "meta": g.meta(), "history": g.history(), "greet": group.greet(g),
            "vars": varstate.load(g)["data"], "llm_available": llm.available()}


def post_group_new(b: dict) -> dict:
    from . import group
    mem = b.get("members") or []
    g = group.Group.create(b["id"], b.get("name") or b["id"], b["world"], mem,
                           talkativeness=b.get("talkativeness") or {})
    return {"ok": True, "id": g.gid}


def post_group_chat(b: dict) -> dict:
    from . import group
    return group.turn(group.Group.load(b["id"]), b.get("message", ""))


def post_group_clear(b: dict) -> dict:
    from . import group
    group.Group.load(b["id"]).clear()
    return {"ok": True}


def post_chat_swipe(b: dict) -> dict:
    """左右切候选(delta=±1);右滑到末尾自动生成新候选。"""
    w = World.load(b["world"]); e = LocalEntity.load(w, b["entity"])
    return _regex_out(chatmod.swipe_next(w, e, int(b.get("delta", 1))))


def post_chat_floor_regen(b: dict) -> dict:
    """从第 idx 楼重生成(截断其后)。"""
    w = World.load(b["world"]); e = LocalEntity.load(w, b["entity"])
    return _regex_out(chatmod.floor_regenerate(w, e, int(b.get("idx", -1))))


def post_chat_undo(b: dict) -> dict:
    w = World.load(b["world"])
    return chatmod.undo_last(LocalEntity.load(w, b["entity"]))


def post_entity_avatar(b: dict) -> dict:
    w = World.load(b["world"]); e = LocalEntity.load(w, b["entity"])
    rel = e.set_avatar(base64.b64decode(b["img_b64"]), b.get("ext", "png"))
    return {"ok": True, "avatar": rel}


def post_entity_expressions(b: dict) -> dict:
    """锁脸预生成一组情绪立绘(需配 render 后端)。"""
    w = World.load(b["world"]); e = LocalEntity.load(w, b["entity"])
    emos = b.get("emotions") or None
    return lenses.render_expressions(w, e, emos)


def post_player(b: dict) -> dict:
    return {"ok": True, "player": chatmod.set_player(b.get("name", "你"), b.get("persona", ""))}


def post_chat_var(b: dict) -> dict:
    w = World.load(b["world"]); e = LocalEntity.load(w, b["entity"])
    return {"ok": True, "vars": chatmod.set_var(e, b["name"], b.get("value", 0))}


def post_chat_var_del(b: dict) -> dict:
    w = World.load(b["world"]); e = LocalEntity.load(w, b["entity"])
    return {"ok": True, "vars": chatmod.del_var(e, b["name"])}


def post_chat_init_vars(b: dict) -> dict:
    """AI 建变量卡(从人设识别该追踪哪些状态)。"""
    w = World.load(b["world"]); e = LocalEntity.load(w, b["entity"])
    return chatmod.init_vars(w, e)


def post_import_card(b: dict) -> dict:
    png = base64.b64decode(b["png_b64"]) if b.get("png_b64") else None   # PNG 卡图 → 头像
    card = importer.parse_card(png) if png else importer.parse_card(b["card"])
    if b.get("target") == "new":   # 默认推荐:卡自带世界 → 新建独立世界
        return {"ok": True, **importer.import_card_new_world(
            card, world_id=b.get("world_id") or None, world_name=b.get("world_name") or None,
            role=b.get("role", "main"), avatar_png=png)}
    w = World.load(b["world"])     # 并入现有世界
    r = importer.import_card(w, card, role=b.get("role", "secondary"), as_id=b.get("as") or None, avatar_png=png)
    return {"ok": True, "world": w.id, **r}


def post_import_preset(b: dict) -> dict:
    """导入 ST 预设(采样集 + 提示词模块)。data=预设 JSON 文本。"""
    return {"ok": True, **importer.import_preset(b["data"], name=b.get("name", ""))}


def post_import_regex(b: dict) -> dict:
    """导入 ST 正则脚本(消息渲染改写)。data=正则 JSON 文本(单个或数组)。"""
    return {"ok": True, **importer.import_regex(b["data"], name=b.get("name", ""))}


def api_presets() -> dict:
    return {"presets": importer.list_presets(), "regex": importer.list_regex(),
            "active_preset": config.PRESET}


def api_preset(pid: str) -> dict:
    """单个预设的完整详情:有序模块(含逐模块开关 enabled)+ 采样参数 + 组装后的系统提示预览。"""
    pre = importer.load_preset(pid)
    return {"id": pid, "name": pre.get("name", pid), "active": config.PRESET == pid,
            "sampling": pre.get("sampling", {}), "modules": pre.get("modules", []),
            "module_count": pre.get("module_count"), "custom_count": pre.get("custom_count"),
            "assembled": importer.assemble_preset(pre, slots={})}


def post_preset_module(b: dict) -> dict:
    """开/关预设里的某个模块(把手艺做成可勾的开关)。"""
    pre = importer.update_preset_module(b["preset"], b["identifier"], bool(b.get("enabled", True)))
    return {"ok": True, "modules": pre.get("modules", []),
            "assembled": importer.assemble_preset(pre, slots={})}


def post_import_undo(b: dict) -> dict:
    return {"ok": True, **importer.undo_import(World.load(b["world"]), b["entity"])}


def post_world_merge(b: dict) -> dict:
    from . import merge
    return {"ok": True, **merge.merge_world(b["src"], b["dst"], delete_src=bool(b.get("delete_src", True)))}


def post_narrate_commit(b: dict) -> dict:
    w = World.load(b["world"]); t = Thread.load(w, b["thread"])
    return lenses.narrate_commit(w, t, b)


def post_play_commit(b: dict) -> dict:
    w = World.load(b["world"]); t = Thread.load(w, b["thread"])
    return lenses.play_commit(w, t, b)


def post_ascend(b: dict) -> dict:
    return nexus.ascend(World.load(b["world"]), b["entity"], as_id=b.get("as") or None)


def post_summon(b: dict) -> dict:
    return nexus.summon(b["nexus_id"], World.load(b["world"]), entry=b.get("entry", "本体进"))


def post_link(b: dict) -> dict:
    return nexus.link_worlds(b["a"], b["b"], b["relation"], note=b.get("note", ""))


# ---- 魂模型新路径(一魂·多门):提取/创造升华 + 跨世界召唤 ----
def post_extract(b: dict) -> dict:
    from . import ascension
    return {"ok": True, **ascension.extract(World.load(b["world"]), b["entity"],
                                            player_name=b.get("player", "你"), soul_id=b.get("soul_id") or None)}


def post_summon_soul(b: dict) -> dict:
    from . import ascension
    return {"ok": True, **ascension.summon(b["soul"], World.load(b["world"]),
                                           entry=b.get("entry", "本体进"), as_id=b.get("as") or None)}


def post_create_soul(b: dict) -> dict:
    from . import ascension
    return {"ok": True, **ascension.create_soul(World.load(b["world"]), b["entity"], b["name"],
                                                role=b.get("role", "main"), anchors=b.get("anchors") or [])}


def api_soul(sid: str) -> dict:
    from .config import read_jsonl
    from .memory import _identity_path
    from .soul import Soul
    s = Soul.load(sid)
    return {"id": s.id, "name": s.meta().get("name", sid), "anchors": s.anchors(),
            "incarnations": s.incarnations(),
            "identity": [x.get("text", "") for x in read_jsonl(_identity_path(s.dir))]}


# ---- 世界书(露出已建的 worldbook 引擎:读/存条目/删条目;引擎逻辑不动)----
def api_worldbook(wid: str) -> dict:
    from . import worldbook as wb
    w = World.load(wid)
    data = wb.load(w)
    return {"world": wid, "name": w.meta().get("name", wid),
            "entries": data.get("entries", []), "summary": wb.summary(w)}


def post_worldbook_save(b: dict) -> dict:
    """新增/更新一条世界书条目(按 uid upsert)。
    编辑既有条目时只覆盖前端真正传来的字段,其余(secondary_keys/source/概率/时效/互斥组等)保留,
    免把导入条目的高级配置抹平。"""
    from . import worldbook as wb
    w = World.load(b["world"]); data = wb.load(w)
    raw = b.get("entry") or {}
    uid = b.get("uid")
    existing = next((x for x in data["entries"] if x.get("uid") == uid), None) if uid is not None else None
    if existing is not None:
        norm = wb.normalize_entry(raw, source=raw.get("source") or existing.get("source", "manual"))
        merged = dict(existing)
        for k in raw:                       # 只覆盖客户端显式发来的字段
            if k in norm:
                merged[k] = norm[k]
        merged["uid"] = uid
        data["entries"][data["entries"].index(existing)] = merged
        out_uid = uid
    else:
        norm = wb.normalize_entry(raw, source=raw.get("source", "manual"))
        norm["uid"] = max((x.get("uid", 0) for x in data["entries"]), default=0) + 1
        data["entries"].append(norm)
        out_uid = norm["uid"]
    wb.save(w, data)
    return {"ok": True, "uid": out_uid, "entries": data["entries"]}


def post_worldbook_delete(b: dict) -> dict:
    from . import worldbook as wb
    w = World.load(b["world"]); data = wb.load(w)
    before = len(data["entries"])
    data["entries"] = [x for x in data["entries"] if x.get("uid") != b.get("uid")]
    wb.save(w, data)
    return {"ok": True, "removed": before - len(data["entries"]), "entries": data["entries"]}


# ---- 记忆溯源(把"这句话从哪来"摊开:命中的世界书条目 + 检索到的记忆 + 起作用锚点)----
def api_trace(q: dict) -> dict:
    """只读重算:据一段上下文,显示哪些世界书条目会命中、检索召回哪些记忆、哪些锚点常驻。
    纯关键词/加权,不调模型;给创作者把看不见的机器摊开(REDESIGN §六)。"""
    from . import worldbook as wb
    w = World.load(q["world"]); e = LocalEntity.load(w, q["entity"])
    buf = q.get("q", "") or ""
    fired = [{"name": x.get("name", ""), "keys": x.get("keys", []), "constant": bool(x.get("constant"))}
             for x in wb.load(w).get("entries", [])
             if x.get("enabled", True) and (x.get("constant") or wb.entry_matches(x, buf))]
    mem = [{"text": m.get("text", ""), "where": m.get("where", ""), "level": m.get("level", ""),
            "score": round(float(m.get("score", 0)), 3) if m.get("score") is not None else None}
           for m in memory.retrieve(e.dir, buf)] if buf.strip() else []
    return {"worldbook": fired, "memory": mem, "anchors": e.anchors()}


# ---- 关系攻略板:给一个角色落上 galgame 关系数值卡(幂等)----
def post_apply_relationship(b: dict) -> dict:
    from . import attrs
    w = World.load(b["world"]); e = LocalEntity.load(w, b["entity"])
    st = attrs.apply_panel(e, player_name=b.get("player", "你"))
    return {"ok": True, "vars": st.get("data", {})}


# ---- 质检(确定性,0 token):全书纵向基线 ----
def post_checks(b: dict) -> dict:
    from . import checks
    w = World.load(b["world"]); t = Thread.load(w, b["thread"])
    return {"ok": True, **checks.check_book(t, last_n=b.get("last") or None)}


# ---- 一稿多吃(convert):chat→小说 / 章→CYOA / beats→剧本… ----
def post_convert(b: dict) -> dict:
    from . import convert
    w = World.load(b["world"]); to = b.get("to", "novel")
    if b.get("entity"):
        pack = convert.chat_to(w, LocalEntity.load(w, b["entity"]), to)
    elif b.get("chapter"):
        pack = convert.chapter_to(w, Thread.load(w, b["thread"]), int(b["chapter"]), to)
    else:
        pack = convert.beats_to(w, Thread.load(w, b["thread"]), to)
    return {"ok": True, "pack": pack, **(convert.run(pack) if b.get("run") else {})}


# ---- 线分支 · 蝴蝶效应 ----
def api_branches(wid: str, tid: str) -> dict:
    from . import branch
    return {"branches": branch.list_branches(Thread.load(World.load(wid), tid))}


def post_branch(b: dict) -> dict:
    from . import branch
    w = World.load(b["world"]); t = Thread.load(w, b["thread"])
    br = branch.Branch.create(t, int(b["from_chapter"]), name=b.get("name", "") or "", divergence=b.get("divergence", "") or "")
    return {"ok": True, "branch": br.meta()}


# ---- AIGC 生成(返回正文供人审后再 create/commit;需配 SV_PROVIDER)----
def post_gen_world(b: dict) -> dict:
    return {"body": forge.generate_world_body(b.get("prompt", ""), genre=b.get("genre", ""),
                                              tags=[x for x in b.get("tags", "").split(",") if x])}


def post_gen_entity(b: dict) -> dict:
    return {"body": forge.generate_entity_body(World.load(b["world"]), b.get("prompt", ""), role=b.get("role", "secondary"))}


def post_gen_thread(b: dict) -> dict:
    return {"body": forge.generate_thread_body(World.load(b["world"]), b.get("prompt", ""))}


def post_gen_chapter(b: dict) -> dict:
    w = World.load(b["world"]); t = Thread.load(w, b["thread"])
    return lenses.narrate_generate(w, t, intent=b.get("intent", ""))


def post_narrate_run(b: dict) -> dict:
    w = World.load(b["world"]); t = Thread.load(w, b["thread"])
    return lenses.narrate_run(w, t, intent=b.get("intent", ""), max_revisions=int(b.get("max_rev", 1)))


def post_narrate_reflect(b: dict) -> dict:
    w = World.load(b["world"]); t = Thread.load(w, b["thread"])
    return lenses.narrate_reflect(w, t, int(b.get("last", 5)))


def _hanzi(s: str) -> int:
    return len(re.findall(r"[一-鿿]", s or ""))


def _qs(path: str) -> dict:
    from urllib.parse import parse_qs, urlparse, unquote
    q = parse_qs(urlparse(path).query)
    return {k: unquote(v[0]) for k, v in q.items()}


GET_ROUTES = [
    (re.compile(r"^/api/overview$"), lambda m, q: api_overview()),
    (re.compile(r"^/api/world/([\w-]+)$"), lambda m, q: api_world(m.group(1))),
    (re.compile(r"^/api/thread/([\w-]+)/([\w-]+)$"), lambda m, q: api_thread(m.group(1), m.group(2))),
    (re.compile(r"^/api/entity/([\w-]+)/([\w-]+)$"), lambda m, q: api_entity(m.group(1), m.group(2))),
    (re.compile(r"^/api/nexus/([\w-]+)$"), lambda m, q: api_nexus_entity(m.group(1))),
    (re.compile(r"^/api/soul/([\w-]+)$"), lambda m, q: api_soul(m.group(1))),
    (re.compile(r"^/api/worldbook/([\w-]+)$"), lambda m, q: api_worldbook(m.group(1))),
    (re.compile(r"^/api/trace$"), lambda m, q: api_trace(q)),
    (re.compile(r"^/api/branches/([\w-]+)/([\w-]+)$"), lambda m, q: api_branches(m.group(1), m.group(2))),
    (re.compile(r"^/api/codex$"), lambda m, q: api_codex()),
    (re.compile(r"^/api/export/thread/([\w-]+)/([\w-]+)$"), lambda m, q: api_export_thread(m.group(1), m.group(2))),
    (re.compile(r"^/api/config$"), lambda m, q: api_config()),
    (re.compile(r"^/api/timeline/([\w-]+)$"), lambda m, q: api_timeline(m.group(1))),
    (re.compile(r"^/api/chat/([\w-]+)/([\w-]+)$"), lambda m, q: api_chat(m.group(1), m.group(2))),
    (re.compile(r"^/api/modes$"), lambda m, q: api_modes()),
    (re.compile(r"^/api/groups$"), lambda m, q: api_groups()),
    (re.compile(r"^/api/group/([\w-]+)$"), lambda m, q: api_group(m.group(1))),
    (re.compile(r"^/api/prep/narrate$"), lambda m, q: api_narrate_prep(q)),
    (re.compile(r"^/api/prep/play$"), lambda m, q: api_play_prep(q)),
    (re.compile(r"^/api/prep/world$"), lambda m, q: api_world_prep(q)),
    (re.compile(r"^/api/recipe$"), lambda m, q: api_recipe(q)),
    (re.compile(r"^/api/presets$"), lambda m, q: api_presets()),
    (re.compile(r"^/api/preset/([\w-]+)$"), lambda m, q: api_preset(m.group(1))),
]
POST_ROUTES = [
    (re.compile(r"^/api/world/create$"), post_world_create),
    (re.compile(r"^/api/world/save-md$"), post_world_save_md),
    (re.compile(r"^/api/entity/create$"), post_entity_create),
    (re.compile(r"^/api/thread/create$"), post_thread_create),
    (re.compile(r"^/api/codex/create$"), post_codex_create),
    (re.compile(r"^/api/codex/seed$"), post_codex_seed),
    (re.compile(r"^/api/narrate/commit$"), post_narrate_commit),
    (re.compile(r"^/api/play/commit$"), post_play_commit),
    (re.compile(r"^/api/ascend$"), post_ascend),
    (re.compile(r"^/api/summon$"), post_summon),
    (re.compile(r"^/api/link$"), post_link),
    (re.compile(r"^/api/extract$"), post_extract),
    (re.compile(r"^/api/summon-soul$"), post_summon_soul),
    (re.compile(r"^/api/create-soul$"), post_create_soul),
    (re.compile(r"^/api/gen/world$"), post_gen_world),
    (re.compile(r"^/api/gen/entity$"), post_gen_entity),
    (re.compile(r"^/api/gen/thread$"), post_gen_thread),
    (re.compile(r"^/api/gen/chapter$"), post_gen_chapter),
    (re.compile(r"^/api/narrate/run$"), post_narrate_run),
    (re.compile(r"^/api/narrate/reflect$"), post_narrate_reflect),
    (re.compile(r"^/api/delete/world$"), post_delete_world),
    (re.compile(r"^/api/delete/thread$"), post_delete_thread),
    (re.compile(r"^/api/delete/entity$"), post_delete_entity),
    (re.compile(r"^/api/delete/codex$"), post_delete_codex),
    (re.compile(r"^/api/unlink$"), post_unlink),
    (re.compile(r"^/api/render/entity$"), post_render_entity),
    (re.compile(r"^/api/render/scene$"), post_render_scene),
    (re.compile(r"^/api/config$"), post_config),
    (re.compile(r"^/api/llm-test$"), post_llm_test),
    (re.compile(r"^/api/hook/add$"), post_hook_add),
    (re.compile(r"^/api/hook/set$"), post_hook_set),
    (re.compile(r"^/api/hook/alpha$"), post_hook_alpha),
    (re.compile(r"^/api/import/card$"), post_import_card),
    (re.compile(r"^/api/import/preset$"), post_import_preset),
    (re.compile(r"^/api/import/regex$"), post_import_regex),
    (re.compile(r"^/api/import/undo$"), post_import_undo),
    (re.compile(r"^/api/world/merge$"), post_world_merge),
    (re.compile(r"^/api/chat$"), post_chat),
    (re.compile(r"^/api/chat/clear$"), post_chat_clear),
    (re.compile(r"^/api/chat/regenerate$"), post_chat_regenerate),
    (re.compile(r"^/api/chat/swipe$"), post_chat_swipe),
    (re.compile(r"^/api/chat/floor-regen$"), post_chat_floor_regen),
    (re.compile(r"^/api/group/new$"), post_group_new),
    (re.compile(r"^/api/group/chat$"), post_group_chat),
    (re.compile(r"^/api/group/clear$"), post_group_clear),
    (re.compile(r"^/api/chat/undo$"), post_chat_undo),
    (re.compile(r"^/api/entity/avatar$"), post_entity_avatar),
    (re.compile(r"^/api/entity/expressions$"), post_entity_expressions),
    (re.compile(r"^/api/player$"), post_player),
    (re.compile(r"^/api/chat/var$"), post_chat_var),
    (re.compile(r"^/api/chat/var/del$"), post_chat_var_del),
    (re.compile(r"^/api/chat/init-vars$"), post_chat_init_vars),
    (re.compile(r"^/api/chat/set-greeting$"), post_chat_set_greeting),
    (re.compile(r"^/api/chat/edit$"), post_chat_edit),
    (re.compile(r"^/api/chat/delete$"), post_chat_delete),
    (re.compile(r"^/api/chat/author-note$"), post_author_note),
    (re.compile(r"^/api/quick-replies$"), post_quick_replies),
    (re.compile(r"^/api/worldbook/save$"), post_worldbook_save),
    (re.compile(r"^/api/worldbook/delete$"), post_worldbook_delete),
    (re.compile(r"^/api/apply-relationship$"), post_apply_relationship),
    (re.compile(r"^/api/checks$"), post_checks),
    (re.compile(r"^/api/convert$"), post_convert),
    (re.compile(r"^/api/branch$"), post_branch),
    (re.compile(r"^/api/preset/module$"), post_preset_module),
]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            return self._send(200, (WEB_DIR / "index.html").read_bytes(), "text/html; charset=utf-8")
        if path in ("/legacy", "/legacy.html"):   # 旧版创作者控制台(完整功能,留作后台工具)
            lp = WEB_DIR / "index.legacy.html"
            if lp.exists():
                return self._send(200, lp.read_bytes(), "text/html; charset=utf-8")
        if path.startswith("/img/"):   # 服务 universe 下的图(防目录穿越)
            from urllib.parse import unquote
            target = (UNIVERSE / unquote(path[len("/img/"):])).resolve()
            root = UNIVERSE.resolve()
            ctype = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(target.suffix.lower())
            if ctype and root in target.parents and target.exists():
                return self._send(200, target.read_bytes(), ctype)
            return self._send(404, b"not found", "text/plain")
        q = _qs(self.path)
        for rx, fn in GET_ROUTES:
            mm = rx.match(path)
            if mm:
                try:
                    return self._json(200, fn(mm, q))
                except (FileNotFoundError, ValueError, KeyError) as e:
                    return self._json(404, {"error": str(e)})
                except Exception as e:  # noqa: BLE001
                    return self._json(500, {"error": repr(e)})
        self._json(404, {"error": "not found"})

    def _sse(self, obj):
        self.wfile.write(b"data: " + json.dumps(obj, ensure_ascii=False).encode("utf-8") + b"\n\n")
        self.wfile.flush()

    def _chat_stream(self, b: dict):
        """流式对话(SSE):逐块吐正文增量,收尾吐 done 元信息(含正则渲染后的整段 reply)。"""
        try:
            w = World.load(b["world"]); e = LocalEntity.load(w, b["entity"])
        except (FileNotFoundError, ValueError, KeyError) as ex:
            return self._json(400, {"error": str(ex)})
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")   # 关代理缓冲,逐块到达
        self.end_headers()
        try:
            for kind, payload in chatmod.stream_turn(w, e, b.get("message", "")):
                if kind == "delta":
                    self._sse({"t": payload})
                else:
                    self._sse({**_regex_out(payload), "done": True})
        except (BrokenPipeError, ConnectionResetError):
            return                                     # 客户端断开,静默收场
        except Exception as ex:  # noqa: BLE001
            try:
                self._sse({"done": True, "error": repr(ex)})
            except Exception:  # noqa: BLE001
                pass

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        n = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._json(400, {"error": "请求体必须是 UTF-8 编码的 JSON"})
        if path == "/api/chat/stream":
            return self._chat_stream(body)
        for rx, fn in POST_ROUTES:
            if rx.match(path):
                try:
                    return self._json(200, fn(body))
                except (FileExistsError, FileNotFoundError, ValueError, KeyError) as e:
                    return self._json(400, {"ok": False, "error": str(e)})
                except Exception as e:  # noqa: BLE001
                    return self._json(500, {"ok": False, "error": repr(e)})
        self._json(404, {"error": "not found"})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="sv-web")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args(argv)
    if not UNIVERSE.exists():
        print(f"⚠ universe 不存在:{UNIVERSE}。可先跑 python -m sim.seed 播种,或在页面里新建。")
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    print(f"暗宇宙控制台 → http://{a.host}:{a.port}  (universe: {UNIVERSE})")
    print("Ctrl+C 退出。")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已退出。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
