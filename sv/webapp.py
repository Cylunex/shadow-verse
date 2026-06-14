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

from . import codex, config, export, forge, lenses, llm, memory, nexus, recipes, util
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
    return {"meta": m, "thread_md": util.read_md(t.dir / "thread.md"), "summary_md": t.summary(),
            "chapters": chapters, "beats": t.beats(), "sessions": sessions,
            "recipe": recipes.get(m.get("genre", "")),
            "entities": [{"id": e, "name": LocalEntity(w, e).card().get("name", e),
                          "role": LocalEntity(w, e).card().get("role", "")} for e in w.list_entities()]}


def api_entity(wid: str, eid: str) -> dict:
    w = World.load(wid); e = LocalEntity.load(w, eid)
    return {"card": e.card(), "profile_md": util.read_md(e.dir / "profile.md"),
            "state": memory.read_state(e.dir), "anchors": e.anchors(),
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
    e = LocalEntity.create(w, b["id"], b.get("name", b["id"]), role=b.get("role", "secondary"))
    if b.get("profile_md"):
        util.write_md(e.dir / "profile.md", b["profile_md"])
    return {"ok": True, "id": e.id}


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
    (re.compile(r"^/api/codex$"), lambda m, q: api_codex()),
    (re.compile(r"^/api/export/thread/([\w-]+)/([\w-]+)$"), lambda m, q: api_export_thread(m.group(1), m.group(2))),
    (re.compile(r"^/api/prep/narrate$"), lambda m, q: api_narrate_prep(q)),
    (re.compile(r"^/api/prep/play$"), lambda m, q: api_play_prep(q)),
    (re.compile(r"^/api/prep/world$"), lambda m, q: api_world_prep(q)),
    (re.compile(r"^/api/recipe$"), lambda m, q: api_recipe(q)),
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

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        n = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._json(400, {"error": "请求体必须是 UTF-8 编码的 JSON"})
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
