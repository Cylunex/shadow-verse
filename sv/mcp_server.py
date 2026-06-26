"""零依赖 stdio MCP server —— 把工具调用翻译成等价 skill_api CLI argv 并复用之(零回归)。

typed 参数根治弱模型拼 JSON heredoc 的脆弱性。跑:python -m sv.mcp_server
"""
from __future__ import annotations

import io
import json
import os
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
    ("import_card", "导入 SillyTavern 角色卡(JSON/PNG 路径)→ 并入现有世界", {"world": "str", "path": "str", "role": "str"}, ["world", "path"], ["role"], False),
    ("import_card_world", "导入卡 → 新建独立世界(卡自带世界时推荐)", {"path": "str", "role": "str"}, ["path"], ["role"], False),
    ("undo_import", "撤销一次卡导入(删实体+剥世界书)", {"world": "str", "entity": "str"}, ["world", "entity"], [], False),
    ("merge_world", "世界融合:把 src 融进 dst(角色/线/设定)", {"src": "str", "dst": "str"}, ["src", "dst"], [], False),
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
    ("expr_gen", "锁脸预生成一组情绪立绘(seed+appearance 锁脸→portraits/<emotion>.png)", {"world": "str", "entity": "str", "emotions": "str"}, ["world", "entity"], ["emotions"], False),
    ("expr_classify", "给一段文本分类情绪(neutral/joy/anger/…)", {"text": "str"}, ["text"], [], False),
    ("ascend", "L4 升格:本地实体→跨世界枢纽实体", {"world": "str", "entity": "str"}, ["world", "entity"], [], False),
    ("summon", "L4 召唤:跨世界实体进入某世界开化身", {"nexus_id": "str", "world": "str", "entry": "str"}, ["nexus_id", "world"], ["entry"], False),
    ("link", "L4 世界互联:连一条暗宇宙边", {"world_a": "str", "world_b": "str", "relation": "str", "note": "str"}, ["world_a", "world_b", "relation"], ["note"], False),
    ("nexus", "L4 枢纽鸟瞰", {}, [], [], False),
    ("hooks", "看钩子台账(α悬念+各钩状态+过期未回收)", {"world": "str", "thread": "str"}, ["world", "thread"], [], False),
    ("hook_add", "加钩子(type:event/concept,level:α/主/中/细)", {"world": "str", "thread": "str", "desc": "str", "type": "str", "level": "str", "payoff": "int"}, ["world", "thread", "desc"], ["type", "level", "payoff"], False),
    ("hook_set", "改钩子状态(待回收/进行中/已回收/顺延/放弃)或回收章", {"world": "str", "thread": "str", "hid": "str", "status": "str", "payoff": "int"}, ["world", "thread", "hid"], ["status", "payoff"], False),
    ("hook_alpha", "设全书唯一 α 悬念", {"world": "str", "thread": "str", "text": "str"}, ["world", "thread", "text"], [], False),
    ("check", "确定性质检某章", {"world": "str", "thread": "str", "chapter": "int"}, ["world", "thread", "chapter"], [], False),
    ("check_book", "全书纵向基线(句式tic章均/跨章逐字复读/章末同构/开篇套路;last 限近 N 章)", {"world": "str", "thread": "str", "last": "int"}, ["world", "thread"], ["last"], False),
    ("worldbook", "世界书触发引擎:给 context 则返回激活条目,否则列全部条目", {"world": "str", "context": "str"}, ["world"], ["context"], False),
    ("import_preset", "导入 ST 预设(采样集+有序提示词模块)", {"path": "str", "name": "str", "id": "str"}, ["path"], ["name", "id"], False),
    ("import_regex", "导入 ST 正则脚本(消息渲染改写规则)", {"path": "str", "name": "str"}, ["path"], ["name"], False),
    ("presets", "列出已导入的预设与正则脚本", {}, [], [], False),
    ("group_new", "建群聊(members=逗号分隔的实体 id)", {"id": "str", "world": "str", "members": "str", "name": "str"}, ["id", "world", "members"], ["name"], False),
    ("group_chat", "群聊一回合(自动选发言人,多角色轮流)", {"id": "str", "message": "str"}, ["id", "message"], [], False),
    ("groups", "列出所有群聊", {}, [], [], False),
    ("branch_new", "从某章分叉出平行线分支(带蝴蝶效应)", {"world": "str", "thread": "str", "from_chapter": "int", "name": "str", "divergence": "str"}, ["world", "thread", "from_chapter"], ["name", "divergence"], False),
    ("branches", "列出某线的所有分支", {"world": "str", "thread": "str"}, ["world", "thread"], [], False),
    ("skills", "列出写作 skill(给 read 则取该 skill 正文)", {"read": "str"}, [], ["read"], False),
    ("skills_seed", "灌入起始写作 skill(反套话/嗓音/事件摘要)", {}, [], [], False),
    ("card_prep", "一句话→角色卡生成包(8必填字段+题材配方)", {"concept": "str", "genre": "str", "tags": "str"}, ["concept"], ["genre", "tags"], False),
    ("worldbook_prep", "一句话→世界书生成包(四类条目内容规范)", {"concept": "str", "genre": "str"}, ["concept"], ["genre"], False),
    ("gen_card", "AIGC 据概念生成一张角色卡草稿(需 SV_PROVIDER)", {"concept": "str", "genre": "str", "tags": "str"}, ["concept"], ["genre", "tags"], False),
    ("modes", "列出体验模式;给 mode 则取该模式的提示模板包(酒馆RP/小说/CYOA/剧本/漫画/跑团/梦境…)", {"mode": "str", "group": "str", "genre": "str"}, [], ["mode", "group", "genre"], False),
    ("convert", "模式间数据互通(chat→小说/小说章→cyoa/beats→剧本;--to 指定目标)", {"world": "str", "entity": "str", "thread": "str", "chapter": "int", "to": "str"}, ["world"], ["entity", "thread", "chapter", "to"], False),
    ("status", "暗宇宙/世界/线状态", {"world": "str", "thread": "str"}, [], ["world", "thread"], False),
    ("doctor", "引擎自检", {}, [], [], False),
]
_BY = {t[0]: t for t in TOOLS}

# 工具分层(OPENCLAW A1):看板娘主回路只需 Tier1,免 ~60 工具一股脑塞进 agent loop。
# tools/list 暴露层级由环境变量 SV_MCP_TIER 控制(1=只主回路 / 2=含创作质量 / 缺省或 3=全暴露,向后兼容);
# 工具语义/可调用性不变——分层只收敛"广告面",任何工具仍可被 tools/call 直接调。
_TIER1 = {"play_prep", "play_commit", "group_new", "group_chat", "status",
          "nexus", "summon", "ascend", "link", "expr_classify", "doctor"}   # RP/陪伴 + 切角色 + 导航/暗宇宙
_TIER3 = {"gen_world", "gen_entity", "gen_thread", "gen_chapter", "gen_card",  # 单机一键/休眠/调试
          "render_prep", "render_commit", "render_entity", "expr_gen",
          "simulate_prep", "simulate_commit", "codex_add", "codex_seed", "presets"}


def _tier(name: str) -> int:
    return 1 if name in _TIER1 else (3 if name in _TIER3 else 2)   # 其余=Tier2(创作/质量,按需)


def _exposed_tools():
    cap = os.environ.get("SV_MCP_TIER", "").strip()
    if cap in ("1", "2"):
        lim = int(cap)
        return [t for t in TOOLS if _tier(t[0]) <= lim]
    return TOOLS


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
    old_o, old_i, old_e = sys.stdout, sys.stdin, sys.stderr
    sys.stdout = io.StringIO(); sys.stderr = io.StringIO()
    if reads:
        sys.stdin = io.StringIO(json.dumps(args.get("payload", {}), ensure_ascii=False))
    code, extra = 1, ""
    try:
        code = skill_api.main(argv)
    except SystemExit as e:        # argparse 缺必填/坏参:转退出码,不让 server 崩
        code = e.code if isinstance(e.code, int) else 1
    except Exception as e:         # 引擎抛错(世界不存在等):转结构化 isError(弱模型乱传也不崩)
        code, extra = 1, f"{type(e).__name__}: {e}"
    finally:
        text, errtext = sys.stdout.getvalue(), sys.stderr.getvalue()
        sys.stdout, sys.stdin, sys.stderr = old_o, old_i, old_e
    body = "\n".join(s for s in (text.strip(), errtext.strip(), extra) if s) or "(无输出)"
    return {"isError": code != 0, "content": [{"type": "text", "text": body}]}


def _handle(req):
    mid, method = req.get("id"), req.get("method")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "shadowverse", "version": "0.2.0"}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": [{"name": n, "description": d, "inputSchema": _schema(p, pos)} for n, d, p, pos, _, _ in _exposed_tools()]}}
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
