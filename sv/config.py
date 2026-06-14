"""配置与路径。所有路径相对项目根,方便迁移(沿用 Doll 成功范式)。"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

# 项目根 = 本文件的上上级(sv/ 的父目录)
ROOT = Path(__file__).resolve().parent.parent


def _load_conf() -> dict[str, str]:
    """读项目根 sv.conf(KEY=VALUE,# 注释)——免环境变量,docker 改配置只改这文件。"""
    conf: dict[str, str] = {}
    p = ROOT / "sv.conf"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                v = v.strip()
                if " #" in v:          # 去掉行内注释(空格+#;不误伤含 # 的 URL/值)
                    v = v.split(" #", 1)[0].strip()
                conf[k.strip()] = v
    return conf


_CONF = _load_conf()


def _get(key: str, default: str = "") -> str:
    """优先级:环境变量 > sv.conf 文件 > 默认。"""
    v = os.environ.get(key)
    if v:
        return v
    return _CONF.get(key, default)


# ---- 数据真相目录(L2 基质)。可用 SV_UNIVERSE_DIR 覆盖,便于代码/数据分离 ----
UNIVERSE = Path(_get("SV_UNIVERSE_DIR", str(ROOT / "universe")))
CODEX_DIR = UNIVERSE / "codex"        # L0 元件库
WORLDS_DIR = UNIVERSE / "worlds"      # L2 世界
NEXUS_DIR = UNIVERSE / "nexus"        # L4 枢纽(跨世界实体 + 世界互联)

# ---- 体验透镜(L3)开关 ----
# 自演化(模拟透镜):能力已建,默认不开(用户:先具备不开)
SIMULATE_ENABLED = _get("SV_SIMULATE", "off").lower() in ("on", "1", "true")
# 多模态渲染(可视化透镜):可插拔,未配 key 则休眠(零依赖 urllib,同 Doll image.py)
RENDER = _get("SV_RENDER", "none")     # none | gitee
GITEE_API_KEY = _get("GITEE_API_KEY", "")
GITEE_BASE_URL = _get("GITEE_BASE_URL", "https://ai.gitee.com/v1")
IMAGE_MODEL = _get("SV_IMAGE_MODEL", "z-image-turbo")
IMAGE_SIZE = _get("SV_IMAGE_SIZE", "1152x2048")
IMAGE_STEPS = int(_get("SV_IMAGE_STEPS", "9"))

# ---- 写作/叙事产线参数(narrate 透镜)----
HANZI_TARGET = int(_get("SV_HANZI_TARGET", "2500"))
SUMMARY_EVERY = int(_get("SV_SUMMARY_EVERY", "5"))
RECENT_EXP_REBUILD = 5     # 状态重建读取的近期经历条数(确定性、范围小)
RETRIEVE_TOP_K = 6         # 记忆检索注入条数(加权、全历史)

# ---- 记忆检索打分(Generative-Agents 式加权和;相关度主导)----
RECENCY_TAU_DAYS = 30.0
W_RELEVANCE = 0.70
W_RECENCY = 0.18
W_IMPORTANCE = 0.12
LEVEL_IMPORTANCE = {"瞬时": 0.2, "持久": 0.6, "身份": 1.0}

# ---- 世界契约默认(实体跨世界进出规则;Phase 0 最简档)----
DEFAULT_CONTRACT = {
    "entry": ["本体进"],          # 本体进 / 带记忆进 / 换皮进(化身)
    "exit": ["带走所得"],         # 带走所得 / 封存
    "carry": "保留随身物",        # 保留随身物 / 清空
}
DEFAULT_SCALE = "max"   # 内容尺度默认最大;世界/线可声明更克制(后端中立)

# ---- 可插拔 LLM provider(闭合 AIGC 生成回路)----
# 默认 stub(关,返回占位)。作为宿主 skill 时不用它(走宿主模型);单机网页/CLI 想一键生成才配。
# 引擎仍"不绑定模型"——provider 是用户自配的可选件,同 render/embed。后端中立、不限尺度。
PROVIDER = _get("SV_PROVIDER", "stub")              # stub | openai | anthropic | ollama
MODEL = _get("SV_MODEL", "")                        # 留空各 provider 用各自默认
ANTHROPIC_API_KEY = _get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = _get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = _get("OPENAI_BASE_URL", "https://api.openai.com/v1")  # 可指 deepseek/本地兼容端
LLM_MAX_TOKENS = int(_get("SV_LLM_MAX_TOKENS", "4096"))
LLM_TEMPERATURE = float(_get("SV_LLM_TEMPERATURE", "0.9"))

# ---- 远期接口(休眠,规模驱动才上)----
EMBED_PROVIDER = _get("SV_EMBED_PROVIDER", "none")  # none | ollama | openai
EMBED_MODEL = _get("SV_EMBED_MODEL", "")
OLLAMA_BASE_URL = _get("OLLAMA_BASE_URL", "http://localhost:11434")


# ---- 文件原语 ----
def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
