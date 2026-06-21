"""立绘表情切换 —— 同角色锁脸预生成一组情绪立绘 + 模型情绪分类。

借鉴 SillyTavern expressions 模块(GoEmotions 标签集 + classify):
  ① 用同一 appearance + 同一 seed 锁脸,只换情绪子句,预生成 portraits/<emotion>.png;
  ② 模型回复后做一次轻量情绪分类(只在已生成的 label 里选);③ 前端按 label 换图。
引擎只管确定性那半(标签集/prompt 拼装/分类解析),出图智力走 render 后端,分类走宿主/可插拔 LLM。
"""
from __future__ import annotations

from . import jsonloose, llm

# 核心 8 情绪(RP 高频,预生成必出)+ 扩展(按需补)
EMOTIONS_CORE = ["neutral", "joy", "anger", "sadness", "surprise", "fear", "embarrassment", "love"]
EMOTIONS_EXTRA = ["disgust", "curiosity", "pride", "grief", "desire", "amusement", "confusion", "determination"]
EMOTIONS_FULL = EMOTIONS_CORE + EMOTIONS_EXTRA

# 情绪 → 英文出图子句(贴 GoEmotions;appearance 不变,只追加这句锁脸换表情)
EMOTION_PROMPT = {
    "neutral": "neutral calm expression",
    "joy": "bright smile, happy, cheerful",
    "anger": "angry, furrowed brows, glaring",
    "sadness": "sad, teary eyes, downcast",
    "surprise": "surprised, wide eyes, slightly open mouth",
    "fear": "fearful, tense, worried",
    "embarrassment": "blushing, shy, averted gaze",
    "love": "loving gaze, soft smile, slight blush",
    "disgust": "disgusted, wrinkled nose, frown",
    "curiosity": "curious, tilted head, raised eyebrow",
    "pride": "proud, confident smirk, chin up",
    "grief": "grieving, tears, anguished",
    "desire": "yearning gaze, parted lips",
    "amusement": "amused, playful grin",
    "confusion": "confused, puzzled, slight frown",
    "determination": "determined, focused, firm jaw",
}

# 中文展示名(给前端/CLI)
EMOTION_ZH = {
    "neutral": "平静", "joy": "喜悦", "anger": "愤怒", "sadness": "悲伤", "surprise": "惊讶",
    "fear": "恐惧", "embarrassment": "害羞", "love": "爱意", "disgust": "厌恶", "curiosity": "好奇",
    "pride": "得意", "grief": "悲恸", "desire": "渴望", "amusement": "玩味", "confusion": "困惑",
    "determination": "坚定",
}


def emotion_clause(emotion: str) -> str:
    return EMOTION_PROMPT.get(emotion, EMOTION_PROMPT["neutral"])


_CLASSIFY_SYS = "你给一段角色台词/旁白分类情绪,只输出一个 JSON,不要解释。"


def classify_emotion(text: str, labels: list[str]) -> str:
    """从 labels 里选最贴合文本(尾部)的情绪。未配 LLM 或解析失败 → neutral/labels[0]。"""
    fallback = "neutral" if "neutral" in labels else (labels[0] if labels else "neutral")
    if not llm.available() or not labels:
        return fallback
    sample = (text or "")[-500:]   # 只取尾部样本(省 token,同 ST sampleClassifyText)
    user = (f"从这些情绪标签里选最贴合最后一句的一个:{('、'.join(labels))}。\n"
            f"文本:\n{sample}\n"
            '只输出 JSON:{"emotion":"标签"}')
    try:
        raw = llm.generate(_CLASSIFY_SYS, user, max_tokens=20, temperature=0)
    except Exception:
        return fallback
    return _parse_emotion(raw, labels, fallback)


def _parse_emotion(raw: str, labels: list[str], fallback: str) -> str:
    j = jsonloose.loads(raw, {})
    emo = (j.get("emotion") if isinstance(j, dict) else "") or ""
    emo = str(emo).strip().lower()
    if emo in labels:
        return emo
    low = (raw or "").lower()
    for lb in labels:   # 三级回退:JSON→子串包含→fallback
        if lb in low:
            return lb
    return fallback
