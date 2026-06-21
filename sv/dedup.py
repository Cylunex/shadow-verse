"""别名合并 —— 同一实体在不同来源被抽成多条(全名/简称/昵称/代号)时归一。

借鉴 Novel-Auto-Generator/mergeService.js:启发式粗筛 → (可选 LLM 精判) → UnionFind 并查集 → 主名选择。
另附「LLM 输出归一化三件套」(容忍模型乱答字段名/编号错位/中文布尔)——所有「让 LLM 返结构化判断」处都用得上。
纯算法零依赖。用于:导入小说语料/世界书去重、记忆实体归一、跨世界同一角色合并。
"""
from __future__ import annotations


# ---------- UnionFind(路径压缩 + 按秩合并)----------
class UnionFind:
    def __init__(self, n: int):
        self.p = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.p[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1

    def groups(self) -> dict[int, list[int]]:
        out: dict[int, list[int]] = {}
        for i in range(len(self.p)):
            out.setdefault(self.find(i), []).append(i)
        return out


# ---------- LLM 输出归一化三件套 ----------
_TRUE = {"true", "1", "yes", "y", "same", "是", "同一", "同一人", "对", "相同"}


def normalize_flag(v) -> bool:
    """把 LLM 各种乱答(true/"是"/"同一"/1/"相同")归一成布尔。"""
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    return str(v).strip().lower() in _TRUE


def results_array(j) -> list:
    """从 LLM 返回里取出判定数组,兼容 results/result/pairs/judgements/judgments/data 各种字段名。"""
    if isinstance(j, list):
        return j
    if isinstance(j, dict):
        for k in ("results", "result", "pairs", "judgements", "judgments", "data", "items"):
            v = j.get(k)
            if isinstance(v, list):
                return v
        # 没有数组字段但本身像一条判定 → 包成单元素
        if any(k in j for k in ("same", "isSamePerson", "index", "main")):
            return [j]
    return []


def resolve_pair_index(item: dict, pairs: list[tuple]) -> int | None:
    """把一条 LLM 判定映射回它指的 pair 下标:优先 index 字段,否则按名字双向匹配。"""
    idx = item.get("index", item.get("pair", item.get("id")))
    if isinstance(idx, int) and 0 <= idx < len(pairs):
        return idx
    if isinstance(idx, str) and idx.isdigit() and 0 <= int(idx) < len(pairs):
        return int(idx)
    a = str(item.get("a") or item.get("name1") or item.get("name_a") or "").strip()
    b = str(item.get("b") or item.get("name2") or item.get("name_b") or "").strip()
    if a and b:
        for k, (na, nb) in enumerate(pairs):
            if {a, b} == {na, nb}:
                return k
    return None


# ---------- 别名合并主流程 ----------
def _suspect(a: dict, b: dict) -> bool:
    """启发式粗筛:疑似同一实体?(简称包含 / 末2字昵称 / 关键词交集)。"""
    na, nb = (a.get("name") or "").strip(), (b.get("name") or "").strip()
    if not na or not nb:
        return False
    if na == nb:
        return True
    if na in nb or nb in na:           # 简称包含全名(「无道」⊂「叶无道」)
        return True
    short, long = (na, nb) if len(na) <= len(nb) else (nb, na)
    if 2 <= len(short) <= 3 and short[-2:] in long:   # 末2字昵称
        return True
    ka, kb = set(a.get("keywords") or []), set(b.get("keywords") or [])
    if ka and kb and (ka & kb):        # 关键词交集
        return True
    return False


def candidate_pairs(items: list[dict]) -> list[tuple[int, int]]:
    return [(i, j) for i in range(len(items)) for j in range(i + 1, len(items)) if _suspect(items[i], items[j])]


def _merge_group(members: list[dict], main_hint: str | None = None) -> dict:
    main = main_hint or max(members, key=lambda m: len(m.get("content", "")))["name"]
    keywords = sorted({kw for m in members for kw in (m.get("keywords") or [])})
    content = "\n---\n".join(m.get("content", "").strip() for m in members if m.get("content", "").strip())
    return {"name": main, "keywords": keywords, "content": content,
            "aliases": [m.get("name") for m in members], "merged_from": len(members)}


def merge_aliases(items: list[dict], *, verify=None) -> dict:
    """合并别名条目。items:[{name, keywords?, content?}]。

    verify:可选 callable(a, b) → {"same":bool/各种, "main":主名?};不给则纯启发式合并。
    返回 {merged:[...合并后条目], groups:[[别名...]], pairs_checked:N}。
    """
    pairs = candidate_pairs(items)
    uf = UnionFind(len(items))
    main_pref: dict[int, str] = {}   # 组内首选主名(LLM 给的)
    for (i, j) in pairs:
        same = True
        if verify is not None:
            res = verify(items[i], items[j]) or {}
            same = normalize_flag(res.get("same", res.get("isSamePerson")))
            if same and res.get("main"):
                main_pref[i] = res["main"]
        if same:
            uf.union(i, j)
    merged, groups = [], []
    for _, idxs in uf.groups().items():
        members = [items[k] for k in idxs]
        if len(idxs) == 1:
            merged.append(items[idxs[0]])
            continue
        hint = next((main_pref[k] for k in idxs if k in main_pref), None)
        merged.append(_merge_group(members, hint))
        groups.append([m.get("name") for m in members])
    return {"merged": merged, "groups": groups, "pairs_checked": len(pairs)}
