"""LLM 生成回路测试(stub 路径,无需 key)—— 生成函数 + 章节切分解析。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_llm_")
os.environ["SV_PROVIDER"] = "stub"

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import forge, llm  # noqa: E402
from sv.lenses import _split_chapter, narrate_generate  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

ok(llm.available() is False, "stub 模式 available()=False")
ok(isinstance(llm.generate("s", "u"), str) and llm.generate("s", "u"), "stub generate 返回非空文本")

w = World.create("w", "W", genre="无限流")
body = forge.generate_world_body("一座规则之塔", genre="无限流")
ok(isinstance(body, str) and len(body) > 0, "generate_world_body 出文本")

forge.entity_commit(w, "hero", "主角", "# 主角\n## 核心事实\n- 护人\n", role="main")
eb = forge.generate_entity_body(w, "守护者", role="main")
ok("stub" in eb or len(eb) > 0, "generate_entity_body 出文本")

t = Thread.create(w, "t", "线", genre="无限流")
gc = narrate_generate(w, t, intent="开篇")
ok("chapter_text" in gc and isinstance(gc["sediments"], list), "narrate_generate 返回 chapter_text + sediments")

# 章节切分解析:正文 + ===沉淀=== + JSON
raw = '# 试章\n这是正文第一段。\n第二段。\n===沉淀===\n{"sediments":[{"entity":"hero","text":"成长","level":"身份"}],"state_updates":{"hero":{"mood":"决绝"}}}'
parsed = _split_chapter(raw)
ok(parsed["title"] == "试章", "切分:提取标题")
ok("正文第一段" in parsed["chapter_text"] and "===" not in parsed["chapter_text"], "切分:正文不含分隔符与 JSON")
ok(parsed["sediments"] and parsed["sediments"][0]["entity"] == "hero", "切分:解析出沉淀")
ok(parsed["state_updates"].get("hero", {}).get("mood") == "决绝", "切分:解析出状态更新")
# 无 JSON 时也不崩
p2 = _split_chapter("# 纯正文\n只有正文没有沉淀块。")
ok(p2["chapter_text"] and p2["sediments"] == [], "切分:无 JSON 块时仅正文、沉淀空")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
