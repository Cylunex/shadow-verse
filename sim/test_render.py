"""render 透镜测试(休眠路径,无需 key)—— 优雅禁用、prompt 组装、实体 appearance 锁脸。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_rnd_")
os.environ["SV_RENDER"] = "none"   # 未配 → 休眠

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import lenses  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

w = World.create("w", "W", genre="无限流")
t = Thread.create(w, "t", "线")
e = LocalEntity.create(w, "hero", "主角", role="main", appearance="26yo man, scar on brow, black coat")

ok(lenses.render_available() is False, "未配时 render_available()=False")
# prep 仍组装 prompt(接口在),enabled=False
rp = lenses.render_prep(w, "a lone figure", appearance="cinematic")
ok("cinematic" in rp["image_prompt"] and rp["enabled"] is False, "render_prep 组 prompt 但休眠")

# 实体 appearance 落盘 + 取用
ok(e.appearance == "26yo man, scar on brow, black coat", "实体 appearance 落盘")
e.set_appearance("28yo, silver hair")
ok(LocalEntity.load(w, "hero").appearance == "28yo, silver hair", "set_appearance 更新")

# 休眠时各 render 调用优雅返回 enabled:False,不抛
rs = lenses.render_scene(w, t, "giant gate")
ok(rs.get("enabled") is False and "未启用" in rs.get("note", ""), "render_scene 休眠优雅返回")
re_ = lenses.render_entity(w, e, "in the rain")
ok(re_.get("enabled") is False, "render_entity 休眠优雅返回")
# 未真出图,故不应建 portraits 目录
ok(not (e.dir / "portraits").exists(), "休眠不产生空目录/文件")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
