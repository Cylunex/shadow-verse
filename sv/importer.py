"""导入器 —— 吃 SillyTavern 角色卡(V1/V2/V3,JSON 或 PNG 内嵌)+ 世界书,落成 entity/世界设定。

借鉴酒馆生态的现成资产(只读其格式,不照搬其实现)。卡→entity profile;世界书→world.md 设定条目。
零依赖:PNG 内嵌卡用标准库解 tEXt chunk(角色卡放 'chara'[v2 base64]/'ccv3'[v3])。
"""
from __future__ import annotations

import base64
import functools
import json
import re
import struct

from . import provenance, util, worldbook
from .config import UNIVERSE, load_json, save_json
from .entity import LocalEntity
from .world import World

LB_MARK = "IMPORT-LOREBOOK"   # world.md 里世界书块的标记(供撤销精确剥离)


def _png_text_chunks(b: bytes) -> dict[str, str]:
    """从 PNG 取 tEXt chunks(keyword→text)。"""
    out: dict[str, str] = {}
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        return out
    i = 8
    while i + 8 <= len(b):
        (length,) = struct.unpack(">I", b[i : i + 4])
        ctype = b[i + 4 : i + 8]
        data = b[i + 8 : i + 8 + length]
        if ctype == b"tEXt" and b"\x00" in data:
            k, v = data.split(b"\x00", 1)
            out[k.decode("latin-1")] = v.decode("latin-1")
        i += 12 + length
        if ctype == b"IEND":
            break
    return out


CARD_SIZE_LIMIT = 8 * 1024 * 1024     # 角色卡(含 PNG)上限 8MB
ASSET_SIZE_LIMIT = 12 * 1024 * 1024   # 世界书/预设/正则上限 12MB


def parse_card(data) -> dict:
    """把 JSON 字符串 / dict / PNG bytes 统一成规范卡字典。"""
    util.guard_size(data, limit=CARD_SIZE_LIMIT, what="角色卡")
    if isinstance(data, bytes) and data[:8] == b"\x89PNG\r\n\x1a\n":
        chunks = _png_text_chunks(data)
        raw = chunks.get("ccv3") or chunks.get("chara")
        if not raw:
            raise ValueError("PNG 里没有内嵌角色卡(chara/ccv3)")
        data = base64.b64decode(raw).decode("utf-8")
    if isinstance(data, (bytes, str)):
        data = json.loads(data)
    if not isinstance(data, dict):
        raise ValueError("无法识别的角色卡格式")
    d = data.get("data", data)   # V2/V3 包在 data 里;V1 是平铺
    ext = d.get("extensions") or {}
    sd = ext.get("sd_character_prompt") or {}
    return {
        "name": d.get("name", "").strip() or "未命名",
        "description": d.get("description", ""),
        "personality": d.get("personality", ""),
        "scenario": d.get("scenario", ""),
        "first_mes": d.get("first_mes", ""),
        "mes_example": d.get("mes_example", ""),
        "system_prompt": d.get("system_prompt", ""),
        "post_history_instructions": d.get("post_history_instructions", ""),
        "alternate_greetings": d.get("alternate_greetings", []) or [],
        "tags": d.get("tags", []) or [],
        "creator": d.get("creator", ""),
        "creator_notes": d.get("creator_notes", ""),
        "character_version": d.get("character_version", ""),
        "character_book": d.get("character_book") or d.get("world_scenario") or None,
        # 扩展字段:SD 正向词→锁脸 appearance;depth_prompt→运行时 @D 注入(角色私货)
        "appearance": (sd.get("positive") or "").strip() if isinstance(sd, dict) else "",
        "depth_prompt": ext.get("depth_prompt") if isinstance(ext.get("depth_prompt"), dict) else None,
        "talkativeness": ext.get("talkativeness"),
        "spec": data.get("spec", "v1"),
    }


def _profile_md(card: dict, eid: str, role: str) -> str:
    def sec(title, body):
        return f"## {title}\n{body.strip()}\n\n" if body and body.strip() else ""
    greetings = "\n\n".join([card["first_mes"], *card["alternate_greetings"]]).strip()
    return (
        f"# {card['name']}\n\n> 实体 id:`{eid}` ｜ 戏份:{role} ｜ 导入自 SillyTavern 角色卡({card['spec']})\n\n"
        + sec("身份", card["description"])
        + sec("Identity Core", card["personality"])
        + sec("声音指纹(对话示例)", card["mes_example"])
        + sec("场景 / 背景", card["scenario"])
        + sec("开场白(参考)", greetings)
        + sec("系统提示(原卡)", card["system_prompt"])
        + "## 核心事实\n<!-- 可由 Agent 从上文精炼为 ≤7 条 anchors -->\n"
    )


def _unique_id(world: World, base: str) -> str:
    """给导入实体一个唯一 id。中文名 slug 退化成 'x',这类一律走 imported-NNN 防撞。"""
    if base and base != "x" and util.is_id(base) and not LocalEntity(world, base).exists():
        return base
    i = 1
    while LocalEntity(world, f"imported-{i:03d}").exists():
        i += 1
    return f"imported-{i:03d}"


def import_card(world: World, card: dict, *, role: str = "secondary", as_id: str | None = None,
                avatar_png: bytes | None = None) -> dict:
    """卡 → 世界内 entity。avatar_png=卡的 PNG 原图(设为头像)。返回 {entity, name, lorebook_entries, avatar}。"""
    name = card["name"]
    eid = as_id if (as_id and util.is_id(as_id)) else _unique_id(world, util.slug(name))
    prov = provenance.stamp("import", prompt=f"ST card:{name}")
    e = LocalEntity.create(world, eid, name, role=role, prov=prov, body=_profile_md(card, eid, role))
    c = e.card()
    if card["tags"]:
        c["tags"] = card["tags"]
    greetings = [g.strip() for g in [card.get("first_mes", ""), *card.get("alternate_greetings", [])] if (g or "").strip()]
    if greetings:
        c["greeting"] = greetings[0]                 # 主开场白(向后兼容)
        if len(greetings) > 1:
            c["greetings"] = greetings               # 多开场白,可在对话页 swipe 选(含 alternate_greetings)
    if card.get("appearance"):
        c["appearance"] = card["appearance"]        # SD 正向词 → 锁脸立绘 appearance
    if card.get("depth_prompt"):
        c["depth_prompt"] = card["depth_prompt"]    # 角色私货,运行时 @D 注入(见 promptkit)
    if card.get("talkativeness") is not None:
        c["talkativeness"] = card["talkativeness"]  # 群聊发言倾向
    save_json(e.card_path, c)
    avatar = e.set_avatar(avatar_png, "png") if avatar_png else None   # PNG 卡图 → 头像/立绘
    n = import_lorebook(world, card.get("character_book"), eid) if card.get("character_book") else 0
    return {"entity": eid, "name": name, "lorebook_entries": n, "avatar": avatar}


def import_lorebook(world: World, book, eid: str) -> int:
    """世界书 entries → 追加到 world.md(带标记块,供撤销精确剥离)。返回条目数。"""
    if not book or not isinstance(book, dict):
        return 0
    entries = book.get("entries") or []
    if isinstance(entries, dict):
        entries = list(entries.values())
    if not entries:
        return 0
    lines = [f"<!-- {LB_MARK}:{eid} -->", f"## 导入世界书(来自角色卡 {eid})"]
    for en in entries:
        keys = en.get("keys") or en.get("key") or []
        kw = "、".join(keys) if isinstance(keys, list) else str(keys)
        const = "常驻" if en.get("constant") else "关键词触发"
        content = (en.get("content") or "").strip()
        comment = (en.get("comment") or "").strip()
        lines.append(f"\n### {comment or kw or '条目'}（{const}）\n触发词:{kw or '—'}\n\n{content}")
    lines.append(f"<!-- /{LB_MARK}:{eid} -->")
    wp = world.dir / "world.md"
    util.write_md(wp, util.read_md(wp).rstrip() + "\n\n" + "\n".join(lines) + "\n")
    # 同时结构化存进世界书触发引擎(运行时按上下文激活,而不只是平铺在 world.md)
    worldbook.add_entries(world, entries, source=eid)
    return len(entries)


def _strip_lorebook(world: World, eid: str) -> None:
    wp = world.dir / "world.md"
    text = util.read_md(wp)
    pat = re.compile(re.escape(f"<!-- {LB_MARK}:{eid} -->") + r".*?" + re.escape(f"<!-- /{LB_MARK}:{eid} -->"), re.S)
    util.write_md(wp, pat.sub("", text).rstrip() + "\n")
    worldbook.remove_source(world, eid)   # 同步从触发引擎剥掉该来源条目


def undo_import(world: World, eid: str) -> dict:
    """撤销一次卡导入:删实体 + 剥掉它并入的世界书块。"""
    e = LocalEntity.load(world, eid)
    if e.card().get("provenance", {}).get("source") != "import":
        raise ValueError(f"{eid} 不是导入的实体(可用「删除实体」)")
    _strip_lorebook(world, eid)
    e.delete()
    return {"undone": eid, "world": world.id}


# ---------- 卡 → 新建独立世界(卡自带世界时推荐)----------
def _derive_world(card: dict) -> tuple[str, str, str]:
    base = util.slug(card["name"])
    wid = base if (base and base != "x" and util.is_id(base)) else "card-world"
    genre = (card.get("tags") or [""])[0] if card.get("tags") else ""
    return wid, f"{card['name']}·世界", genre


def import_card_new_world(card: dict, *, world_id: str | None = None, world_name: str | None = None,
                          role: str = "main", avatar_png: bytes | None = None) -> dict:
    """卡 → 新建独立世界(scenario 作背景 + 世界书作设定),角色落进去。"""
    d_id, d_name, genre = _derive_world(card)
    wid = world_id if (world_id and util.is_id(world_id)) else d_id
    base, i = wid, 1
    while World(wid).exists():
        wid = f"{base}-{i}"; i += 1
    name = world_name or d_name
    body = (f"# {name}\n\n> 世界 id:`{wid}` ｜ 题材:{genre or '未定'} ｜ 导入自 SillyTavern 角色卡\n\n"
            f"## 基调 / 背景\n{(card.get('scenario') or '').strip() or '（卡未给场景,可补充）'}\n\n"
            f"## 核心规则\n<!-- 见下方导入世界书 -->\n")
    w = World.create(wid, name, genre=genre, prov=provenance.stamp("import"), body=body)
    r = import_card(w, card, role=role, avatar_png=avatar_png)
    return {"world": wid, "world_name": name, "new_world": True, **r}


# ========== ST 预设(Chat Completion Preset)==========
# 卡是"角色"、世界书是"设定",**预设是"怎么组织提示词 + 采样参数"**——shadow-verse 此前缺这一层。
# 只读其格式:采样集喂可插拔 LLM;prompts+prompt_order 落成"提示词配方"(有序模块,marker 为占位槽)。
_SAMPLING_KEYS = {
    "temperature": "temperature", "top_p": "top_p", "top_k": "top_k", "top_a": "top_a",
    "min_p": "min_p", "frequency_penalty": "frequency_penalty", "presence_penalty": "presence_penalty",
    "repetition_penalty": "repetition_penalty", "seed": "seed", "openai_max_tokens": "max_tokens",
    "reasoning_effort": "reasoning_effort", "verbosity": "verbosity",
}


def _coerce(data):
    if isinstance(data, bytes):
        data = data.decode("utf-8")
    if isinstance(data, str):
        data = json.loads(data)
    return data


def parse_preset(data, *, name: str = "") -> dict:
    """ST 预设 → {sampling, modules(有序), order}。modules.marker=True 为 ST 注入占位(内容空)。"""
    util.guard_size(data, limit=ASSET_SIZE_LIMIT, what="预设")
    data = _coerce(data)
    if not isinstance(data, dict) or "prompts" not in data:
        raise ValueError("不是 SillyTavern 预设(缺 prompts)")
    sampling = {dst: data[src] for src, dst in _SAMPLING_KEYS.items() if data.get(src) not in (None, "")}
    by_id = {p.get("identifier"): p for p in data.get("prompts", []) if p.get("identifier")}
    order_block = data.get("prompt_order") or []
    order = order_block[-1].get("order", []) if order_block else []
    if not order:   # 无 prompt_order 则按 prompts 原序全启用
        order = [{"identifier": i, "enabled": True} for i in by_id]
    modules, seq = [], []
    for o in order:
        ident = o.get("identifier")
        if not o.get("enabled", True):
            continue
        seq.append(ident)
        p = by_id.get(ident)
        if not p:   # ST 内建占位(worldInfoBefore/charDescription…),保留为槽
            modules.append({"identifier": ident, "name": ident, "role": "system",
                            "marker": True, "content": ""})
            continue
        modules.append({
            "identifier": ident, "name": p.get("name") or ident,
            "role": p.get("role") or "system", "marker": bool(p.get("marker")),
            "content": (p.get("content") or "").strip(),
            "injection_position": p.get("injection_position"),
            "injection_depth": p.get("injection_depth"),
            "injection_order": p.get("injection_order"),
        })
    custom = [m for m in modules if m["content"] and not m["marker"]]
    return {"kind": "preset", "name": name or "导入预设", "sampling": sampling,
            "order": seq, "modules": modules,
            "module_count": len(modules), "custom_count": len(custom)}


def _presets_dir():
    return UNIVERSE / "presets"


def import_preset(data, *, name: str = "", pid: str | None = None) -> dict:
    pre = parse_preset(data, name=name)
    base = pid if (pid and util.is_id(pid)) else util.slug(name or "")
    if not util.is_id(base) or base == "x":   # 中文名 slug 退化成 'x',给个干净基名
        base = "preset"
    pid, i = base, 1
    while (_presets_dir() / f"{pid}.json").exists():
        pid = f"{base}-{i}"; i += 1
    pre["id"] = pid
    pre["provenance"] = provenance.stamp("import", prompt=f"ST preset:{name}")
    save_json(_presets_dir() / f"{pid}.json", pre)
    return {"preset": pid, "name": pre["name"], "module_count": pre["module_count"],
            "custom_count": pre["custom_count"], "sampling": pre["sampling"]}


def list_presets() -> list[dict]:
    d = _presets_dir()
    out = []
    for p in sorted(d.glob("*.json")) if d.exists() else []:
        j = load_json(p, {}) or {}
        out.append({"id": j.get("id", p.stem), "name": j.get("name"),
                    "module_count": j.get("module_count"), "custom_count": j.get("custom_count")})
    return out


def load_preset(pid: str) -> dict:
    j = load_json(_presets_dir() / f"{pid}.json", None)
    if not j:
        raise FileNotFoundError(f"无此预设:{pid}")
    return j


def assemble_preset(preset: dict, slots: dict | None = None) -> str:
    """按 order 拼接预设模块成一段系统提示。marker/占位模块用 slots[identifier] 填(没给则跳过)。

    借鉴 Narratium preset-assembler:有序段落注入。这给"世界书预设"backlog 一个能跑的组装器。
    """
    slots = slots or {}
    parts = []
    for m in preset.get("modules", []):
        if m.get("marker") or not m.get("content"):
            s = slots.get(m["identifier"])
            if s:
                parts.append(s.strip())
        else:
            parts.append(m["content"])
    return "\n\n".join(p for p in parts if p)


# ========== ST 正则脚本(消息渲染/HUD 改写)==========
# 把模型输出按 findRegex→replaceString 改写。**先做文本改写**(忠实替换,含 $1 反向引用);
# replaceString 内嵌的 HTML 面板渲染需前端沙箱化,后置(本层只负责文本变换)。
_PLACEMENT = {"output": 1, "input": 2}
_FIND_DELIM = re.compile(r"^/(.*)/([a-z]*)$", re.S)
_RX_TOKEN = re.compile(r"\$\$|\$&|\$\d{1,2}|\{\{match\}\}")


def parse_regex(data) -> list[dict]:
    """ST 正则脚本(单个或数组)→ 规范化渲染规则列表。"""
    util.guard_size(data, limit=ASSET_SIZE_LIMIT, what="正则脚本")
    data = _coerce(data)
    items = data if isinstance(data, list) else [data]
    out = []
    for raw in items:
        if not isinstance(raw, dict) or "findRegex" not in raw:
            continue
        out.append({
            "name": raw.get("scriptName") or "正则", "find": raw.get("findRegex") or "",
            "replace": raw.get("replaceString") or "", "placement": raw.get("placement") or [1],
            "markdown_only": bool(raw.get("markdownOnly")), "prompt_only": bool(raw.get("promptOnly")),
            "disabled": bool(raw.get("disabled")), "trim": raw.get("trimStrings") or [],
            "min_depth": raw.get("minDepth"), "max_depth": raw.get("maxDepth"),
        })
    if not out:
        raise ValueError("不是 SillyTavern 正则脚本(缺 findRegex)")
    return out


def _regex_dir():
    return UNIVERSE / "regex"


def import_regex(data, *, name: str = "") -> dict:
    scripts = parse_regex(data)
    base = util.slug(name or scripts[0]["name"])
    if not util.is_id(base) or base == "x":   # 中文名 slug 退化成 'x',给个干净基名
        base = "regex"
    rid, i = base, 1
    while (_regex_dir() / f"{rid}.json").exists():
        rid = f"{base}-{i}"; i += 1
    save_json(_regex_dir() / f"{rid}.json", {"id": rid, "kind": "regex", "scripts": scripts,
                                             "provenance": provenance.stamp("import")})
    return {"regex": rid, "count": len(scripts), "names": [s["name"] for s in scripts]}


def list_regex() -> list[dict]:
    d = _regex_dir()
    out = []
    for p in sorted(d.glob("*.json")) if d.exists() else []:
        j = load_json(p, {}) or {}
        out.append({"id": j.get("id", p.stem), "count": len(j.get("scripts", [])),
                    "names": [s.get("name") for s in j.get("scripts", [])]})
    return out


def load_regex_scripts() -> list[dict]:
    """汇总所有已导入、未禁用的正则脚本(供渲染端按 placement 应用)。"""
    d = _regex_dir()
    scripts = []
    for p in sorted(d.glob("*.json")) if d.exists() else []:
        for s in (load_json(p, {}) or {}).get("scripts", []):
            if not s.get("disabled"):
                scripts.append(s)
    return scripts


@functools.lru_cache(maxsize=256)
def _compile_find(find: str):
    """解析 /pat/flags;返回 (compiled, global?)。flags 支持 i/m/s/g。
    lru_cache:同一段 find 在一次进程里只编译一次(api_chat 渲染 N 行历史时,N×S 次降为 S 次)。"""
    m = _FIND_DELIM.match(find or "")
    pat, fl = (m.group(1), m.group(2)) if m else (find or "", "")
    flags = (re.I if "i" in fl else 0) | (re.M if "m" in fl else 0) | (re.S if "s" in fl else 0)
    try:
        return re.compile(pat, flags), ("g" in fl)
    except re.error:
        return None, False


def _expand_repl(m, template: str) -> str:
    """把 ST replaceString 的 $1/$&/$$/{{match}} 用本次匹配展开(函数式,避免 HTML 里的 \\ 被误解析)。"""
    def repl(tok):
        t = tok.group(0)
        if t == "$$":
            return "$"
        if t in ("$&", "{{match}}"):
            return m.group(0)
        idx = int(t[1:])
        try:
            return m.group(idx) or ""
        except (re.error, IndexError):
            return ""
    return _RX_TOKEN.sub(repl, template)


def apply_regex(text: str, scripts: list[dict], *, scope: str = "output", depth: int | None = None) -> str:
    """按 placement/depth 链式套用正则脚本改写文本(忠实替换;HTML 面板渲染由前端沙箱负责)。"""
    code = _PLACEMENT.get(scope, 1)
    for s in scripts or []:
        if s.get("disabled") or code not in (s.get("placement") or [1]):
            continue
        if depth is not None:
            if s.get("min_depth") is not None and depth < s["min_depth"]:
                continue
            if s.get("max_depth") is not None and depth > s["max_depth"]:
                continue
        cre, g = _compile_find(s.get("find", ""))
        if cre is None:
            continue
        text = cre.sub(lambda m: _expand_repl(m, s.get("replace", "")), text, count=0 if g else 1)
        for t in s.get("trim") or []:
            text = text.replace(t, "")
    return text
