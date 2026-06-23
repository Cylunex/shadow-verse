"""透镜测试 —— narrate 落章+门控+自动质检、play 条件写回、simulate/render 默认关。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_lens_")

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import lenses  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

w = World.create("w", "W", genre="无限流")
t = Thread.create(w, "t", "线", genre="无限流")
LocalEntity.create(w, "hero", "主角", role="main")
LocalEntity.create(w, "side", "配角", role="secondary")
LocalEntity.create(w, "cam", "客串", role="cameo")

# narrate_prep 带配方
pk = lenses.narrate_prep(w, t, brief="试")
ok(pk["recipe"]["pacing"], "写作包带题材配方 pacing")
ok(pk["writing_chapter"] == 1, "下一章=1")

# narrate_commit:门控 + beat + 自动质检
rc = lenses.narrate_commit(w, t, {
    "chapter_text": "第一层规则自相矛盾，主角看穿了缝隙。" * 12, "title": "破局",
    "sediments": [{"entity": "hero", "text": "看穿规则缝隙", "level": "持久"},
                  {"entity": "side", "text": "第一次有用", "level": "身份"},
                  {"entity": "cam", "text": "被吓退", "level": "瞬时"}],
    "state_updates": {"hero": {"location": "第二层", "mood": "戒备"}},
})
ok(len(rc["sedimented"]) == 2 and len(rc["skipped"]) == 1, "narrate 沉淀:cameo 被门控丢弃")
ok("auto_checks" in rc, "落章回执带自动质检")
ok(t.beats() and t.beats()[-1]["lens"] == "narrate", "记下 narrate beat")
ok(t.meta()["chapter_count"] == 1, "章数推进")

# play_commit:条件写回 + 标记 play 透镜
pr = lenses.play_commit(w, t, {
    "scene": "歇脚", "transcript": "……",
    "growth": [{"entity": "side", "text": "违逆主角", "trigger": True},
               {"entity": "hero", "text": "情绪波动", "trigger": False}],
})
ok(len(pr["written_back"]) == 1 and len(pr["candidates"]) == 1, "play:触发才写回,余者候选")
ok("play" in t.meta()["lenses"], "玩过的线标记 play 透镜")

# 统一写入口 commit_core:唯一落盘路径 + 闭合透镜标签 + 角色门控
from sv.lens import commit_core, LENS_TAGS  # noqa: E402
beats_before = len(t.beats())
core = commit_core(w, t, lens="play", where="play:probe", beat="探针 beat",
                   sediments=[{"entity": "hero", "text": "成长", "level": "持久"},
                              {"entity": "cam", "text": "客串", "level": "瞬时"}])
ok(len(t.beats()) == beats_before + 1 and t.beats()[-1]["where"] == "play:probe", "commit_core 落 beat 到统一时间线")
ok(len(core["sedimented"]) == 1 and len(core["skipped"]) == 1, "commit_core 角色门控:cameo 客串被丢弃")
ok("play" in LENS_TAGS and "companion" in LENS_TAGS and "cross" in LENS_TAGS, "透镜标签集为新门预留(companion/cross)")
try:
    commit_core(w, t, lens="not-a-lens", beat="x"); ok(False, "未知透镜标签应报错")
except ValueError:
    ok(True, "commit_core 拒绝闭合集外的透镜标签")

# simulate 默认关 / render 未配休眠
ok(lenses.simulate_prep(w, t).get("enabled") is False, "simulate 默认关")
ok(lenses.render_prep(w, "主角立绘").get("enabled") is False, "render 未配 key 休眠")
ok("image_prompt" in lenses.render_prep(w, "x", appearance="冷峻"), "render 仍组装 prompt(接口在)")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
