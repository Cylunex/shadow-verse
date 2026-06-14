"""管理 + 导出测试 —— 删除(世界/线/实体/元件/连接,含枢纽清理) + 全书导出。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_mng_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import codex, export, nexus  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.lenses import narrate_commit  # noqa: E402
from sv.nexus import NexusEntity  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# 元件删除
codex.add("themes", "x-theme", "临时母题", tags=["t"])
ok(any(e["id"] == "x-theme" for e in codex.all_elements()), "元件已加")
ok(codex.remove("themes", "x-theme") and not any(e["id"] == "x-theme" for e in codex.all_elements()), "元件删除")

# 建两世界 + 实体 + 线 + 章
w1 = World.create("w1", "世界一", genre="无限流")
w2 = World.create("w2", "世界二", genre="都市")
e = LocalEntity.create(w1, "hero", "主角", role="main", body="# 主角\n## 核心事实\n- 护人")
t = Thread.create(w1, "t", "首章线", genre="无限流")
narrate_commit(w1, t, {"chapter_text": "第一章正文。" * 20, "title": "起", "sediments": [{"entity": "hero", "text": "出场", "level": "持久"}]})
narrate_commit(w1, t, {"chapter_text": "第二章正文。" * 20, "title": "承"})

# 导出全书
book = export.compile_thread_book(w1, t)
ok(book["chapters"] == 2 and "第一章正文" in book["content"] and "第二章正文" in book["content"], "导出含全部章节")
ok(book["filename"] == "w1-t.md" and book["hanzi"] > 0, "导出文件名+字数")
ok("# 首章线" in book["content"], "导出含书名标题")

# 升格 + 互联 + 召唤,再删世界验证枢纽清理
nexus.ascend(w1, "hero")
nexus.link_worlds("w1", "w2", "裂隙")
nexus.summon("hero", w2, entry="换皮进")
ok("w2" in NexusEntity.load("hero").incarnations() and len(nexus.links()) == 1, "删前:化身w2+连接就位")

# 删实体
LocalEntity.load(w1, "hero").delete()
ok(not LocalEntity(w1, "hero").exists(), "实体删除(枢纽升格副本不受影响)")
ok(NexusEntity.load("hero").exists(), "升格的跨世界实体独立存活")

# 删线
t.delete()
ok(not Thread(w1, "t").exists() and "t" not in w1.list_threads(), "叙事线删除")

# 断连接
nexus.unlink("w1", "w2")
ok(len(nexus.links()) == 0, "连接断开")
nexus.link_worlds("w1", "w2", "重连")  # 重新连上,验证 purge_world

# 删世界 w2:purge 应清掉 w1↔w2 连接 + hero 在 w2 的化身
nexus.purge_world("w2"); World("w2").delete()
ok(not World("w2").exists(), "世界删除")
ok(len(nexus.links()) == 0, "purge:删世界连带清连接")
ok("w2" not in NexusEntity.load("hero").incarnations(), "purge:删世界连带清化身")
ok(all(l.get("to") != "w2" for l in World.load("w1").meta().get("links", [])), "w1.meta 不再指向已删的 w2")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
