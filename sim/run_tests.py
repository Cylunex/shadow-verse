"""测试总跑 —— 各测试独立子进程跑(各自临时 universe),汇总结果。

跑:PYTHONUTF8=1 python -m sim.run_tests
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TESTS = ["sim.test_memory", "sim.test_forge", "sim.test_lenses", "sim.test_nexus",
         "sim.test_llm", "sim.test_narrate", "sim.test_codex", "sim.test_manage",
         "sim.test_render", "sim.test_config", "sim.smoke"]
ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    env = {"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    import os
    e = {**os.environ, **env}
    results = []
    for t in TESTS:
        print(f"\n{'='*48}\n▶ {t}\n{'='*48}")
        r = subprocess.run([sys.executable, "-m", t], cwd=str(ROOT), env=e)
        results.append((t, r.returncode == 0))
    print(f"\n{'='*48}\n汇总")
    for t, good in results:
        print(f"  {'✓' if good else '✗'} {t}")
    failed = [t for t, g in results if not g]
    print(f"\n{len(results) - len(failed)}/{len(results)} 套通过" + (f",失败:{failed}" if failed else " — 全绿"))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
