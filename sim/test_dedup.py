"""别名合并测试 —— UnionFind / 启发式粗筛 / LLM 输出归一化三件套 / 主名选择。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_dd_")

from sv import dedup  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# UnionFind
uf = dedup.UnionFind(5)
uf.union(0, 1); uf.union(1, 2); uf.union(3, 4)
g = uf.groups()
ok(uf.find(0) == uf.find(2) and uf.find(0) != uf.find(3), "并查集传递合并(A=B,B=C→A=C)")
ok(sorted(len(v) for v in g.values()) == [2, 3], "连通分量大小 [2,3]")

# 归一化三件套
ok(dedup.normalize_flag("是") and dedup.normalize_flag(1) and dedup.normalize_flag("same"), "flag 归一:是/1/same→True")
ok(not dedup.normalize_flag("否") and not dedup.normalize_flag(0) and not dedup.normalize_flag("no"), "flag 归一:否/0/no→False")
ok(dedup.results_array({"results": [1, 2]}) == [1, 2], "results_array 取 results 字段")
ok(dedup.results_array({"judgements": [3]}) == [3], "results_array 兼容 judgements")
ok(dedup.results_array([{"same": True}]) == [{"same": True}], "results_array 本身是列表")
ok(dedup.results_array({"same": True, "index": 0}) == [{"same": True, "index": 0}], "单条判定包成列表")
pairs = [("叶无道", "无道"), ("苏晴", "晴儿")]
ok(dedup.resolve_pair_index({"index": 1, "same": True}, pairs) == 1, "resolve 按 index")
ok(dedup.resolve_pair_index({"a": "晴儿", "b": "苏晴"}, pairs) == 1, "resolve 按名字双向匹配")
ok(dedup.resolve_pair_index({"a": "x", "b": "y"}, pairs) is None, "resolve 对不上→None")

# 启发式粗筛
ok(dedup._suspect({"name": "叶无道"}, {"name": "无道"}), "简称包含全名")
ok(dedup._suspect({"name": "苏晴", "keywords": ["画室"]}, {"name": "晴姐", "keywords": ["画室"]}), "关键词交集")
ok(not dedup._suspect({"name": "张三"}, {"name": "李四"}), "无关不误判")

# 纯启发式合并(无 LLM)
items = [
    {"name": "叶无道", "keywords": ["黑道", "话事人"], "content": "黑道话事人,护短"},
    {"name": "无道", "keywords": ["话事人"], "content": "外号"},
    {"name": "苏晴", "keywords": ["画室"], "content": "插画师"},
    {"name": "张三", "keywords": ["路人"], "content": "路人甲"},
]
r = dedup.merge_aliases(items)
ok(len(r["merged"]) == 3, "4 条合并成 3 条(叶无道+无道 合一)")
yw = next(m for m in r["merged"] if m.get("merged_from"))
ok(yw["merged_from"] == 2 and set(yw["aliases"]) == {"叶无道", "无道"}, "合并组含两别名")
ok(yw["name"] == "叶无道", "主名默认取内容最长者")
ok("黑道" in yw["keywords"] and "话事人" in yw["keywords"], "合并去重关键词")
ok("---" in yw["content"], "合并内容用 --- 拼接")

# 带 LLM 精判(假 verify:只认含「画室」的为同一,叶无道们判不同)
def fake_verify(a, b):
    if "画室" in (a.get("keywords") or []) and "画室" in (b.get("keywords") or []):
        return {"same": "是", "main": "苏晴老师"}
    return {"same": False}
items2 = [
    {"name": "苏晴", "keywords": ["画室"], "content": "插画师"},
    {"name": "晴姐", "keywords": ["画室"], "content": "称呼"},
    {"name": "叶无道", "keywords": ["黑道"], "content": "话事人"},
    {"name": "无道", "keywords": ["黑道"], "content": "外号"},
]
r2 = dedup.merge_aliases(items2, verify=fake_verify)
su = next((m for m in r2["merged"] if m.get("merged_from")), None)
ok(su and su["name"] == "苏晴老师", "LLM 精判:同一→用 LLM 给的主名")
ok(not any(m.get("merged_from") and "叶无道" in (m.get("aliases") or []) for m in r2["merged"]),
   "LLM 判不同:叶无道/无道 不被合并")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
