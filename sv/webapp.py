"""暗宇宙 · 网页控制台 —— 薄分发器 + 静态/图片服务 + 启动。

路由处理器按「薄路由」原则拆到 sv/web_routes.py(纯搬运,零行为变化);本文件只留
HTTP 壳(Handler)、静态/图片服务(防目录穿越)与 main()。GET/POST 路由表从 web_routes 引入。
默认只绑 127.0.0.1(单机本地工具)。跑:python -m sv.webapp [--port 8787]
"""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import chat as chatmod
from .config import UNIVERSE
from .entity import LocalEntity   # Handler._chat_stream 用
from .world import World          # Handler._chat_stream 用

WEB_DIR = Path(__file__).resolve().parent / "web"

# 路由表 + 处理器(含测试/兼容直接引用的若干处理器与正则渲染助手)从拆出的 web_routes 引入。
from .web_routes import (  # noqa: E402
    GET_ROUTES, POST_ROUTES, _qs, _regex_out, _regex_render,
    api_overview, api_world, api_drives, api_soul_incarnations,
    post_entity_save, post_render_cover,
)


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
        if path in ("/components", "/components.html"):   # 创作组件库管理台(开发者向:工艺/配方/名词库/大纲)
            cp = WEB_DIR / "components.html"
            if cp.exists():
                return self._send(200, cp.read_bytes(), "text/html; charset=utf-8")
        if path.startswith("/img/"):   # 服务 universe 下的图(防目录穿越)
            from urllib.parse import unquote
            target = (UNIVERSE / unquote(path[len("/img/"):])).resolve()
            root = UNIVERSE.resolve()
            ctype = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(target.suffix.lower())
            if ctype and root in target.parents and target.exists():
                return self._send(200, target.read_bytes(), ctype)
            return self._send(404, b"not found", "text/plain")
        if path.startswith("/static/"):   # 服务 sv/web/static 下的 CSS/JS(防目录穿越)
            from urllib.parse import unquote
            sroot = (WEB_DIR / "static").resolve()
            target = (sroot / unquote(path[len("/static/"):])).resolve()
            ctype = {".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8"}.get(target.suffix.lower())
            if ctype and sroot in target.parents and target.exists():
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
