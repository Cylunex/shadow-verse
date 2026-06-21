"""配置与路径。所有路径相对项目根,方便迁移(沿用 Doll 成功范式)。"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

# 项目根 = 本文件的上上级(sv/ 的父目录)
ROOT = Path(__file__).resolve().parent.parent


# sv.conf = 模板/默认(入库,无密钥);sv.local.conf = 本机/UI 写入(密钥,gitignore)。local 覆盖 base。
CONF_FILE = ROOT / "sv.conf"
LOCAL_CONF_FILE = Path(os.environ.get("SV_LOCAL_CONF", str(ROOT / "sv.local.conf")))


def _parse_conf(p: Path) -> dict[str, str]:
    conf: dict[str, str] = {}
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


def _load_conf() -> dict[str, str]:
    """sv.conf 打底 + sv.local.conf 覆盖(本机密钥/UI 设置)。"""
    return {**_parse_conf(CONF_FILE), **_parse_conf(LOCAL_CONF_FILE)}


_CONF = _load_conf()


def _get(key: str, default: str = "") -> str:
    """优先级:环境变量 > sv.local.conf > sv.conf > 默认。"""
    v = os.environ.get(key)
    if v:
        return v
    return _CONF.get(key, default)


# 由 UI/CLI 管理的可热加载设置键(写进 sv.local.conf)
MANAGED_KEYS = (
    "SV_PROVIDER", "SV_MODEL", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "OPENAI_BASE_URL",
    "SV_LLM_TEMPERATURE", "SV_RENDER", "GITEE_API_KEY", "GITEE_BASE_URL", "SV_IMAGE_SIZE",
    "SV_EMBED_PROVIDER", "SV_EMBED_MODEL", "OLLAMA_BASE_URL", "SV_SIMULATE",
)
SECRET_KEYS = {"ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GITEE_API_KEY"}


# ---- 数据真相目录(L2 基质)。可用 SV_UNIVERSE_DIR 覆盖,便于代码/数据分离 ----
UNIVERSE = Path(_get("SV_UNIVERSE_DIR", str(ROOT / "universe")))
CODEX_DIR = UNIVERSE / "codex"        # L0 元件库
WORLDS_DIR = UNIVERSE / "worlds"      # L2 世界
NEXUS_DIR = UNIVERSE / "nexus"        # L4 枢纽(跨世界实体 + 世界互联)
GROUPS_DIR = UNIVERSE / "groups"      # 群聊(多角色同场)

# ---- 纯常量(不随配置变)----
RECENT_EXP_REBUILD = 5     # 状态重建读取的近期经历条数(确定性、范围小)
RETRIEVE_TOP_K = 6         # 记忆检索注入条数(加权、全历史)
RECENCY_TAU_DAYS = 30.0
W_RELEVANCE = 0.70
W_RECENCY = 0.18
W_IMPORTANCE = 0.12
LEVEL_IMPORTANCE = {"瞬时": 0.2, "持久": 0.6, "身份": 1.0}
DEFAULT_CONTRACT = {"entry": ["本体进"], "exit": ["带走所得"], "carry": "保留随身物"}
DEFAULT_SCALE = "max"   # 内容尺度默认最大(后端中立)


def _compute() -> None:
    """据当前 _CONF/env 计算可热加载的设置(UI/CLI 改完调 reload() 即生效,不必重启)。"""
    g = globals()
    # 体验透镜开关
    g["SIMULATE_ENABLED"] = _get("SV_SIMULATE", "off").lower() in ("on", "1", "true")
    g["RENDER"] = _get("SV_RENDER", "none")          # none | gitee
    g["GITEE_API_KEY"] = _get("GITEE_API_KEY", "")
    g["GITEE_BASE_URL"] = _get("GITEE_BASE_URL", "https://ai.gitee.com/v1")
    g["IMAGE_MODEL"] = _get("SV_IMAGE_MODEL", "z-image-turbo")
    g["IMAGE_SIZE"] = _get("SV_IMAGE_SIZE", "1152x2048")
    g["IMAGE_STEPS"] = int(_get("SV_IMAGE_STEPS", "9"))
    # 叙事产线参数
    g["HANZI_TARGET"] = int(_get("SV_HANZI_TARGET", "2500"))
    g["SUMMARY_EVERY"] = int(_get("SV_SUMMARY_EVERY", "5"))
    # 可插拔 LLM(默认 stub;作为 skill 时不用,单机想一键生成才配)
    g["PROVIDER"] = _get("SV_PROVIDER", "stub")      # stub | openai | anthropic | ollama
    g["MODEL"] = _get("SV_MODEL", "")
    g["ANTHROPIC_API_KEY"] = _get("ANTHROPIC_API_KEY", "")
    g["OPENAI_API_KEY"] = _get("OPENAI_API_KEY", "")
    g["OPENAI_BASE_URL"] = _get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    g["LLM_MAX_TOKENS"] = int(_get("SV_LLM_MAX_TOKENS", "4096"))
    g["LLM_TEMPERATURE"] = float(_get("SV_LLM_TEMPERATURE", "0.9"))
    # 向量(休眠,规模驱动才上)
    g["EMBED_PROVIDER"] = _get("SV_EMBED_PROVIDER", "none")
    g["EMBED_MODEL"] = _get("SV_EMBED_MODEL", "")
    g["OLLAMA_BASE_URL"] = _get("OLLAMA_BASE_URL", "http://localhost:11434")


_compute()


def reload() -> None:
    """重读配置文件并重算设置(UI 保存后调用,免重启)。"""
    global _CONF
    _CONF = _load_conf()
    _compute()


def save_setting(updates: dict) -> None:
    """把设置写进 sv.local.conf(合并已有键)并热加载。只接受 MANAGED_KEYS。"""
    existing = _parse_conf(LOCAL_CONF_FILE)
    for k, v in (updates or {}).items():
        if k not in MANAGED_KEYS:
            continue
        v = ("" if v is None else str(v)).strip()
        if v == "":
            existing.pop(k, None)
        else:
            existing[k] = v
    lines = ["# 本机设置(含密钥)——由网页设置面板/CLI 写入,勿入库。", ""]
    lines += [f"{k}={existing[k]}" for k in sorted(existing)]
    LOCAL_CONF_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    reload()


def settings_snapshot() -> dict:
    """给 UI 的当前设置(密钥脱敏:只报是否已设)。"""
    def mask(key):
        val = _get(key, "")
        return {"set": bool(val), "preview": (val[:4] + "…" + val[-2:]) if len(val) > 8 else ("已设" if val else "")}
    return {
        "provider": PROVIDER, "model": MODEL, "openai_base_url": OPENAI_BASE_URL,
        "temperature": LLM_TEMPERATURE, "llm_available": PROVIDER != "stub",
        "render": RENDER, "gitee_base_url": GITEE_BASE_URL, "image_size": IMAGE_SIZE,
        "embed_provider": EMBED_PROVIDER, "embed_model": EMBED_MODEL, "ollama_base_url": OLLAMA_BASE_URL,
        "simulate": SIMULATE_ENABLED,
        "secrets": {k: mask(k) for k in SECRET_KEYS},
        "env_overrides": [k for k in MANAGED_KEYS if os.environ.get(k)],
    }


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
