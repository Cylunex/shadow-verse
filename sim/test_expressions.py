"""立绘表情切换测试 —— 情绪分类解析 / emotion_clause / sd_prompt→appearance / render 门控 / seed 入参。"""
from __future__ import annotations

import json
import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_expr_")
os.environ["SV_LOCAL_CONF"] = tempfile.mktemp(suffix=".conf")   # 隔离本机已配的 provider
os.environ.pop("SV_PROVIDER", None)

from sv import clock  # noqa: E402

clock.use_virtual()

import sv.expressions as X  # noqa: E402
from sv import importer, lenses  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# 标签集 + 子句
ok(len(X.EMOTIONS_CORE) == 8 and "neutral" in X.EMOTIONS_CORE, "核心 8 情绪")
ok("smile" in X.emotion_clause("joy") and X.emotion_clause("未知") == X.EMOTION_PROMPT["neutral"], "情绪子句 + 未知回退 neutral")

# 分类解析三级回退(无 LLM → fallback)
ok(X.classify_emotion("他笑了", X.EMOTIONS_CORE) == "neutral", "无 LLM → fallback neutral")
# 假 LLM:返回带围栏脏 JSON
_av, _gen = X.llm.available, X.llm.generate
X.llm.available = lambda: True
try:
    X.llm.generate = lambda s, u, **k: '```json\n{"emotion":"anger"}\n```'
    ok(X.classify_emotion("你给我滚!", X.EMOTIONS_CORE) == "anger", "脏 JSON 分类(jsonloose 解析)")
    X.llm.generate = lambda s, u, **k: '我觉得是 joy 吧'   # 非 JSON → 子串回退
    ok(X.classify_emotion("哈哈哈", X.EMOTIONS_CORE) == "joy", "非 JSON → 子串包含回退")
    X.llm.generate = lambda s, u, **k: 'xyz 无关'           # 都不中 → fallback
    ok(X.classify_emotion("...", ["joy", "anger"]) == "joy", "全不中 → labels[0]")
    # 只在给定 labels 里选(模型给了不在集里的)
    X.llm.generate = lambda s, u, **k: '{"emotion":"love"}'
    ok(X.classify_emotion("...", ["joy", "anger"]) == "joy", "label 限定:不在集→回退")
finally:
    X.llm.available, X.llm.generate = _av, _gen

# sd_character_prompt.positive → appearance(导入)
v2 = {"spec": "chara_card_v2", "data": {
    "name": "凛", "description": "剑客", "first_mes": "嗯。",
    "extensions": {"sd_character_prompt": {"positive": "silver hair, red eyes, black coat"},
                   "depth_prompt": {"prompt": "始终冷淡", "depth": 4, "role": "system"},
                   "talkativeness": 0.7}}}
c = importer.parse_card(json.dumps(v2, ensure_ascii=False))
ok(c["appearance"] == "silver hair, red eyes, black coat", "解析 sd_character_prompt→appearance")
ok(c["depth_prompt"]["prompt"] == "始终冷淡" and c["talkativeness"] == 0.7, "解析 depth_prompt + talkativeness")
w = World.create("w", "W", genre="玄幻")
r = importer.import_card(w, c, role="main")
e = LocalEntity.load(w, r["entity"])
ok(e.appearance == "silver hair, red eyes, black coat", "导入后 appearance 落到 card(锁脸素材)")
ok(e.card()["depth_prompt"]["depth"] == 4 and e.card()["talkativeness"] == 0.7, "depth_prompt/talkativeness 落 card")

# render 门控:未配 render 后端 → enabled False,不崩
res = lenses.render_expressions(w, e)
ok(res.get("enabled") is False, "未配 render 后端:表情预生成休眠不崩")

# 已生成表情列举(手造两张假图)
pdir = e.dir / "portraits"; pdir.mkdir(parents=True, exist_ok=True)
(pdir / "joy.png").write_bytes(b"x"); (pdir / "anger.png").write_bytes(b"x")
sp = lenses.expression_sprites(w, e)
ok(set(sp) == {"joy", "anger"}, "列举已生成表情立绘")
cr = lenses.classify_reply_emotion(w, e, "随便")
ok(cr["emotion"] in ("joy", "anger") and cr["sprite"], "分类只在已生成表情里选(无LLM→labels[0]=anger)")

# _gen_image 带 seed 入参(签名校验,不真出图)
import inspect  # noqa: E402
ok("seed" in inspect.signature(lenses._gen_image).parameters, "_gen_image 支持 seed 入参(锁脸)")

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
