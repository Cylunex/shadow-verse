"""零依赖 stdio MCP server —— 把工具调用翻译成等价 skill_api CLI argv 并复用之(零回归)。

typed 参数根治弱模型拼 JSON heredoc 的脆弱性。跑:python -m sv.mcp_server
"""
from __future__ import annotations

import io
import json
import sys

from . import skill_api

try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    sys.stdin.reconfigure(encoding="utf-8")    # type: ignore[attr-defined]
except Exception:
    pass

# (工具名, 描述, props, 位置参数键, 选项键, 读stdin payload?)
TOOLS = [
    ("codex_add", "L0 元件入库(category∈worlds/mechanics/characters/conflicts/organizations/scenes/themes)",
     {"category": "str", "id": "str", "summary": "str", "tags": "str", "body": "str"}, ["category", "id"], ["summary", "tags", "body"], False),
    ("codex_seed", "幂等灌入起始元件库(~40 个亲手提炼的抽象元件)", {}, [], [], False),
    ("world_prep", "L1 锻造世界:取元件+题材配方+约束,返回生成包", {"prompt": "str", "tags": "str", "genre": "str"}, ["prompt"], ["tags", "genre"], False),
    ("recipes", "查看题材配方(pacing/爽点/疲劳词/侧重)", {"genre": "str"}, [], ["genre"], False),
    ("gen_world", "AIGC 生成 world.md 正文(需配 SV_PROVIDER;单机用)", {"prompt": "str", "genre": "str", "tags": "str"}, ["prompt"], ["genre", "tags"], False),
    ("gen_entity", "AIGC 生成 profile.md 正文", {"world": "str", "prompt": "str", "role": "str"}, ["world", "prompt"], ["role"], False),
    ("gen_thread", "AIGC 生成 thread.md 正文", {"world": "str", "prompt": "str"}, ["world", "prompt"], [], False),
    ("gen_chapter", "AIGC 写下一章(正文+结构化沉淀,供审后 commit)", {"world": "str", "thread": "str", "intent": "str"}, ["world", "thread"], ["intent"], False),
    ("narrate_run", "narrate 产线:写手→审校→修订→落章(需配 SV_PROVIDER;单机一键)", {"world": "str", "thread": "str", "intent": "str"}, ["world", "thread"], ["intent"], False),
    ("review_prep", "审校包:交宿主审校子代理独立查某章(传 chapter 章号)", {"world": "str", "thread": "str", "chapter": "int"}, ["world", "thread", "chapter"], [], False),
    ("reflect_prep", "反思包:交宿主反思子代理横向校验最近 N 章", {"world": "str", "thread": "str", "last": "int"}, ["world", "thread"], ["last"], False),
    ("world_commit", "落世界(payload:{id,name,genre,scale,body})", {"payload": "object"}, [], [], True),
    ("entity_prep", "L1 锻造实体:返回生成包", {"world": "str", "prompt": "str", "tags": "str"}, ["world", "prompt"], ["tags"], False),
    ("entity_commit", "落实体(payload:{id,name,role,body})", {"world": "str", "payload": "object"}, ["world"], [], True),
    ("thread_prep", "L1 锻造叙事线:返回生成包", {"world": "str", "prompt": "str", "tags": "str"}, ["world", "prompt"], ["tags"], False),
    ("thread_commit", "落线(payload:{id,title,genre,pacing,body})", {"world": "str", "payload": "object"}, ["world"], [], True),
    ("narrate_prep", "读透镜:组装写作包", {"world": "str", "thread": "str", "focus": "str", "intent": "str"}, ["world", "thread"], ["focus", "intent"], False),
    ("narrate_commit", "读透镜:落章+沉淀(payload:{chapter_text,title,sediments,state_updates,summary})", {"world": "str", "thread": "str", "payload": "object"}, ["world", "thread"], [], True),
    ("play_prep", "玩透镜:场景包", {"world": "str", "thread": "str", "scene": "str", "entities": "str"}, ["world", "thread"], ["scene", "entities"], False),
    ("play_commit", "玩透镜:落 session+条件成长(payload:{scene,transcript,growth})", {"world": "str", "thread": "str", "payload": "object"}, ["world", "thread"], [], True),
    ("simulate_prep", "模拟透镜(自演化,默认关):自主行动包", {"world": "str", "thread": "str"}, ["world", "thread"], [], False),
    ("simulate_commit", "模拟透镜:落自主 beats(payload:{beats})", {"world": "str", "thread": "str", "payload": "object"}, ["world", "thread"], [], True),
    ("render_prep", "渲染透镜(多模态):组装图像 prompt", {"world": "str", "subject": "str", "appearance": "str"}, ["world"], ["subject", "appearance"], False),
    ("render_commit", "渲染透镜:出场景图(需配 GITEE_API_KEY)", {"world": "str", "thread": "str", "subject": "str", "appearance": "str"}, ["world", "thread"], ["subject", "appearance"], False),
    ("render_entity", "渲染透镜:出角色立绘(用实体 appearance 锁脸)", {"world": "str", "entity": "str", "scene": "str"}, ["world", "entity"], ["scene"], False),
    ("ascend", "L4 升格:本地实体→跨世界枢纽实体", {"world": "str", "entity": "str"}, ["world", "entity"], [], False),
    ("summon", "L4 召唤:跨世界实体进入某世界开化身", {"nexus_id": "str", "world": "str", "entry": "str"}, ["nexus_id", "world"], ["entry"], False),
    ("link", "L4 世界互联:连一条暗宇宙边", {"world_a": "str", "world_b": "str", "relation": "str", "note": "str"}, ["world_a", "world_b", "relation"], ["note"], False),
    ("nexus", "L4 枢纽鸟瞰", {}, [], [], False),
    ("check", "确定性质检某章", {"world": "str", "thread": "str", "chapter": "int"}, ["world", "thread", "chapter"], [], False),
    ("status", "暗宇宙/世界/线状态", {"world": "str", "thread": "str"}, [], ["world", "thread"], False),
    ("doctor", "引擎自检", {}, [], [], False),
]
_BY = {t[0]: t for t in TOOLS}


def _schema(props, required):
    tm = {"str": "string", "int": "integer", "object": "object"}
    return {"type": "object", "properties": {k: {"type": tm.get(v, "string")} for k, v in props.items()}, "required": required}


def _call(name, args):
    t = _BY.get(name)
    if not t:
        return {"isError": True, "content": [{"type": "text", "text": f"未知工具:{name}"}]}
    _, _, _, pos, opt, reads = t
    argv = [name.replace("_", "-")] + [str(args[k]) for k in pos if k in args and args[k] is not None]
    for k in opt:
        if k in args and args[k] not in (None, ""):
            argv += [f"--{k}", str(args[k])]
    old_o, old_i = sys.stdout, sys.stdin
    sys.stdout = io.StringIO()
    if reads:
        sys.stdin = io.StringIO(json.dumps(args.get("payload", {}), ensure_ascii=False))
    try:
        code = skill_api.main(argv)
        text = sys.stdout.getvalue()
    finally:
        sys.stdout, sys.stdin = old_o, old_i
    return {"isError": code != 0, "content": [{"type": "text", "text": text or "(无输出)"}]}


def _handle(req):
    mid, method = req.get("id"), req.get("method")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "shadowverse", "version": "0.2.0"}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": [{"name": n, "description": d, "inputSchema": _schema(p, pos)} for n, d, p, pos, _, _ in TOOLS]}}
    if method == "tools/call":
        pr = req.get("params", {})
        return {"jsonrpc": "2.0", "id": mid, "result": _call(pr.get("name", ""), pr.get("arguments", {}))}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if method and method.startswith("notifications/"):
        return None
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = _handle(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
