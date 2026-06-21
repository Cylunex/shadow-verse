"""Skills 知识包 —— Anthropic 兼容 SKILL.md(frontmatter + 正文),三 scope later-wins。

借鉴 Luker:把「两千行不敢碰的 system prompt」拆成可按需拉取的 skill 包(反套话/角色嗓音/情节模板…),
写手按需 read,不必每次全量注入。与 Claude Code 的 skill 格式互通(SKILL.md + name/description frontmatter)。
scope 优先级 global < preset < character(同名后者覆盖);引用只按 name。存 `universe/skills/<name>/SKILL.md`。零依赖。
"""
from __future__ import annotations

import re

from . import util
from .config import UNIVERSE

SCOPES = ("global", "preset", "character")
_SCOPE_RANK = {s: i for i, s in enumerate(SCOPES)}
_NAME = re.compile(r"[a-z0-9][a-z0-9_-]{0,127}$")
_FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.S)


def _dir():
    return UNIVERSE / "skills"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """解析 `--- ... ---` 之间的扁平 frontmatter(key: value;零依赖,不引 YAML)+ 正文。"""
    m = _FM.match(text or "")
    if not m:
        return {}, (text or "").strip()
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip("'\"")
    return meta, m.group(2).strip()


def _skill_path(name: str):
    return _dir() / name / "SKILL.md"


def add_skill(name: str, description: str, body: str, *, scope: str = "global") -> dict:
    """写一个 skill 包。name 须 [a-z0-9_-]≤128;scope∈global/preset/character。"""
    name = name.strip().lower()
    if not _NAME.match(name):
        raise ValueError(f"skill name 须 [a-z0-9_-] 且 ≤128:{name!r}")
    if scope not in SCOPES:
        raise ValueError(f"scope 须 ∈ {SCOPES}")
    fm = f"---\nname: {name}\ndescription: {description}\nscope: {scope}\n---\n\n{body.strip()}\n"
    util.write_md(_skill_path(name), fm)
    return {"name": name, "scope": scope, "description": description}


def list_skills() -> list[dict]:
    d = _dir()
    out = []
    for p in sorted(d.glob("*/SKILL.md")) if d.exists() else []:
        meta, _ = parse_frontmatter(util.read_md(p))
        out.append({"name": meta.get("name", p.parent.name), "scope": meta.get("scope", "global"),
                    "description": meta.get("description", "")})
    return out


def get_skill(name: str) -> dict | None:
    p = _skill_path(name)
    if not p.exists():
        return None
    meta, body = parse_frontmatter(util.read_md(p))
    return {"name": meta.get("name", name), "scope": meta.get("scope", "global"),
            "description": meta.get("description", ""), "body": body}


def read_skill(name: str) -> str:
    """取一个 skill 的正文(写手 skill_read 时用)。"""
    s = get_skill(name)
    return s["body"] if s else ""


def visible(scope: str = "character") -> list[dict]:
    """当前可见 skill 集:≤ 指定 scope 的全收;同名按 scope later-wins(高 scope 覆盖低)。"""
    cap = _SCOPE_RANK.get(scope, 2)
    by_name: dict[str, dict] = {}
    for s in list_skills():
        if _SCOPE_RANK.get(s["scope"], 0) > cap:
            continue
        cur = by_name.get(s["name"])
        if cur is None or _SCOPE_RANK[s["scope"]] >= _SCOPE_RANK[cur["scope"]]:
            by_name[s["name"]] = s
    return sorted(by_name.values(), key=lambda x: x["name"])


def available_menu(scope: str = "character") -> str:
    """注入写手 system 的短目录(省 token,正文按需 read)。"""
    vis = visible(scope)
    if not vis:
        return ""
    lines = "\n".join(f"- {s['name']}: {s['description']}" for s in vis)
    return f"<available_skills>(需要时按 name 取正文)\n{lines}\n</available_skills>"


# ---------- 起始 skill 种子(从 craft 工艺提炼,演示格式 + 立即可用)----------
def seed() -> int:
    """幂等灌入几个起始写作 skill(反套话/角色嗓音/事件摘要)。返回新建数。"""
    seeds = [
        ("anti-cliche-zh", "反套话:绞杀 data-person 腔与升华套话,换具体动作/感官",
         "# 反套话\n\n## data-person 腔(最常见失败模式)\n别把人写成数据:绞杀『嘴角勾起一抹弧度』『眸光深邃』『空气仿佛凝固』。\n\n## 黑名单词族\n- 冷观察动词:扫视/打量/审视(堆砌即 AI 味)\n- 升华套话:那一刻他明白了/某种情绪在心底蔓延\n- 契约词:仿佛/像是/似乎(泛化比喻)\n\n## 替代\n用具体动作+感官+后果代替心理直陈;签名句用变体防复读。"),
        ("character-voice-zh", "角色嗓音:用 profile 签名句型/口头禅,守 Identity Core",
         "# 角色嗓音\n\n每个角色一套可辨识的说话方式:句长、口头禅、回避什么、攻击什么。\n- 从 profile 的对话样本提取语气,别让所有角色一个腔。\n- 潜台词:说 A 意在 B;沉默比台词更有力。\n- 守 Identity Core 底线,越界=OOC。"),
        ("event-summary-zh", "事件摘要:把一章压成可检索的『谁对谁做了什么+后果』",
         "# 事件摘要规则\n\n压缩一章/一段为高召回卡片,非好看概括:\n- 保原词(昵称/道具/暗号/关键动作),不抽象同义改写。\n- 结构:[谁] 对 [谁] 做了 [什么动作] → [后果/状态变化]。\n- 禁空泛:别写『关系升温』『气氛微妙』,写具体行为。"),
    ]
    added = 0
    for name, desc, body in seeds:
        if not _skill_path(name).exists():
            add_skill(name, desc, body, scope="global")
            added += 1
    return added
