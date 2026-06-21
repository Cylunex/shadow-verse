"""提示词组装器 —— 把 ST 预设的有序模块 + marker 槽 + @D 深度注入,拼成 system/user/depth。

借鉴 Narratium preset-assembler(有序段落)。**预设管人格/越狱/语气/世界观注入;引擎仍掌产物结构契约**
(章标题/沉淀 JSON/字数),故 assemble 只产"人格那半",结构契约由调用方拼在后面。
无预设时返回空骨架(调用方走自己的手写默认,不回退能力)。
"""
from __future__ import annotations


def assemble(preset: dict | None, slots: dict | None = None) -> dict:
    """按 preset['order'] 拼模块:marker/空 content 取 slots[identifier];role 决定进 system 还是 user;
    injection_position==1(ABSOLUTE/@D)收进 depth_msgs。返回 {system, user, depth_msgs}。"""
    slots = slots or {}
    if not preset:
        return {"system": "", "user": "", "depth_msgs": []}
    sys_parts, user_parts, depth_msgs = [], [], []
    for m in preset.get("modules", []):
        content = m.get("content") or ""
        if m.get("marker") or not content.strip():
            content = (slots.get(m.get("identifier")) or "").strip()
        if not content:
            continue
        if m.get("injection_position") == 1:   # ABSOLUTE → @D 深度注入
            depth_msgs.append({"depth": m.get("injection_depth") or 4,
                               "role": m.get("role", "system"), "content": content})
            continue
        (user_parts if m.get("role") in ("user", "assistant") else sys_parts).append(content)
    return {"system": "\n\n".join(sys_parts), "user": "\n\n".join(user_parts), "depth_msgs": depth_msgs}


def apply_depth(history_msgs: list, depth_msgs: list) -> list:
    """把 @D 注入插到对话历史倒数第 depth 条之前(author's note / depth prompt 的载体)。"""
    msgs = list(history_msgs or [])
    for inj in sorted(depth_msgs or [], key=lambda x: x.get("depth", 4)):
        pos = max(0, len(msgs) - int(inj.get("depth", 4)))
        msgs.insert(pos, {"role": inj.get("role", "system"), "content": inj.get("content", "")})
    return msgs


def depth_from_card(card: dict) -> list:
    """角色卡 depth_prompt → 一条 @D 注入(角色私货,贯穿全程)。"""
    dp = card.get("depth_prompt")
    if isinstance(dp, dict) and (dp.get("prompt") or "").strip():
        role = dp.get("role", 0)
        role = {0: "system", 1: "user", 2: "assistant"}.get(role, role) if isinstance(role, int) else role
        return [{"depth": dp.get("depth", 4), "role": role, "content": dp["prompt"].strip()}]
    return []
