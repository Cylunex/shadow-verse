"""L1 · 锻造器(AIGC 核心)—— 从元件 + 一句话生成自洽的世界 / 实体 / 线。

每个锻造器两步(Model A):prep 组装生成上下文(取元件 + 约束 + 已有世界供一致性)→
宿主 Agent 生成正文 → commit 落盘并盖谱系(provenance)。这是"海量世界生成"的引擎。
"""
from __future__ import annotations

import json

from . import codex, llm, provenance, recipes, util
from .entity import LocalEntity
from .thread import Thread
from .world import World

WORLD_GUIDE = [
    "产出一个自洽世界的 world.md:基调/氛围 + 4-6 条核心规则(每条带触发关键词) + 核心冲突 + 时间设定 + 12 模块。",
    "若与已有世界连接(暗宇宙),在『与其它世界的连接』写清接口(裂隙/同源/传承…)。",
    "声明尺度基线与世界契约(外来实体进出规则)。规则要能落到人能感受的后果,别停在设定讲解。",
]
ENTITY_GUIDE = [
    "产出一个实体的 profile.md:身份 + Identity Core(3-5 条刚性) + 声音指纹(签名句型) + 核心欲望与底线 + 核心事实(≤7,作 anchors)。",
    "贴合所在世界的规则与基调;给一个能驱动剧情的欲望与一条不可退的底线。",
]
THREAD_GUIDE = [
    "产出一条线的 thread.md:立意 + 节奏契约(每章必推进什么) + 大纲(α 悬念统领的 beats/钩子/爽点)。",
    "钩子分两类:事件钩子(带回收)/ 概念阶梯(按层推进)。一章主推一条钩子的下一层。",
]


# ========== 创作包:一句话 → 完整角色卡 + 世界书(吸收 Narratium 创作 Agent 内容规范)==========
# 角色卡 8 必填字段(按完成度门控顺序填:先骨架后细节)
CARD_FIELDS = [
    ("name", "角色名"),
    ("description", "身份/外形/背景(200-500字)"),
    ("personality", "性格内核 + Identity Core 刚性底线"),
    ("scenario", "出场场景/初始处境"),
    ("first_mes", "开场白(第一人称,带画面)"),
    ("mes_example", "对话样本(声音指纹,<START>{{char}}: …)"),
    ("tags", "题材/标签数组"),
    ("appearance", "英文锁脸外貌词(发色/瞳色/服装/特征,供出图)"),
]

# 四类世界书的内容规范(constant/order/position + 字数 + 结构);宿主据此生成结构化条目
WORLDBOOK_CLASSES = {
    "STATUS": {"role": "实时状态面板", "constant": True, "order": 1, "position": 0,
               "spec": "固定关键词常驻;<status> 包裹的游戏界面排版,含时间/地点/角色状态/数值进度条。简洁、信息密度高。"},
    "USER_SETTING": {"role": "玩家角色档", "constant": True, "order": 2, "position": 0,
                     "spec": "玩家扮演谁:身份/能力/初始处境/与主角关系。四级 markdown,800-1500 字。"},
    "WORLD_VIEW": {"role": "世界基础框架", "constant": True, "order": 3, "position": 0,
                   "spec": "世界规则/势力/地理/历史的多级分类框架。是 SUPPLEMENT 取名词的来源。"},
    "SUPPLEMENT": {"role": "设定补充条目", "constant": False, "order": 10, "position": 2,
                   "spec": "从 WORLD_VIEW 提非空名词作 keys 上下文触发;每条 500-1000 字,≥5 条。"},
}


def card_prep(concept: str, *, genre: str = "", tags=None) -> dict:
    """一句话概念 → 角色卡生成包:8 必填字段(按顺序填)+ 题材配方 + 取料。供宿主/LLM 生成,人审后落。"""
    picks = _picks(concept, "characters", tags)
    return {
        "kind": "card", "concept": concept, "genre": genre,
        "required_fields": [f for f, _ in CARD_FIELDS],
        "field_specs": {f: spec for f, spec in CARD_FIELDS},
        "recipe": recipes.get(genre), "codex": [p.get("id") for p in picks],
        "guide": ["按字段顺序逐项填(先 name/description 骨架,后 mes_example/appearance 细节);",
                  "Identity Core 给 3-5 条刚性底线;appearance 用英文锁脸词供出图;",
                  "对话样本要体现独特嗓音(句长/口头禅/回避什么)。"],
    }


def worldbook_prep(concept: str, *, genre: str = "") -> dict:
    """一句话概念 → 世界书生成包:四类条目内容规范(STATUS/USER_SETTING/WORLD_VIEW/SUPPLEMENT)。"""
    return {
        "kind": "worldbook", "concept": concept, "genre": genre,
        "classes": WORLDBOOK_CLASSES, "recipe": recipes.get(genre),
        "order": ["STATUS", "USER_SETTING", "WORLD_VIEW", "SUPPLEMENT"],
        "guide": ["严格按 STATUS→USER_SETTING→WORLD_VIEW→SUPPLEMENT 顺序生成;",
                  "前三类 constant 常驻、SUPPLEMENT 关键词触发;",
                  "SUPPLEMENT 的 keys 必须来自 WORLD_VIEW 里出现的名词,≥5 条。"],
    }


def gen_card(concept: str, *, genre: str = "", tags=None) -> dict:
    """AIGC 据概念生成一张角色卡(需 LLM)。返回卡字典草稿供人审后导入/落盘。"""
    pkt = card_prep(concept, genre=genre, tags=tags)
    sys = "你是暗宇宙的角色设计师,据概念产出一张自洽角色卡,只输出一个 JSON。"
    fields = "；".join(f"{f}({spec})" for f, spec in CARD_FIELDS)
    user = (f"概念:{concept}\n题材:{genre or '未定'}\n"
            f"按这些字段产出 JSON(tags 为数组,其余字符串):{fields}\n"
            "只输出 JSON,不要解释。")
    from . import jsonloose
    j = jsonloose.loads(llm.generate(sys, user, max_tokens=1500), {})
    return {f: j.get(f, "") for f, _ in CARD_FIELDS} | {"_concept": concept, "_genre": genre}


def _picks(query: str, category: str = "", tags=None) -> list[dict]:
    return codex.pick(query, category=category, tags=tags or [], k=8)


# ---------- 世界 ----------
def world_prep(prompt: str, *, tags=None, genre: str = "") -> dict:
    picks = _picks(prompt, tags=tags)
    rec = {"recipe": recipes.get(genre)} if genre else {"available_genres": recipes.genres()}
    return {
        "forge": "world", "prompt": prompt, "genre": genre,
        "codex": [{"id": p["id"], "category": p["category"], "summary": p["summary"]} for p in picks],
        "existing_worlds": [{"id": w, "name": World.load(w).meta().get("name")} for w in World.list_all()],
        "guide": WORLD_GUIDE, **rec,
        "commit_hint": "生成 world.md 正文后调 world-commit --json {id,name,genre,scale,body}",
    }


def world_commit(wid: str, name: str, body: str, *, genre: str = "", scale: str = "max",
                 prompt: str = "", from_codex=None) -> dict:
    prov = provenance.stamp("forge", prompt=prompt, from_codex=from_codex or [])
    w = World.create(wid, name, genre=genre, scale=scale, prov=prov, body=body)
    return {"world": wid, "name": name, "dir": str(w.dir), "provenance": prov["source"]}


# ---------- 实体 ----------
def entity_prep(world: World, prompt: str, *, tags=None) -> dict:
    picks = _picks(prompt, category="characters", tags=tags)
    return {
        "forge": "entity", "prompt": prompt, "world": world.id,
        "world_setting": util.read_md(world.dir / "world.md")[:2000],
        "canon": util.read_md(world.dir / "canon.md"),
        "codex": [{"id": p["id"], "summary": p["summary"]} for p in picks],
        "genre_emphasis": recipes.get(world.meta().get("genre", "")).get("emphasis", []),
        "guide": ENTITY_GUIDE,
        "commit_hint": "生成 profile.md 后调 entity-commit --json {id,name,role,body}",
    }


def entity_commit(world: World, eid: str, name: str, body: str, *, role: str = "secondary",
                  prompt: str = "", from_codex=None) -> dict:
    prov = provenance.stamp("forge", prompt=prompt, from_codex=from_codex or [])
    e = LocalEntity.create(world, eid, name, role=role, prov=prov, body=body)
    return {"entity": eid, "name": name, "role": e.role, "dir": str(e.dir)}


# ---------- 线 ----------
def thread_prep(world: World, prompt: str, *, tags=None) -> dict:
    picks = _picks(prompt, tags=tags)
    pkg = {
        "forge": "thread", "prompt": prompt, "world": world.id,
        "world_setting": util.read_md(world.dir / "world.md")[:2000],
        "canon": util.read_md(world.dir / "canon.md"),
        "entities": world.list_entities(),
        "codex": [{"id": p["id"], "category": p["category"], "summary": p["summary"]} for p in picks],
        "recipe": recipes.get(world.meta().get("genre", "")),
        "guide": THREAD_GUIDE,
        "commit_hint": "生成 thread.md 后调 thread-commit --json {id,title,genre,pacing,body}",
    }
    terms = (world.glossary() or {}).get("terms", [])   # C2:世界已有名词库则注入,新线沿用规范命名(无则休眠)
    if terms:
        pkg["glossary"] = terms
    return pkg


def thread_commit(world: World, tid: str, title: str, body: str, *, genre: str = "",
                  pacing: str = "每章至少推进一条主线钩子", prompt: str = "", from_codex=None) -> dict:
    prov = provenance.stamp("forge", prompt=prompt, from_codex=from_codex or [])
    t = Thread.create(world, tid, title, genre=genre, pacing=pacing, prov=prov)
    if body:
        util.write_md(t.dir / "thread.md", body)
    return {"thread": tid, "title": title, "dir": str(t.dir)}


# ========== AIGC 生成(可插拔 LLM;单机一键造)——返回正文供人审后 commit ==========
def _codex_lines(picks) -> str:
    return "\n".join(f"- [{p['category']}] {p['id']}:{p['summary']}" for p in picks) or "（暂无元件,自由发挥）"


def generate_world_body(prompt: str, *, genre: str = "", tags=None) -> str:
    pkt = world_prep(prompt, tags=tags, genre=genre)
    sys = "你是暗宇宙的世界锻造师,产出一份自洽、有戏剧张力、规则落到可感后果的 world.md(中文,Markdown)。" + " ".join(WORLD_GUIDE)
    user = [f"一句话设定:{prompt}", f"题材:{genre or '自定'}"]
    if "recipe" in pkt:
        user.append("题材配方:" + json.dumps(pkt["recipe"], ensure_ascii=False))
    user.append("可选用并组合的元件:\n" + _codex_lines(pkt["codex"]))
    if pkt.get("existing_worlds"):
        user.append("已存在的世界(可在『与其它世界的连接』里呼应):" + json.dumps(pkt["existing_worlds"], ensure_ascii=False))
    user.append("直接输出完整 world.md 正文,不要额外解释。")
    return llm.generate(sys, "\n\n".join(user))


def generate_entity_body(world: World, prompt: str, *, role: str = "secondary") -> str:
    pkt = entity_prep(world, prompt)
    sys = "你是暗宇宙的角色锻造师,产出一份贴合世界、能驱动剧情的 profile.md(中文,Markdown)。" + " ".join(ENTITY_GUIDE)
    user = [f"角色概念:{prompt}", f"戏份:{role}", f"所在世界设定(节选):\n{pkt['world_setting']}",
            "本世界侧重:" + "、".join(pkt.get("genre_emphasis", [])),
            "可参考的角色原型元件:\n" + _codex_lines(pkt["codex"]),
            "直接输出完整 profile.md,必须含『## 核心事实』段(≤7 条,作 anchors)。"]
    return llm.generate(sys, "\n\n".join(user))


def generate_thread_body(world: World, prompt: str) -> str:
    pkt = thread_prep(world, prompt)
    sys = "你是暗宇宙的叙事锻造师,产出一条有 α 悬念统领、节奏契约清晰的 thread.md(中文,Markdown)。" + " ".join(THREAD_GUIDE)
    user = [f"叙事概念:{prompt}", f"所在世界设定(节选):\n{pkt['world_setting']}",
            "题材配方:" + json.dumps(pkt["recipe"], ensure_ascii=False),
            f"世界现有角色:{pkt['entities']}",
            "可参考元件:\n" + _codex_lines(pkt["codex"]),
            "直接输出完整 thread.md(立意+节奏契约+大纲+钩子台账)。"]
    return llm.generate(sys, "\n\n".join(user))
