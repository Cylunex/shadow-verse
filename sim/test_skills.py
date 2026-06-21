"""Skills 加载器测试 —— frontmatter 解析 / 三 scope later-wins / 菜单注入 / 种子 / narrate 接入。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_sk_")

from sv import clock, skills  # noqa: E402

clock.use_virtual()

from sv import lenses  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# frontmatter 解析
meta, body = skills.parse_frontmatter("---\nname: foo\ndescription: 测试包\nscope: global\n---\n\n正文内容")
ok(meta["name"] == "foo" and meta["description"] == "测试包" and body == "正文内容", "frontmatter 解析")
ok(skills.parse_frontmatter("无 frontmatter 纯正文") == ({}, "无 frontmatter 纯正文"), "无 frontmatter 退化")

# name 校验
try:
    skills.add_skill("Bad Name!", "x", "y"); ok(False, "非法 name 应报错")
except ValueError:
    ok(True, "非法 name(空格/大写)拒绝")

# 写 + 读 + 列
skills.add_skill("test-skill", "测试技能", "# 测试\n用具体动作代替形容词。")
s = skills.get_skill("test-skill")
ok(s and "具体动作" in s["body"], "写入+读取 skill 正文")
ok(skills.read_skill("test-skill").startswith("# 测试"), "read_skill 取正文")
ok(any(x["name"] == "test-skill" for x in skills.list_skills()), "列出 skill")

# 三 scope later-wins(同名 character 覆盖 global)
skills.add_skill("voice", "全局版", "global body", scope="global")
skills.add_skill("voice", "角色版", "character body", scope="character")
vis = skills.visible("character")
voice = next(x for x in vis if x["name"] == "voice")
ok(voice["scope"] == "character" and voice["description"] == "角色版", "同名 character 覆盖 global")
# scope=global 时看不到 character 级
vis_g = skills.visible("global")
ok(all(x["scope"] == "global" for x in vis_g), "scope=global 只见 global 级")

# 菜单注入(短目录)
menu = skills.available_menu("character")
ok("<available_skills>" in menu and "test-skill: 测试技能" in menu, "available_menu 短目录")

# 种子幂等
n1 = skills.seed()
ok(n1 == 3, "首次种子灌入 3 个起始 skill")
ok(skills.seed() == 0, "再次种子幂等(已存在跳过)")
ok(skills.get_skill("anti-cliche-zh") and "data-person" in skills.read_skill("anti-cliche-zh"), "反套话 skill 可读")

# narrate_prep 接入
w = World.create("w", "W", genre="玄幻")
t = Thread.create(w, "line", "线", genre="玄幻")
pkt = lenses.narrate_prep(w, t)
ok("skills" in pkt and "anti-cliche-zh" in pkt["skills"], "narrate 包带 skills 短目录")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
