"""可插拔 LLM provider —— 闭合 AIGC 生成回路(零依赖 urllib)。

默认 stub(关,返回占位 markdown,供测试/未配 key 时跑通流程)。配 SV_PROVIDER 后真实生成。
**定位**:作为宿主 skill 时不用它(生成走宿主 Agent 的模型,Model A);单机网页/CLI 想"一键锻造/写章"才用。
引擎仍不绑定模型——provider 是用户自配的可选件(同 render/embed)。后端中立、不限尺度。
"""
from __future__ import annotations

import json
import urllib.request

from . import config


def available() -> bool:
    return config.PROVIDER != "stub"


def generate(system: str, user: str, *, max_tokens: int | None = None, temperature: float | None = None) -> str:
    """单轮生成:system 设定 + user 请求 → 文本。失败抛异常(由调用方/CLI 处理)。"""
    mt = max_tokens or config.LLM_MAX_TOKENS
    temp = config.LLM_TEMPERATURE if temperature is None else temperature
    p = config.PROVIDER
    if p == "stub":
        return _stub(system, user)
    if p == "openai":
        return _openai(system, user, mt, temp)
    if p == "anthropic":
        return _anthropic(system, user, mt, temp)
    if p == "ollama":
        return _ollama(system, user, temp)
    raise ValueError(f"未知 provider:{p}(stub|openai|anthropic|ollama)")


def _post(url: str, body: dict, headers: dict, timeout: int = 180) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _openai(system: str, user: str, mt: int, temp: float) -> str:
    if not config.OPENAI_API_KEY:
        raise ValueError("缺 OPENAI_API_KEY")
    model = config.MODEL or "gpt-4o-mini"
    d = _post(f"{config.OPENAI_BASE_URL}/chat/completions",
              {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "max_tokens": mt, "temperature": temp},
              {"Authorization": f"Bearer {config.OPENAI_API_KEY}"})
    return d["choices"][0]["message"]["content"].strip()


def _anthropic(system: str, user: str, mt: int, temp: float) -> str:
    if not config.ANTHROPIC_API_KEY:
        raise ValueError("缺 ANTHROPIC_API_KEY")
    model = config.MODEL or "claude-sonnet-4-6"
    d = _post("https://api.anthropic.com/v1/messages",
              {"model": model, "max_tokens": mt, "temperature": temp, "system": system,
               "messages": [{"role": "user", "content": user}]},
              {"x-api-key": config.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"})
    return "".join(b.get("text", "") for b in d.get("content", [])).strip()


def _ollama(system: str, user: str, temp: float) -> str:
    model = config.MODEL or "qwen2.5"
    d = _post(f"{config.OLLAMA_BASE_URL}/api/chat",
              {"model": model, "stream": False, "options": {"temperature": temp},
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
              {})
    return d["message"]["content"].strip()


def _stub(system: str, user: str) -> str:
    """占位生成:返回可用的 markdown 骨架,标明是 stub —— 让未配 key 时流程仍能跑通/测试。"""
    head = user.strip().splitlines()[0][:40] if user.strip() else "未命名"
    return (f"# {head}（stub 占位）\n\n"
            f"> ⚠ 当前 SV_PROVIDER=stub,这是占位文本。配置真实 provider(openai/anthropic/ollama)后由模型生成。\n\n"
            f"## 生成请求摘要\n{user.strip()[:400]}\n")
