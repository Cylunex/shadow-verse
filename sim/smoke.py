"""端到端冒烟 —— 证明五层地基贯通(AIGC 多元宇宙)。

L0 元件 → L1 锻造世界/实体/线 → L3 读/玩透镜(沉淀+核心循环铁律) → L4 升格+第二世界+互联+跨世界召唤化身。
跑:PYTHONUTF8=1 python -m sim.smoke
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="sv_smoke_"))
os.environ["SV_UNIVERSE_DIR"] = str(_TMP)

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import checks, codex, forge, lenses, nexus  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.nexus import NexusEntity  # noqa: E402
from sv.thread import Thread  # noqa: E402
from sv.world import World  # noqa: E402

PASS, FAIL = [], []


def ok(c, label):
    (PASS if c else FAIL).append(label)
    print(("  ✓ " if c else "  ✗ ") + label)


print(f"临时 universe:{_TMP}\n")

# L0 元件库
print("[L0] 元件库取料")
codex.add("worlds", "infinite-tower", "无限攀登的塔,每层一个规则世界", tags=["无限流", "规则"])
codex.add("mechanics", "rule-horror", "规则怪谈:照做活、违则死,规则自相矛盾是钩子", tags=["规则", "悬疑"])
codex.add("characters", "cold-protector", "外冷内热的守护者,绷紧护人", tags=["主角"])
picks = codex.pick("规则 无限流 塔")
ok(len(codex.all_elements()) == 3, "元件入库")
ok(any(p["id"] == "infinite-tower" for p in picks), "取料按相关度命中")

# L1 锻造世界(AIGC:prep 取料 → 宿主生成 → commit 落盘+谱系)
print("[L1] 锻造世界 / 实体 / 线")
wp = forge.world_prep("一座无限攀登的规则之塔", tags=["规则"])
ok(wp["forge"] == "world" and len(wp["codex"]) > 0, "世界生成包带元件食材")
forge.world_commit("infinite-tower", "无限之塔", "# 无限之塔\n\n基调:冷峻规则地狱。\n", genre="无限流", prompt="规则之塔", from_codex=["infinite-tower", "rule-horror"])
w1 = World.load("infinite-tower")
ok(w1.exists() and w1.meta()["provenance"]["source"] == "forge", "世界落盘且带 forge 谱系")

ep = forge.entity_prep(w1, "外冷内热的守护者")
ok(ep["forge"] == "entity" and "world_setting" in ep, "实体生成包带世界设定")
forge.entity_commit(w1, "ye-wudao", "叶无道", "# 叶无道\n\n## 核心事实\n- 绷紧护人\n- 不伤无辜\n", role="main", prompt="守护者")
forge.entity_commit(w1, "lin-wan", "林晚", "# 林晚\n", role="secondary")
ye = LocalEntity.load(w1, "ye-wudao")
ok(ye.grows() and "绷紧护人" in (ye.anchors() or []), "实体落盘+anchors 从核心事实抽出")

forge.thread_commit(w1, "first-climb", "首登", "# 首登\n\n节奏:每层一规则。\n", genre="无限流", prompt="第一次攀登")
t1 = Thread.load(w1, "first-climb")
ok(t1.exists(), "线落盘")

# L3 读透镜(narrate):写作包 → 落章 + 沉淀(cameo 门控) + 核心循环
print("[L3] 读透镜 narrate")
forge.entity_commit(w1, "lu-jia", "路甲", "# 路甲\n", role="cameo")
pkt = lenses.narrate_prep(w1, t1, brief="叶无道破解第一条矛盾规则")
ok(pkt["writing_chapter"] == 1 and len(pkt["craft_checklist"]) > 0, "写作包就绪(章号/craft清单)")
chapter = "塔的第一层只有一条规则,可这条规则自己打自己的脸。叶无道盯着墙上的字。" * 18
rc = lenses.narrate_commit(w1, t1, {
    "chapter_text": chapter, "title": "第一层",
    "sediments": [
        {"entity": "ye-wudao", "text": "识破第一层规则的自相矛盾", "level": "持久"},
        {"entity": "lin-wan", "text": "第一次跟着冒险", "level": "身份"},
        {"entity": "lu-jia", "text": "被吓退", "level": "瞬时"},
    ],
    "state_updates": {"ye-wudao": {"location": "塔·第一层", "mood": "警觉", "goal": "登顶"}},
})
ok(rc["chapter"] == 1 and len(rc["sedimented"]) == 2 and len(rc["skipped"]) == 1, "落章+沉淀,cameo 被门控丢弃")
ok(t1.beats() and t1.beats()[-1]["lens"] == "narrate", "跨透镜事件日志记下 narrate beat")

# 核心循环铁律
print("[核心循环] rebuild ≠ retrieve")
rb = ye.rebuild()
ok(rb["state"]["location"] == "塔·第一层", "状态重建拿到此刻")
ret = ye.retrieve("矛盾规则")
ok(any("矛盾" in e["text"] for e in ret), "记忆检索按相关度命中")

# L3 玩透镜(play):条件成长写回
print("[L3] 玩透镜 play")
pr = lenses.play_commit(w1, t1, {
    "scene": "登塔前夜的对峙", "transcript": "林晚拦住要独自登塔的叶无道……",
    "growth": [{"entity": "lin-wan", "text": "第一次正面违逆他", "trigger": True},
               {"entity": "ye-wudao", "text": "心情波动", "trigger": False}],
})
ok(len(pr["written_back"]) == 1 and len(pr["candidates"]) == 1, "触发成长才写回,余者候选")

# L3 模拟透镜默认关 / 渲染透镜未配休眠
print("[L3] 模拟(默认关)/ 渲染(休眠)")
sp = lenses.simulate_prep(w1, t1)
ok(sp.get("enabled") is False, "自演化默认关(留接口不开)")
rp = lenses.render_prep(w1, "塔下的叶无道", appearance="冷峻青年")
ok("image_prompt" in rp and rp.get("enabled") is False, "渲染透镜未配 key 时休眠但有接口")

# 确定性质检
print("[质检]")
chk = checks.check_chapter(t1, 1)
ok(chk["hanzi"] > 0, f"汉字计数({chk['hanzi']} 字)")

# L4 枢纽:升格 + 第二世界 + 世界互联 + 跨世界召唤化身(强连接)
print("[L4] 枢纽:跨世界穿梭 = 暗宇宙")
asr = nexus.ascend(w1, "ye-wudao")
ne = NexusEntity.load("ye-wudao")
ok(asr["incarnation"] == "infinite-tower" and "infinite-tower" in ne.incarnations(), "升格为跨世界实体+起源化身")

World.create("linjiang", "临江", genre="都市黑道")
edge = nexus.link_worlds("infinite-tower", "linjiang", "塔之裂隙通向临江")
ok(any(l["relation"] == "塔之裂隙通向临江" for l in nexus.links()), "世界互联连边")

sr = nexus.summon("ye-wudao", World.load("linjiang"), entry="换皮进")
ok("linjiang" in NexusEntity.load("ye-wudao").incarnations(), "跨世界召唤:同一实体在临江开化身")
ne.sediment("linjiang", "在临江以新身份醒来,仍绷紧护人", level="身份", where="cross")
rb2 = ne.rebuild("linjiang")
ok("绷紧护人" in ne.anchors() and len(rb2["recent"]) >= 1, "跨世界:灵魂anchors一致,化身记忆独立")
ok((_TMP / "nexus" / "nexus.md").exists(), "枢纽鸟瞰 nexus.md 已渲染")

print(f"\n结果:{len(PASS)} 通过 / {len(FAIL)} 失败")
if FAIL:
    print("失败项:" + "; ".join(FAIL))
    sys.exit(1)
print("✓ 五层地基端到端贯通(海量生成 · 多种体验 · 强连接多元宇宙)。")
