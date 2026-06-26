"""题材配方 —— 按题材的 pacing / 爽点形态 / 疲劳词 / 有效套路 / 设定侧重。

旧 NovelKB「配方填空即出」的产出强项,落成引擎数据:锻造世界/线时注入"这个题材该怎么写",
写章时注入节奏纪律与该题材的去AI味疲劳词。不是模板,是给宿主模型的题材食材。
"""
from __future__ import annotations

# 每个配方:pacing(每章必推进)/ climax(爽点形态)/ tropes(有效套路)/
#           forbidden(本题材高频疲劳词,叠加进质检)/ emphasis(12模块侧重)
RECIPES: dict[str, dict] = {
    "无限流": {
        "pacing": "每个副本/层推进一条规则 + 至少一次队伍关系变化;通关靠破解而非蛮力",
        "climax": "破局爽(看穿规则缝隙)、反杀爽(被逼到绝境翻盘)",
        "tropes": ["规则自相矛盾处即生路", "队伍内鬼悬念", "代价守恒(用力要还)", "新副本=新规则压力"],
        "forbidden": ["突然", "莫名", "一股强大的", "瞬间秒杀"],
        "emphasis": ["规则体系", "副本/层设计", "队伍关系", "通关条件与缝隙"],
    },
    "玄幻": {
        "pacing": "每章一个小目标达成或受挫 + 实力/资源/敌友格局推进一步",
        "climax": "扮猪吃虎、越阶战、打脸、奇遇得宝",
        "tropes": ["境界压制与破格", "宗门/家族势力网", "金手指守恒", "宿敌养成"],
        "forbidden": ["强大的气息", "恐怖的威压", "不可思议", "整个人都"],
        "emphasis": ["修炼/力量体系", "境界与寿元", "势力地理", "天材地宝经济"],
    },
    "仙侠": {
        "pacing": "每章推进道心/情劫/机缘之一;长线靠境界与因果",
        "climax": "斩业证道、情之取舍、逆天改命",
        "tropes": ["大道五十天衍四九(留一线)", "情劫与道心冲突", "因果债"],
        "forbidden": ["仙气飘飘", "缥缈", "亘古", "诸天万界"],
        "emphasis": ["修炼体系", "天道规则", "情与道", "历史纪元"],
    },
    "都市": {
        "pacing": "每章一次人物关系或处境的实质变化;别停在日常水文",
        "climax": "扮猪吃虎、打脸装逼、危机化解、感情升温",
        "tropes": ["身份反差", "旧债与人情账", "规矩大于法的小江湖"],
        "forbidden": ["嘴角勾起一抹", "深邃的眼眸", "霸道", "冷冽"],
        "emphasis": ["社会规则", "人物关系网", "势力与金钱", "城市质感"],
    },
    "科幻": {
        "pacing": "每章揭示一条设定后果或推进一个谜题;设定要落到人能感受的代价",
        "climax": "认知颠覆、技术反转、文明尺度的抉择",
        "tropes": ["一个硬设定贯穿到底", "技术的伦理代价", "尺度落差带来的压迫"],
        "forbidden": ["先进的科技", "未知的能量", "无法理解的", "高维"],
        "emphasis": ["科学设定与常数", "技术社会后果", "文明格局", "时间尺度"],
    },
    "悬疑": {
        "pacing": "每章推进 α 谜题一层 + 抛一个新疑点;信息克制给",
        "climax": "真相反转、伏笔回收、身份揭穿",
        "tropes": ["不可靠叙述", "线索公平埋设", "红鲱鱼误导"],
        "forbidden": ["毛骨悚然", "不寒而栗", "诡异", "细思极恐"],
        "emphasis": ["谜题结构", "线索台账", "人物动机", "时间线"],
    },
    "言情": {
        "pacing": "每章推进关系温度或制造一次有效拉扯;别单调上扬",
        "climax": "心动、误会与澄清、双向奔赴、不可逆告白",
        "tropes": ["错位与误会", "关系不可逆节点", "细节见情"],
        "forbidden": ["脸红心跳", "小鹿乱撞", "宠溺", "霸道总裁"],
        "emphasis": ["人物关系", "情感节奏", "性格反差", "日常质感"],
    },
}

DEFAULT = {
    "pacing": "每章至少推进一条主线钩子的下一层",
    "climax": "目标达成 / 危机化解 / 关系变化",
    "tropes": ["α 悬念统领", "一章主推一条钩子", "行动后果闭环"],
    "forbidden": [],
    "emphasis": ["核心冲突", "人物弧", "世界规则"],
}


# 题材专属审校维度(喂审校子代理,在通用 rubric 之外按题材多查这些)
AUDIT_DIMS: dict[str, list[str]] = {
    "无限流": ["每副本/层是否给出通关条件与已用缝隙", "队伍信任/内鬼线是否推进", "代价是否守恒(借力有还)"],
    "玄幻": ["战力/资源进展本章是否可见", "金手指是否守恒(不凭空)", "境界压制逻辑是否自洽"],
    "仙侠": ["道心/情劫/机缘是否至少推进一条", "境界与因果是否自洽", "情与道的张力是否在场"],
    "都市": ["人物关系或处境是否实质变化(非水文)", "规矩/人情账是否记得住", "身份反差是否用上"],
    "科幻": ["设定后果是否落到人能感受的代价", "硬设定/常数是否前后自洽", "尺度落差的压迫是否到位"],
    "悬疑": ["α谜题是否推进一层并抛新疑点", "线索是否公平埋设(非作弊)", "人物动机是否站得住"],
    "言情": ["关系温度本章是否有变(非单调上扬)", "误会/拉扯是否有效", "细节是否见情"],
    "_default": ["α悬念是否推进一层", "本章是否兑现节奏契约", "行动是否有后果闭环"],
}


def _match_key(genre: str, keys=None) -> str:
    if keys is None:
        keys = [k for k in _genres() if k != "_default"]
    if not genre:
        return "_default"
    if genre in keys:
        return genre
    for g in keys:
        if g in genre or genre in g:
            return g
    return "_default"


def get(genre: str) -> dict:
    """按题材取配方(子串匹配,如'都市黑道'→都市;未知→DEFAULT)+ 附题材审校维度。
    走组件数据(缺则原样回退内置种子=字节等价);配方与审校维度合一存于 recipes/genres。"""
    g = _genres()
    k = _match_key(genre, [x for x in g if x != "_default"])
    return dict(g.get(k) or g.get("_default") or _GENRES_SEED["_default"])   # 末位兜底:即便有人删了数据里的 _default 也不崩


def forbidden_words(genre: str) -> list[str]:
    return get(genre).get("forbidden", [])


def genres() -> list[str]:
    return [k for k in _genres() if k != "_default"]


# ========== 题材配方字段化(吸收 webnovel-writer genre-profiles)==========
# 把「pacing/爽点」从文字升级成可被 checker/reflect 读的量化参数:节奏红线 + 钩子/爽点基线。
# 字段:hook_strength(钩子强度基线)/coolpoint_per_chapter(每章爽点密度下限)/
#       stall_max(主线最大连续停滞章)/romance_gap_max(感情线最大断档章)/transition_max(过渡章最大连续)。
PROFILES: dict[str, dict] = {
    "无限流": {"hook_strength": "高", "coolpoint_per_chapter": 1, "stall_max": 1, "romance_gap_max": 8, "transition_max": 1},
    "玄幻": {"hook_strength": "高", "coolpoint_per_chapter": 1, "stall_max": 2, "romance_gap_max": 10, "transition_max": 2},
    "仙侠": {"hook_strength": "中", "coolpoint_per_chapter": 1, "stall_max": 2, "romance_gap_max": 8, "transition_max": 2},
    "都市": {"hook_strength": "中", "coolpoint_per_chapter": 1, "stall_max": 2, "romance_gap_max": 5, "transition_max": 2},
    "科幻": {"hook_strength": "中", "coolpoint_per_chapter": 0, "stall_max": 3, "romance_gap_max": 12, "transition_max": 3},
    "悬疑": {"hook_strength": "高", "coolpoint_per_chapter": 0, "stall_max": 1, "romance_gap_max": 12, "transition_max": 2},
    "言情": {"hook_strength": "中", "coolpoint_per_chapter": 1, "stall_max": 2, "romance_gap_max": 2, "transition_max": 2},
}
PROFILE_DEFAULT = {"hook_strength": "中", "coolpoint_per_chapter": 0, "stall_max": 2, "romance_gap_max": 8, "transition_max": 2}

# 追读力钩型分类(每型:触发场景 + 题材适配 + 常见误用)
HOOK_TAXONOMY: dict[str, dict] = {
    "危机钩": {"when": "角色陷入立刻行动否则崩盘的处境", "fit": "无限流/玄幻/悬疑", "misuse": "低风险假危机(读者知道死不了)"},
    "悬念钩": {"when": "抛一个未解之谜/真相缺口", "fit": "悬疑/科幻/仙侠", "misuse": "故弄玄虚却永不兑现"},
    "渴望钩": {"when": "角色立下目标/承诺,兑现遥远", "fit": "玄幻/言情/都市", "misuse": "目标空泛,读者不在乎"},
    "情绪钩": {"when": "强烈情感时刻(心动/愤怒/不舍)未落定", "fit": "言情/都市", "misuse": "强行煽情、情绪与情节脱节"},
    "选择钩": {"when": "两难抉择定格在选择前", "fit": "全题材", "misuse": "选项无实质差异/有明显正解"},
}


def get_profile(genre: str) -> dict:
    """题材量化配方(节奏红线 + 钩子/爽点基线)。子串匹配,未知→默认。走组件数据,缺则回退种子。"""
    p = _profiles()
    k = _match_key(genre, [x for x in _genres() if x != "_default"])
    return dict(p.get(k) or p.get("_default") or _PROFILES_SEED["_default"])


# ===== 组件化外化(C1):配方/量化档/钩型登记为可编辑组件,缺数据回退内置种子(字节等价)=====
# 上面 RECIPES/AUDIT_DIMS/DEFAULT/PROFILES/PROFILE_DEFAULT/HOOK_TAXONOMY 保留为种子(也供旧测试直接引用)。
# genres 把「配方 + 审校维度」合一(含 _default 兜底条);profiles 含 _default。
_GENRES_SEED = {k: {**v, "audit_dimensions": AUDIT_DIMS.get(k, AUDIT_DIMS["_default"])}
                for k, v in RECIPES.items()}
_GENRES_SEED["_default"] = {**DEFAULT, "audit_dimensions": AUDIT_DIMS["_default"]}
_PROFILES_SEED = {**PROFILES, "_default": PROFILE_DEFAULT}
_HOOK_TAXONOMY_SEED = HOOK_TAXONOMY                  # 捕获种子后下面 del,让 recipes.HOOK_TAXONOMY 透明走数据层
_GROUP_DEFS = [
    ("genres", "record", "题材配方(pacing/爽点/疲劳词/套路/侧重/审校维度)", _GENRES_SEED),
    ("profiles", "record", "题材量化档(钩子/爽点/停滞红线)", _PROFILES_SEED),
    ("hook_taxonomy", "record", "追读力钩型", _HOOK_TAXONOMY_SEED),
]


def _genres() -> dict:
    from . import components
    return components.load_group("recipes", "genres", "record", _GENRES_SEED)


def _profiles() -> dict:
    from . import components
    return components.load_group("recipes", "profiles", "record", _PROFILES_SEED)


def _hook_taxonomy() -> dict:
    from . import components
    return components.load_group("recipes", "hook_taxonomy", "record", _HOOK_TAXONOMY_SEED)


del HOOK_TAXONOMY   # 改走 __getattr__:recipes.HOOK_TAXONOMY 反映组件编辑(缺数据=种子,字节等价)


def __getattr__(name):   # PEP 562:仅 HOOK_TAXONOMY 走数据层(RECIPES/AUDIT_DIMS/... 仍是常量,旧测试照读)
    if name == "HOOK_TAXONOMY":
        return _hook_taxonomy()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
