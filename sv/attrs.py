"""数值面板模板 —— 轮回者(被提取 / 被创造的魂)初期的多维「攻略式」状态卡。

用户(2026-06-22)定调:初期数值要**完善、维度多、像游戏攻略**,直观、参与感强;
后期定性系统成熟了再逐步精简(把 meta.vis 调成 hidden 或删维度即可,数据结构不动)。
**与「你」的关系要做厚(galgame 攻略板),在虚拟女友透镜里是 HUD 主角。**

落在化身的 vars.json(走 [[varstate]] 三段式 data/rules/meta + 护栏),随副本 / 游戏世界实时变动。
设定立足无限流(主神空间·副本)+ 头号玩家(游戏世界):评级 / 奖励点 / 理智SAN / 兑换能力 / 副本进度…

只造数据,不接逻辑——提取(ascend)/ 创造 soul-character 时用 apply_panel(e) 落库;前端按类目分组渲染。
"""
from __future__ import annotations

from . import varstate

# ---------- 与「你」的关系:galgame 式攻略板(多轴 + 阶段 + 称呼 + 里程碑 + 隐藏真心话)----------
# 关系阶段阶梯:攻略推进随好感/心动/亲密爬升(阶段跃迁逻辑后续接,先定 schema)。
REL_STAGES = ["陌生人", "点头之交", "朋友", "暧昧", "恋人", "挚爱", "唯一"]

# 每条关系轴:HUD 渲染元(label/color/icon Tabler)+ 护栏(min/max)+ 初值。心防是逆向轴(越攻略越低)。
REL_AXES = [
    {"key": "好感", "label": "好感", "color": "#ff8fb0", "icon": "heart", "min": -100, "max": 100, "start": 0},
    {"key": "心动", "label": "心动", "color": "#ff6b9c", "icon": "heartbeat", "min": 0, "max": 100, "start": 0},
    {"key": "信任", "label": "信任", "color": "#5ee0d0", "icon": "shield", "min": -100, "max": 100, "start": 0},
    {"key": "依赖", "label": "依赖", "color": "#9b82ff", "icon": "link", "min": 0, "max": 100, "start": 0},
    {"key": "亲密", "label": "亲密", "color": "#ffb3c8", "icon": "flame", "min": 0, "max": 100, "start": 0},
    {"key": "默契", "label": "默契", "color": "#8fd0ff", "icon": "users", "min": 0, "max": 100, "start": 0},
    {"key": "安全感", "label": "安全感", "color": "#7fce9f", "icon": "home", "min": 0, "max": 100, "start": 30},
    {"key": "心防", "label": "心防", "color": "#a8a6c8", "icon": "lock", "min": 0, "max": 100, "start": 70},
    {"key": "占有欲", "label": "占有欲", "color": "#ffcd6b", "icon": "diamond", "min": 0, "max": 100, "start": 0},
]
# 高亲密才解锁的隐藏内在(galgame 攻略到位才看得见的真心话/期待/雷区)——平时 ?? 锁着。
REL_HIDDEN = ["真心话", "隐藏期待", "雷区"]

# 维度类目(仅供前端分组显示;varstate 实际是扁平/深路径)
CATEGORIES = [
    ("核心属性", ["体魄", "敏捷", "感知", "心智", "魅力", "气运"]),
    ("生存状态", ["生命", "理智", "体力", "状态"]),
    ("轮回档案", ["评级", "奖励点", "轮回次数", "存活率"]),
    ("能力兑换", ["已兑换能力"]),
    ("当前副本", ["副本", "副本进度", "危险度", "主线"]),
    ("与你·关系攻略", ["关系"]),   # 陪伴透镜的 HUD 主角:展开成 REL_AXES 攻略板 + 阶段/称呼/里程碑
    ("灵魂跨界", ["身份锚点", "记忆完整度", "已解锁副本"]),
    ("内在·隐藏", ["真实想法", "执念", "底线压力"]),
]

_CORE = ["体魄", "敏捷", "感知", "心智", "魅力", "气运"]
_CORE_ICON = {"体魄": "barbell", "敏捷": "run", "感知": "eye", "心智": "brain", "魅力": "sparkles", "气运": "clover"}


def _rules() -> dict:
    r = {k: {"min": 0, "max": 100, "step": 10} for k in _CORE}
    r.update({
        "生命": {"min": 0, "max": 100}, "理智": {"min": 0, "max": 100}, "体力": {"min": 0, "max": 100},
        "存活率": {"min": 0, "max": 100}, "副本进度": {"min": 0, "max": 100},
        "身份锚点": {"min": 0, "max": 100}, "记忆完整度": {"min": 0, "max": 100}, "底线压力": {"min": 0, "max": 100},
        "奖励点": {"min": 0}, "轮回次数": {"min": 0, "ro": True},     # 轮回次数只引擎推进,模型/手动写不动
        "评级": {"enum": ["D", "C", "B", "A", "S", "SS"]},
        "危险度": {"enum": ["安全", "低", "中", "高", "致命"]},
        "关系.*.阶段": {"enum": REL_STAGES},               # 关系阶段只能取阶梯里的值
    })
    for a in REL_AXES:                                     # 关系多轴通配护栏(对任意对象生效,你的最厚)
        r[f"关系.*.{a['key']}"] = {"min": a["min"], "max": a["max"]}
    return r


def _meta() -> dict:
    m = {k: {"label": k, "vis": "bar", "color": "#9b82ff", "icon": _CORE_ICON[k]} for k in _CORE}
    m.update({
        "生命": {"label": "生命 HP", "vis": "bar", "color": "#7fce9f", "icon": "heart"},
        "理智": {"label": "理智 SAN", "vis": "bar", "color": "#c08fff", "icon": "brain"},
        "体力": {"label": "体力", "vis": "bar", "color": "#ffcd6b", "icon": "bolt"},
        "状态": {"label": "状态", "vis": "list", "icon": "alert-triangle"},
        "评级": {"label": "评级", "vis": "text", "color": "#ffcd6b", "icon": "award"},
        "奖励点": {"label": "奖励点", "vis": "num", "color": "#5ee0d0", "icon": "diamond"},
        "轮回次数": {"label": "轮回次数", "vis": "num", "icon": "versions"},
        "存活率": {"label": "存活率", "vis": "num", "icon": "heartbeat"},
        "已兑换能力": {"label": "已兑换能力", "vis": "list", "icon": "stack-2"},
        "副本": {"label": "当前副本", "vis": "text", "icon": "map-pin"},
        "副本进度": {"label": "副本进度", "vis": "bar", "color": "#5ee0d0", "icon": "flag"},
        "危险度": {"label": "危险度", "vis": "text", "icon": "skull"},
        "主线": {"label": "主线任务", "vis": "text", "icon": "target"},
        "关系": {"label": "关系 · 攻略", "vis": "rel", "icon": "heart-handshake"},   # vis=rel:前端按 REL_AXES 展开攻略板
        "身份锚点": {"label": "身份锚点", "vis": "bar", "color": "#ffcd6b", "icon": "anchor"},
        "记忆完整度": {"label": "记忆完整度", "vis": "bar", "color": "#9b82ff", "icon": "brain"},
        "已解锁副本": {"label": "已解锁副本", "vis": "list", "icon": "versions"},
        "真实想法": {"label": "真实想法", "vis": "hidden"},
        "执念": {"label": "执念", "vis": "hidden"},
        "底线压力": {"label": "底线压力", "vis": "hidden"},
    })
    return m


def relationship_with(name: str = "你") -> dict:
    """一条对某人的关系卡(galgame 攻略板):多轴 + 阶段 + 称呼 + 里程碑 + 隐藏真心话。"""
    rel = {a["key"]: a["start"] for a in REL_AXES}
    rel.update({"阶段": "陌生人", "称呼": name, "里程碑": [],
                "真心话": "", "隐藏期待": "", "雷区": []})   # 隐藏:高亲密才解锁(?? 锁着)
    return rel


def default_panel(player_name: str = "你") -> dict:
    """一个全新轮回者的多维数值卡(data/rules/meta);player_name=「你扮演谁」,先建一条对你的厚关系卡。"""
    data = {
        "体魄": 50, "敏捷": 50, "感知": 50, "心智": 50, "魅力": 50, "气运": 50,
        "生命": 100, "理智": 100, "体力": 100, "状态": [],
        "评级": "D", "奖励点": 0, "轮回次数": 0, "存活率": 100,
        "已兑换能力": [],
        "副本": "主神空间", "副本进度": 0, "危险度": "安全", "主线": "",
        "关系": {player_name: relationship_with(player_name)},
        "身份锚点": 60, "记忆完整度": 100, "已解锁副本": [],
        "真实想法": "", "执念": "", "底线压力": 0,
    }
    return {"data": data, "rules": _rules(), "meta": _meta()}


def apply_panel(e, player_name: str = "你") -> dict:
    """给实体(化身)落上数值卡:schema(rules+meta)整套写入,data 只补缺失键不覆盖既有值。幂等。"""
    st = varstate.load(e)
    panel = default_panel(player_name)
    st["rules"] = {**panel["rules"], **st.get("rules", {})}
    st["meta"] = {**panel["meta"], **st.get("meta", {})}
    data = st.get("data", {}) or {}
    for k, v in panel["data"].items():
        data.setdefault(k, v)
    st["data"] = data
    varstate.save(e, st)
    return st
