"""配置热加载测试 —— save_setting → reload 即时生效、密钥脱敏、清除回退。"""
from __future__ import annotations

import os
import sys
import tempfile

# 把本机配置文件指到临时,不污染真实 sv.local.conf
os.environ["SV_LOCAL_CONF"] = tempfile.mktemp(prefix="sv_local_", suffix=".conf")
# 确保没有环境变量抢占被测键
for k in ("SV_PROVIDER", "OPENAI_API_KEY", "SV_RENDER", "GITEE_API_KEY"):
    os.environ.pop(k, None)

from sv import config, llm  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

# 初始(sv.conf 打底 = stub)
ok(config.PROVIDER == "stub" and llm.available() is False, "初始 provider=stub,LLM 未启用")

# 保存 provider → 热加载即时生效
config.save_setting({"SV_PROVIDER": "openai", "SV_MODEL": "gpt-4o-mini"})
ok(config.PROVIDER == "openai" and config.MODEL == "gpt-4o-mini", "save_setting 后 provider/model 即时生效")
ok(llm.available() is True, "llm.available() 随之翻转(无需重启)")

# 密钥脱敏:snapshot 不漏全 key
config.save_setting({"OPENAI_API_KEY": "sk-secret-1234567890"})
snap = config.settings_snapshot()
ok(snap["secrets"]["OPENAI_API_KEY"]["set"] is True, "snapshot 报告密钥已设")
ok("1234567890" not in str(snap) and "sk-secret" not in str(snap), "snapshot 不泄露完整密钥")
ok(config.OPENAI_API_KEY == "sk-secret-1234567890", "引擎内部仍能拿到真实密钥")

# 只接受 MANAGED_KEYS
config.save_setting({"NOT_A_KEY": "x"})
ok("NOT_A_KEY" not in config._CONF, "非托管键被忽略")

# 清除(空字符串)→ 回退到 sv.conf 打底
config.save_setting({"SV_PROVIDER": ""})
ok(config.PROVIDER == "stub", "清除 SV_PROVIDER 后回退到 stub")

# 渲染开关热加载
config.save_setting({"SV_RENDER": "gitee", "GITEE_API_KEY": "g-key-abcdef"})
import sv.lenses as L  # noqa: E402
ok(L.render_available() is True, "render 配 key 后 render_available 翻转(lenses 走 config.X)")
config.save_setting({"SV_RENDER": "", "GITEE_API_KEY": ""})
ok(L.render_available() is False, "清除后 render 回到休眠")

# 收尾删临时文件
try:
    os.remove(os.environ["SV_LOCAL_CONF"])
except OSError:
    pass

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
