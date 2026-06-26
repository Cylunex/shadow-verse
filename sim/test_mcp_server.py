"""H1.1 测试 —— MCP server 契约护栏(OpenClaw 命脉):
   ① tools/list 的每个 inputSchema 合法(type/required⊆properties/属性 type)、工具名唯一;
   ② 代表性 tools/call round-trip(无参 / *_prep 取包 / 带 payload 的 *_commit)验证 argv+payload 映射;
   ③ 未知工具 / 缺必填参数 / 引擎抛错 → 结构化 isError,不崩。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_mcp_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import mcp_server as M  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

VALID_TYPES = {"string", "integer", "object"}

def call(name, args):
    return M._handle({"jsonrpc": "2.0", "id": 9, "method": "tools/call",
                      "params": {"name": name, "arguments": args}})["result"]

# ---------- ① tools/list 契约 ----------
tools = M._handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})["result"]["tools"]
names = [t["name"] for t in tools]
ok(len(names) >= 50, f"工具数合理({len(names)})")
ok(len(names) == len(set(names)), "工具名无重复")
ok(len(M._BY) == len(M.TOOLS), "_BY 无重复 key(TOOLS 名唯一)")
bad = []
for t in tools:
    s = t.get("inputSchema", {})
    if not t.get("name") or not t.get("description"):
        bad.append(str(t.get("name")) + ":缺 name/desc")
    if s.get("type") != "object":
        bad.append(t["name"] + ":type≠object")
    props, req = s.get("properties", {}), s.get("required", [])
    if not set(req) <= set(props):
        bad.append(t["name"] + ":required⊄properties")
    for k, pv in props.items():
        if pv.get("type") not in VALID_TYPES:
            bad.append(t["name"] + "." + k + ":坏 type")
ok(not bad, "每个工具 inputSchema 合法" + (" — " + "；".join(bad[:3]) if bad else ""))

# ---------- ② 代表性 tools/call round-trip ----------
r = call("codex_seed", {})
ok(r["isError"] is False and r["content"][0]["text"] != "(无输出)", "无参工具 codex_seed round-trip 成功有输出")
r = call("world_prep", {"prompt": "一座塔", "genre": "无限流"})
ok(not r["isError"] and "pacing" in r["content"][0]["text"], "*_prep:位置参数 + 选项映射(world_prep 注入配方)")
r = call("world_commit", {"payload": {"id": "tw", "name": "塔", "genre": "无限流", "body": "# 塔\n规则。"}})
ok(not r["isError"], "*_commit:payload 经 stdin 注入 round-trip")
ok(World("tw").exists(), "world_commit 真落盘(payload→skill_api commit)")
r = call("entity_commit", {"world": "tw", "payload": {"id": "su", "name": "苏", "role": "main", "body": "# 苏"}})
ok(not r["isError"] and LocalEntity(World("tw"), "su").exists(), "*_commit:位置参数(world)+payload 同时映射")

# ---------- ③ 错误结构化、不崩 ----------
r = call("no_such_tool", {})
ok(r["isError"] is True and "未知" in r["content"][0]["text"], "未知工具 → isError 不崩")
r = call("review_prep", {"world": "tw"})   # 缺 thread/chapter
ok(r["isError"] is True, "缺必填参数 → isError 不崩(接住 argparse SystemExit)")
r = call("narrate_prep", {"world": "不存在", "thread": "x"})   # 引擎抛 FileNotFoundError
ok(r["isError"] is True, "引擎抛错(世界不存在) → isError 不崩")

# ---------- ④ 工具分层(OPENCLAW A1):SV_MCP_TIER 收敛 tools/list ----------
def listed():
    return [t["name"] for t in M._handle({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})["result"]["tools"]]
alln = listed()
ok(len(alln) == len(M.TOOLS), "缺省 SV_MCP_TIER:全暴露(向后兼容)")
os.environ["SV_MCP_TIER"] = "1"
t1 = listed()
ok(t1 and all(M._tier(n) == 1 for n in t1) and "play_prep" in t1 and "gen_world" not in t1,
   "SV_MCP_TIER=1 只暴露 Tier1(含 play_prep,不含 gen_world)")
os.environ["SV_MCP_TIER"] = "2"
t2 = listed()
ok(len(t1) < len(t2) < len(alln) and "narrate_prep" in t2, "SV_MCP_TIER=2 含创作工具,介于 Tier1 与全量之间")
ok(M._call("codex_seed", {})["isError"] is False, "分层只收敛 tools/list,未广告的工具仍可 tools/call")
del os.environ["SV_MCP_TIER"]
ok(len(listed()) == len(M.TOOLS), "清掉 env 恢复全暴露")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
