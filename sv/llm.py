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


# 各 provider 接受的采样参数(预设里带来的 sampling 据此分流;非标键丢弃,免严格端 400)
_OPENAI_SAMPLERS = {"temperature", "top_p", "frequency_penalty", "presence_penalty", "seed", "max_tokens"}
_ANTHROPIC_SAMPLERS = {"temperature", "top_p", "top_k", "max_tokens"}
_OLLAMA_SAMPLERS = {"temperature", "top_p", "top_k", "seed", "repeat_penalty"}
_OLLAMA_REMAP = {"repetition_penalty": "repeat_penalty"}


def _samplers(params: dict | None, allowed: set, remap: dict | None = None) -> dict:
    """从预设 sampling 里挑该 provider 认的键(可改名),其余丢弃。"""
    out = {}
    for k, v in (params or {}).items():
        k = (remap or {}).get(k, k)
        if k in allowed and v not in (None, ""):
            out[k] = v
    return out


def _chain() -> list[tuple[str, str]]:
    """provider 尝试链:主 provider →(配了就)备援 provider。备援同主时不重复。"""
    chain = [(config.PROVIDER, config.MODEL)]
    fb = (config.FALLBACK_PROVIDER or "").strip()
    if fb and fb != "stub" and (fb, config.FALLBACK_MODEL) != (config.PROVIDER, config.MODEL):
        chain.append((fb, config.FALLBACK_MODEL))
    return chain


def _gen_one(p: str, model: str, system: str, user: str, mt: int, temp: float, params: dict | None) -> str:
    if p == "stub":
        return _stub(system, user)
    if p == "openai":
        return _openai(system, user, mt, temp, params, model)
    if p == "anthropic":
        return _anthropic(system, user, mt, temp, params, model)
    if p == "ollama":
        return _ollama(system, user, temp, params, model)
    raise ValueError(f"未知 provider:{p}(stub|openai|anthropic|ollama)")


def generate(system: str, user: str, *, max_tokens: int | None = None,
             temperature: float | None = None, params: dict | None = None) -> str:
    """单轮生成:system 设定 + user 请求 → 文本。主 provider 失败则自动切备援(SV_FALLBACK_PROVIDER)。"""
    mt = max_tokens or config.LLM_MAX_TOKENS
    temp = config.LLM_TEMPERATURE if temperature is None else temperature
    chain = _chain()
    last = None
    for i, (p, model) in enumerate(chain):
        try:
            return _gen_one(p, model, system, user, mt, temp, params)
        except Exception as ex:  # noqa: BLE001 — 留到链尾再抛
            last = ex
            if i + 1 < len(chain):
                continue
            raise last


def _stream_one(p: str, model: str, system: str, user: str, mt: int, temp: float, params: dict | None):
    if p == "openai":
        yield from _openai_stream(system, user, mt, temp, params, model)
    elif p == "anthropic":
        yield from _anthropic_stream(system, user, mt, temp, params, model)
    elif p == "ollama":
        yield from _ollama_stream(system, user, temp, params, model)
    elif p == "stub":
        txt = _stub(system, user)
        for i in range(0, len(txt), 12):
            yield txt[i:i + 12]
    else:
        raise ValueError(f"未知 provider:{p}(stub|openai|anthropic|ollama)")


def stream(system: str, user: str, *, temperature: float | None = None, params: dict | None = None):
    """流式生成:逐块 yield 文本增量。主 provider 若在出第一个字之前就失败,自动切备援(已出字则交由上层回退)。"""
    mt = config.LLM_MAX_TOKENS
    temp = config.LLM_TEMPERATURE if temperature is None else temperature
    chain = _chain()
    for i, (p, model) in enumerate(chain):
        started = False
        try:
            for piece in _stream_one(p, model, system, user, mt, temp, params):
                started = True
                yield piece
            return
        except Exception:  # noqa: BLE001
            if started or i + 1 >= len(chain):
                raise            # 已开始吐字 → 不能中途换源(交由上层回退);或已是链尾
            continue             # 连接阶段就挂且有备援 → 换下一个


def _stream_req(url: str, body: dict, headers: dict, timeout: int | None = None):
    """打开一个流式 POST,逐行 yield 已 strip 的文本行(SSE/JSONL 通用)。"""
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout or config.LLM_TIMEOUT) as r:
        for raw in r:                       # urllib 响应可按行迭代
            line = raw.decode("utf-8", "ignore").strip()
            if line:
                yield line


def _sse_deltas(lines, pick):
    """从 SSE 行流里抽增量:pick(chunk_dict)->文本片段|None。"""
    for line in lines:
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if not payload or payload == "[DONE]":
            continue
        try:
            chunk = json.loads(payload)
        except json.JSONDecodeError:
            continue
        piece = pick(chunk)
        if piece:
            yield piece


def _openai_stream(system, user, mt, temp, params=None, model=None):
    if not config.OPENAI_API_KEY:
        raise ValueError("缺 OPENAI_API_KEY")
    model = model or config.MODEL or "gpt-4o-mini"
    body = {"model": model, "stream": True, "max_tokens": mt, "temperature": temp,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    body.update(_samplers(params, _OPENAI_SAMPLERS))
    lines = _stream_req(f"{config.OPENAI_BASE_URL}/chat/completions", body,
                        {"Authorization": f"Bearer {config.OPENAI_API_KEY}"})
    yield from _sse_deltas(lines, lambda c: next(
        ((ch.get("delta") or {}).get("content") for ch in c.get("choices", []) if (ch.get("delta") or {}).get("content")), None))


def _anthropic_stream(system, user, mt, temp, params=None, model=None):
    if not config.ANTHROPIC_API_KEY:
        raise ValueError("缺 ANTHROPIC_API_KEY")
    model = model or config.MODEL or "claude-sonnet-4-6"
    body = {"model": model, "stream": True, "max_tokens": mt, "temperature": temp, "system": system,
            "messages": [{"role": "user", "content": user}]}
    body.update(_samplers(params, _ANTHROPIC_SAMPLERS))
    lines = _stream_req("https://api.anthropic.com/v1/messages", body,
                        {"x-api-key": config.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"})
    yield from _sse_deltas(lines, lambda c: (c.get("delta") or {}).get("text") if c.get("type") == "content_block_delta" else None)


def _ollama_stream(system, user, temp, params=None, model=None):
    model = model or config.MODEL or "qwen2.5"
    opts = {"temperature": temp, **_samplers(params, _OLLAMA_SAMPLERS, _OLLAMA_REMAP)}
    for line in _stream_req(f"{config.OLLAMA_BASE_URL}/api/chat",
                            {"model": model, "stream": True, "options": opts,
                             "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
                            {}):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        piece = (obj.get("message") or {}).get("content")
        if piece:
            yield piece
        if obj.get("done"):
            break


def _post(url: str, body: dict, headers: dict, timeout: int | None = None) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout or config.LLM_TIMEOUT) as r:
        ctype = r.headers.get("Content-Type", "")
        raw = r.read().decode("utf-8")
    # 有些 OpenAI 兼容代理(one-api 等)对部分模型强制 SSE 流式,即使没传 stream。
    # body 形如 `data: {chunk}` 而非整块 JSON,这里合并回非流式结构,调用方无感。
    if "text/event-stream" in ctype or raw.lstrip().startswith("data:"):
        return _merge_sse(raw)
    return json.loads(raw)


def _merge_sse(raw: str) -> dict:
    """合并 OpenAI 兼容 SSE 流(逐块 choices[].delta.content)为非流式响应结构。"""
    text: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if not payload or payload == "[DONE]":
            continue
        try:
            chunk = json.loads(payload)
        except json.JSONDecodeError:
            continue
        for ch in chunk.get("choices", []):
            piece = (ch.get("delta") or {}).get("content")
            if piece:
                text.append(piece)
    return {"choices": [{"message": {"content": "".join(text)}}]}


def _openai(system: str, user: str, mt: int, temp: float, params: dict | None = None, model=None) -> str:
    if not config.OPENAI_API_KEY:
        raise ValueError("缺 OPENAI_API_KEY")
    model = model or config.MODEL or "gpt-4o-mini"
    body = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "max_tokens": mt, "temperature": temp}
    body.update(_samplers(params, _OPENAI_SAMPLERS))      # 预设采样参数覆盖默认
    d = _post(f"{config.OPENAI_BASE_URL}/chat/completions", body,
              {"Authorization": f"Bearer {config.OPENAI_API_KEY}"})
    return d["choices"][0]["message"]["content"].strip()


def _anthropic(system: str, user: str, mt: int, temp: float, params: dict | None = None, model=None) -> str:
    if not config.ANTHROPIC_API_KEY:
        raise ValueError("缺 ANTHROPIC_API_KEY")
    model = model or config.MODEL or "claude-sonnet-4-6"
    body = {"model": model, "max_tokens": mt, "temperature": temp, "system": system,
            "messages": [{"role": "user", "content": user}]}
    body.update(_samplers(params, _ANTHROPIC_SAMPLERS))
    d = _post("https://api.anthropic.com/v1/messages", body,
              {"x-api-key": config.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"})
    return "".join(b.get("text", "") for b in d.get("content", [])).strip()


def _ollama(system: str, user: str, temp: float, params: dict | None = None, model=None) -> str:
    model = model or config.MODEL or "qwen2.5"
    opts = {"temperature": temp, **_samplers(params, _OLLAMA_SAMPLERS, _OLLAMA_REMAP)}
    d = _post(f"{config.OLLAMA_BASE_URL}/api/chat",
              {"model": model, "stream": False, "options": opts,
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
              {})
    return d["message"]["content"].strip()


def _stub(system: str, user: str) -> str:
    """占位生成:返回可用的 markdown 骨架,标明是 stub —— 让未配 key 时流程仍能跑通/测试。"""
    head = user.strip().splitlines()[0][:40] if user.strip() else "未命名"
    return (f"# {head}（stub 占位）\n\n"
            f"> ⚠ 当前 SV_PROVIDER=stub,这是占位文本。配置真实 provider(openai/anthropic/ollama)后由模型生成。\n\n"
            f"## 生成请求摘要\n{user.strip()[:400]}\n")
