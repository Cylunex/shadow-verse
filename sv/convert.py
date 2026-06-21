"""数据互通 —— 模式间一键转换(《参考功能.txt》数据流整合的核心)。

枢纽 = thread.beats(跨透镜事件日志)+ chapters(小说)+ chat(对话)。任一模式的产出可转成另一模式的输入:
  RP聊天 → 小说章节 / CYOA分支 ;小说 → 剧本场景 / 跑团日志 ;beats → 剧本 / 战役日志。
每个转换器返回「转换包」(源材料 + 目标模式模板),供宿主/LLM 实际改写(人在环);配 LLM 则给一键生成。
零依赖。
"""
from __future__ import annotations

from . import chat as chatmod
from . import jsonloose, llm, modes
from .entity import LocalEntity
from .thread import Thread
from .world import World

# (from, to) → 该转换的提示指引
_GUIDE = {
    ("chat", "novel"): "把这段对话/扮演记录改写成第三人称小说章节正文:保留情节与情感,补叙述与场景,去掉『谁:』标签。",
    ("chat", "cyoa"): "把这段对话改写成互动小说:在关键决策处停下,给 2-4 个有实质差异的编号选项。",
    ("novel", "cyoa"): "把这章小说改写成互动小说分支:找出关键抉择点,给编号选项(每项标 advance-beat 或 change-scene)。",
    ("novel", "screenplay"): "把这章小说转成剧本格式:场景头(INT./EXT.+地点+时间)、动作行、角色名+对白、必要的括号镜头提示。",
    ("beats", "screenplay"): "把这些事件 beats 编成剧本场景序列(场景头+动作+对白)。",
    ("beats", "campaign"): "把这些事件 beats 整理成跑团战役日志:时间线、关键判定、角色行动与后果。",
    ("novel", "comic"): "把这章小说拆成漫画分镜:每格给画面描述(可直接当出图 prompt)+ 对白气泡 + 在场角色。",
}


def _pack(source_kind: str, target_mode: str, material: str, *, genre: str = "", title: str = "") -> dict:
    to_view = (modes.get_mode(target_mode) or {}).get("view", "")
    guide = _GUIDE.get((source_kind, _short(target_mode)), f"把源材料转成「{target_mode}」模式的输出。")
    return {"from": source_kind, "to": target_mode, "title": title,
            "guide": guide, "target": modes.mode_pack(target_mode, genre=genre),
            "material": material}


def _short(mode_id: str) -> str:
    """target_mode → _GUIDE 用的短名(novel/cyoa/screenplay/comic/campaign)。"""
    return {"tabletop": "campaign", "screenplay": "screenplay", "comic": "comic",
            "cyoa": "cyoa", "novel": "novel"}.get(mode_id, mode_id)


# ---------- 各源的取料 ----------
def chat_to(world: World, entity: LocalEntity, target_mode: str = "novel", *, n: int | None = None) -> dict:
    """对话记录 → 目标模式(默认小说章节)。"""
    pl = chatmod.player()
    cname = entity.card().get("name", entity.id)
    lines = []
    for t in chatmod.history(entity, n):
        who = pl["name"] if t.get("role") == "user" else cname
        lines.append(f"{who}:{t.get('text', '')}")
    return _pack("chat", target_mode, "\n".join(lines), title=f"{cname}·对话")


def chapter_to(world: World, thread: Thread, chapter_no: int, target_mode: str = "cyoa") -> dict:
    """某章小说 → 目标模式(默认 CYOA / 也可 screenplay / comic)。"""
    genre = thread.meta().get("genre", "")
    return _pack("novel", target_mode, thread.chapter_text(chapter_no),
                 genre=genre, title=f"{thread.meta().get('title', thread.id)}·第{chapter_no}章")


def beats_to(world: World, thread: Thread, target_mode: str = "screenplay") -> dict:
    """跨透镜事件 beats → 目标模式(默认剧本 / 也可 tabletop 战役日志)。"""
    src_kind = "beats"
    material = "\n".join(f"- [{b.get('lens', '')}] {b.get('text', '')}" for b in thread.beats())
    return _pack(src_kind, target_mode, material, genre=thread.meta().get("genre", ""),
                 title=f"{thread.meta().get('title', thread.id)}·事件线")


# ---------- 可选一键生成(配 LLM)----------
def run(pack: dict, *, max_tokens: int = 2000) -> dict:
    """据转换包让 LLM 实际改写出目标模式产物(人在环,返回供审)。未配 LLM 给提示。"""
    if not llm.available():
        return {"available": False, "note": "一键转换需配 SV_PROVIDER;或用转换包交宿主模型改写。"}
    t = pack["target"]
    sys = (f"你把源材料转换成「{t['name']}」模式的产物。{pack['guide']} "
           f"输出格式:{t['output_format']}。" + "；".join(t["guide"]))
    out = llm.generate(sys, f"源材料:\n{pack['material']}", max_tokens=max_tokens).strip()
    return {"available": True, "from": pack["from"], "to": pack["to"], "output": out}


def cyoa_choices(pack_output: str) -> list[dict]:
    """从 CYOA 生成结果里抽编号选项(尽力解析;给 branch.py 建分支用)。"""
    j = jsonloose.loads(pack_output, None)
    if isinstance(j, dict) and isinstance(j.get("choices"), list):
        return j["choices"]
    # 文本兜底:抓「1. xxx / 2. xxx」行
    import re
    out = []
    for m in re.finditer(r"^\s*([1-9])[.、)]\s*(.+)$", pack_output, re.M):
        out.append({"label": m.group(2).strip()})
    return out
