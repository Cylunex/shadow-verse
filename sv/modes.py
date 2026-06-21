"""模式注册表 —— 把「体验模式」形式化成可插拔数据(模板 + 视图),新增模式不改核心引擎。

落地《参考功能.txt》的「模式层」:统一底层(codex→forge→substrate→透镜→枢纽)之上,
每个模式 = {基于哪个透镜 lens + 提示模板 guide + 输出格式 output_format + 前端视图 view}。
13 个模式作纯数据声明;`mode_pack` 据模式组装写作/扮演包(注入风格与格式)。零依赖。

—— 模式不是新引擎,是「透镜 + 题材配方 + 格式模板」的命名组合;加模式只加一条 MODES 数据。
"""
from __future__ import annotations

from . import craft, recipes

# group: core(三大核心) / pillar(并行支柱) / world(世界级)
# lens : 复用哪个透镜(narrate/play/simulate/render/chat)
# view : 前端视图提示(chat/reader/branch/gallery/text/map)
MODES: dict[str, dict] = {
    # ===== 三大核心 =====
    "tavern-rp": {"name": "酒馆角色扮演", "group": "core", "lens": "play", "view": "chat",
                  "output_format": "双段:【世界回应】(NPC言行+环境)+【你的处境】+ 状态行",
                  "guide": ["自由聊天、沉浸互动;系统控世界/NPC,玩家控自己角色(权限分离)。",
                            "氛围优先,短回合,留话头;触发成长时刻才沉淀。"]},
    "novel": {"name": "小说创作", "group": "core", "lens": "narrate", "view": "reader",
              "output_format": "章标题 + 正文 + ===沉淀=== 结构化沉淀 JSON",
              "guide": ["长篇/章节写作,α 悬念统领;每章按节奏契约推进一条钩子的下一层。",
                        "去AI味、感官轮换、声音指纹;按题材配方控爽点与疲劳词。"]},
    "companion": {"name": "虚拟陪伴/生活模拟", "group": "core", "lens": "chat", "view": "chat",
                  "output_format": "第一人称对话 + 变量结算(好感/日程/状态)",
                  "guide": ["长期关系养成、情感陪伴、日常互动;关系是不变量。",
                            "时间流逝/日程/约会等生活事件。注:陪伴有独立产品 Doll,此为模式入口。"]},
    # ===== 并行支柱(8 个)=====
    "cyoa": {"name": "互动小说/选择分支", "group": "pillar", "lens": "play", "view": "branch",
             "output_format": "场景叙述 + 编号选项(每项→advance-beat 或 change-scene)",
             "guide": ["选择驱动剧情、多重结局;一键从聊天/小说转分支树(见 branch.py)。",
                       "每个关键节点给 2-4 个有实质差异的选项,记录蝴蝶效应。"]},
    "screenplay": {"name": "剧本/影视脚本", "group": "pillar", "lens": "narrate", "view": "reader",
                   "output_format": "剧本格式:场景标题(INT./EXT.)+ 动作描述 + 角色名+对白 + (镜头指示)",
                   "guide": ["专业剧本格式:场景头、动作行、对白、括号提示;惜字如金。",
                             "可从小说片段提取为剧本场景。"]},
    "comic": {"name": "漫画/图形小说", "group": "pillar", "lens": "render", "view": "gallery",
              "output_format": "分镜列表:每格 {画面描述(出图prompt) + 对白气泡 + 角色}",
              "guide": ["分镜创作 + AIGC 出图(角色一致性用 appearance 锁脸)。",
                        "对白气泡、风格统一;可导出图像集。"]},
    "music": {"name": "音乐与歌词", "group": "pillar", "lens": "narrate", "view": "text",
              "output_format": "歌曲结构:[主歌][副歌][桥段] + 歌词 + (情绪/曲风标注)",
              "guide": ["角色主题曲、故事 BGM、情感歌词;完整歌曲结构。",
                        "歌词贴角色与剧情,可让角色『演唱』回应。"]},
    "tabletop": {"name": "桌游/跑团模拟", "group": "pillar", "lens": "play", "view": "chat",
                 "output_format": "DM 叙述 + 骰子判定({{roll::NdM}}) + 属性/状态结算 + 战役日志",
                 "guide": ["属性、骰子判定、规则系统;DM/玩家视角切换(用内联宏 roll)。",
                           "战役可一键转小说。判定结果驱动剧情。"]},
    "educational": {"name": "教育/知识探索", "group": "pillar", "lens": "play", "view": "chat",
                    "output_format": "沉浸故事 + 导师引导 + 互动问答 + 知识点标注",
                    "guide": ["沉浸式学习故事,导师角色,历史/科学/语言/职业模拟。",
                              "把知识点织进剧情,互动问答检验。"]},
    "dream": {"name": "梦境/超现实探索", "group": "pillar", "lens": "play", "view": "chat",
              "output_format": "象征性叙事 + 随机奇幻元素 + sanity/潜意识追踪(变量)",
              "guide": ["抽象梦境互动、象征叙事、随机奇幻;可从其他模式进入梦境分支。",
                        "追踪 sanity/潜意识变量;逻辑可跳跃、意象优先。"]},
    # ===== 世界级 =====
    "world-explore": {"name": "世界探索", "group": "world", "lens": "simulate", "view": "map",
                      "output_format": "地图导航 + 随机/触发事件 + 实时互动 beat",
                      "guide": ["持久演化地图、时间线、动态事件(腐化/变化追踪,跨模式生效)。",
                                "世界你不在时自己长(simulate 透镜,默认关)。"]},
}

# lens → 该透镜的 prep 函数名(供调用方按模式取对应取料器)
LENS_PREP = {"narrate": "narrate_prep", "play": "play_prep", "simulate": "simulate_prep",
             "render": "render_prep", "chat": "_chat(对话页直接 turn)"}


def list_modes(group: str = "") -> list[dict]:
    out = []
    for mid, m in MODES.items():
        if group and m.get("group") != group:
            continue
        out.append({"id": mid, "name": m["name"], "group": m["group"],
                    "lens": m["lens"], "view": m["view"]})
    return out


def get_mode(mode_id: str) -> dict | None:
    m = MODES.get(mode_id)
    return {"id": mode_id, **m} if m else None


def mode_pack(mode_id: str, *, genre: str = "") -> dict:
    """据模式组装「提示模板包」:模式 guide + 输出格式 + 题材配方 + 工艺核心。

    这是《参考功能》「提示模板引擎:按当前模式自动切换风格与格式」的落地。
    调用方把它和对应透镜的 prep(见 m['lens'])合并,喂宿主模型。
    """
    m = MODES.get(mode_id)
    if not m:
        raise ValueError(f"未知模式:{mode_id}(见 list_modes)")
    return {
        "mode": mode_id, "name": m["name"], "group": m["group"],
        "lens": m["lens"], "view": m["view"],
        "output_format": m["output_format"], "guide": m["guide"],
        "recipe": recipes.get(genre) if genre else None,
        "craft": craft.WRITER_CHECKLIST if m["lens"] == "narrate" else craft.PLAY_PROTOCOL,
        "prep_hint": LENS_PREP.get(m["lens"], ""),
    }
