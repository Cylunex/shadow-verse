"""H1.2 测试 —— merge 世界融合(暗宇宙铺路):src 角色/线/设定并入 dst,不丢数据,默认删源。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_merge_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import merge, util  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

src = World.create("src", "小世界", genre="玄幻", body="# 小世界\n一处秘境。")
LocalEntity.create(src, "hero", "主角", role="main")
Thread.create(src, "line", "源线", genre="玄幻")
dst = World.create("dst", "大世界", genre="玄幻", body="# 大世界\n主线在此。")

r = merge.merge_world("src", "dst")
ok(r["deleted_src"] is True, "默认融完删源")
ok(r["moved_entities"] == ["hero"] and r["moved_threads"] == ["line"], "返回搬运清单")
ok("hero" in dst.list_entities(), "角色并入 dst(不丢)")
ok("line" in dst.list_threads(), "叙事线并入 dst")
tdst = Thread(dst, "line")
ok(tdst.meta().get("world") == "dst", "并入的线 world 字段改指 dst")
dst_md = util.read_md(dst.dir / "world.md")
ok(merge.MERGE_MARK + ":src" in dst_md and "秘境" in dst_md, "源世界设定并入目标(可见来源标记块)")
ok(not World("src").exists(), "源世界已删")

# id 撞名 → 自动改名,不覆盖
src2 = World.create("src2", "再来", genre="玄幻")
LocalEntity.create(src2, "hero", "另一个主角", role="main")   # 与 dst 的 hero 撞名
r2 = merge.merge_world("src2", "dst")
ok(r2["moved_entities"] and r2["moved_entities"][0] != "hero", "撞名实体自动改名,不覆盖原 hero")
ok(LocalEntity(dst, "hero").card().get("name") == "主角", "原 hero 未被覆盖")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
