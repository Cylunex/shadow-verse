"""L2 · 世界 —— 一个自洽的现实。承载实体与叙事线;通过枢纽与别的世界互联(强连接多元宇宙)。

world.md(设定) + meta.json(题材/尺度/契约/谱系/世界互联边) + canon/pulse + entities/ + threads/。
"""
from __future__ import annotations

from pathlib import Path

from . import clock, provenance, util
from .config import DEFAULT_CONTRACT, DEFAULT_SCALE, WORLDS_DIR, load_json, save_json

WORLD_TEMPLATE = """# {name}

> 世界 id:`{id}` ｜ 题材:{genre} ｜ 尺度基线:{scale}

## 基调 / 氛围
<!-- 一句话定调 + 三个氛围关键词 -->

## 核心规则(力量 / 社会 / 禁忌,4-6 条,每条带触发关键词)
<!-- 每条:小标题 · 内容 · 触发关键词[...] —— 供按场景注入,不一次性灌全设定 -->

## 核心冲突
<!-- 这个世界的根本张力 -->

## 12 模块设定
<!-- 地理/历史/势力/经济/科技或修炼/信仰/日常/语言/禁忌/秘密/原住实体/世界契约 -->

## 与其它世界的连接(暗宇宙)
<!-- 这个世界如何接入多元宇宙:裂隙/传送/共享历史/同源神话…(由枢纽 links 管理边) -->

## 世界契约(外来实体进出规则)
- 入场:{entry}
- 离场:{exit}
- 带入物:{carry}
"""

CANON_TEMPLATE = "# {name} · 硬事实表(canon)\n\n## 时间锚\n<!-- -->\n\n## 关键数值 / 体系 / 常数\n<!-- -->\n"
PULSE_TEMPLATE = "# {name} · 低频呼吸(pulse,供模拟透镜)\n\n> 不观察不推进;模拟开启时按 tick 惰性结算。\n\n## 当前宏观态\n<!-- 时节 / 势力消长 / 流动传闻 -->\n"


class World:
    def __init__(self, wid: str):
        self.id = wid
        self.dir = WORLDS_DIR / wid

    @property
    def meta_path(self) -> Path:
        return self.dir / "meta.json"

    @property
    def entities_dir(self) -> Path:
        return self.dir / "entities"

    @property
    def threads_dir(self) -> Path:
        return self.dir / "threads"

    def exists(self) -> bool:
        return self.meta_path.exists()

    def meta(self) -> dict:
        return load_json(self.meta_path, {}) or {}

    def save_meta(self, meta: dict) -> None:
        save_json(self.meta_path, meta)

    @classmethod
    def create(
        cls, wid: str, name: str, *, genre: str = "", scale: str = DEFAULT_SCALE,
        contract: dict | None = None, prov: dict | None = None, body: str | None = None,
    ) -> "World":
        if not util.is_id(wid):
            raise ValueError(f"世界 id 必须 kebab-case:{wid!r}")
        w = cls(wid)
        if w.exists():
            raise FileExistsError(f"世界已存在:{wid}")
        contract = contract or dict(DEFAULT_CONTRACT)
        w.save_meta({
            "id": wid, "name": name, "genre": genre, "scale": scale,
            "contract": contract, "links": [],
            "provenance": prov or provenance.stamp("manual"),
            "created": clock.now_iso(),
        })
        if body:   # 锻造器生成的世界正文直接落
            util.write_md(w.dir / "world.md", body)
        else:
            util.write_md(w.dir / "world.md", WORLD_TEMPLATE.format(
                id=wid, name=name, genre=genre or "未定", scale=scale,
                entry=" / ".join(contract["entry"]), exit=" / ".join(contract["exit"]), carry=contract["carry"]))
        util.write_md(w.dir / "canon.md", CANON_TEMPLATE.format(name=name))
        util.write_md(w.dir / "pulse.md", PULSE_TEMPLATE.format(name=name))
        return w

    @classmethod
    def load(cls, wid: str) -> "World":
        w = cls(wid)
        if not w.exists():
            raise FileNotFoundError(f"世界不存在:{wid}")
        return w

    @classmethod
    def list_all(cls) -> list[str]:
        if not WORLDS_DIR.exists():
            return []
        return sorted(p.name for p in WORLDS_DIR.iterdir() if (p / "meta.json").exists())

    def list_entities(self) -> list[str]:
        d = self.entities_dir
        return sorted(p.name for p in d.iterdir() if p.is_dir()) if d.exists() else []

    def list_threads(self) -> list[str]:
        d = self.threads_dir
        return sorted(p.name for p in d.iterdir() if (p / "meta.json").exists()) if d.exists() else []

    def delete(self) -> None:
        """删世界目录(枢纽残留另由 nexus.purge_world 清,API 层先调它)。"""
        import shutil
        if self.dir.exists():
            shutil.rmtree(self.dir)
