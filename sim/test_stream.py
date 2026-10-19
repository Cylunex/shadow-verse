"""流式对话 + 预设接入系统提示 + 正则套用输出 —— 三件新功能的回归测试(不打网络,假 LLM)。"""
from __future__ import annotations

import os
import sys
import tempfile

os.environ["SV_UNIVERSE_DIR"] = tempfile.mkdtemp(prefix="sv_t_stream_")
os.environ["SV_LOCAL_CONF"] = tempfile.mktemp(suffix=".conf")
for k in ("SV_PROVIDER", "SV_PRESET"):
    os.environ.pop(k, None)

from sv import clock  # noqa: E402

clock.use_virtual()

from sv import chat, config, importer, llm  # noqa: E402
from sv.entity import LocalEntity  # noqa: E402
from sv.world import World  # noqa: E402

P, F = [], []
def ok(c, m): (P if c else F).append(m); print(("  ✓ " if c else "  ✗ ") + m)

w = World.create("w", "W", genre="都市")
e = LocalEntity.create(w, "su", "苏晴", role="main", body="# 苏晴\n## 核心事实\n- 外冷内热")

# ---------- 1) 预设接入系统提示 ----------
sys_off = chat._system(w, e, chat.player(), {})
ok("PRESET-AUTHOR-MARK" not in sys_off, "未启用预设:无作者模块")

preset = {"prompts": [{"identifier": "main", "name": "m", "role": "system", "content": "PRESET-AUTHOR-MARK 冷面叙事。"},
                      {"identifier": "charDescription", "marker": True, "content": ""}],
          "prompt_order": [{"order": [{"identifier": "main", "enabled": True},
                                      {"identifier": "charDescription", "enabled": True}]}]}
pid = importer.import_preset(preset, name="ztest")["preset"]
config.save_setting({"SV_PRESET": pid})
sys_on = chat._system(w, e, chat.player(), {})
ok("PRESET-AUTHOR-MARK" in sys_on, "启用预设:作者模块前置注入")
ok("苏晴" in sys_on and "第一人称" in sys_on, "启用预设:引擎核心(人设/铁律)仍在,正确性不丢")
config.save_setting({"SV_PRESET": ""})   # 关掉,免影响后续
ok("PRESET-AUTHOR-MARK" not in chat._system(w, e, chat.player(), {}), "停用预设:作者模块消失")

# 删/损坏的预设 → 静默退回原生(不报错)
config.save_setting({"SV_PRESET": "nonexistent-xyz"})
ok(chat._active_preset() is None and "苏晴" in chat._system(w, e, chat.player(), {}), "预设不存在:静默退回原生")
config.save_setting({"SV_PRESET": ""})

# ---------- 2) 流式分隔器:正文吐出、变量块挡住 ----------
sp = chat._StreamSplitter(chat.VAR_SEP)
emitted = "".join(sp.feed(x) for x in ["啧,", "走开", "。\n" + chat.VAR_SEP + '\n{"好', '感度":"+5"}'])
emitted += sp.flush()
ok(emitted == "啧,走开。\n", "分隔器:只吐正文,变量块挡在外面")

sp2 = chat._StreamSplitter(chat.VAR_SEP)   # 无变量块:全吐
out2 = "".join(sp2.feed(x) for x in ["你好", ",在的"]) + sp2.flush()
ok(out2 == "你好,在的", "分隔器:无变量块时正文全吐")

# ---------- 3) stream_turn:逐块 + 收尾落盘 + 变量结算 ----------
_av, _stream = llm.available, llm.stream
llm.available = lambda: True
def _fake_stream(system, user, **kw):
    for piece in ["啧,", "又来了。", "\n" + chat.VAR_SEP + '\n{"好感度":"+5","金钱":"100"}']:
        yield piece
llm.stream = _fake_stream
try:
    chat.clear(e)
    deltas, done = [], None
    for kind, payload in chat.stream_turn(w, e, "我来看你了"):
        (deltas.append(payload) if kind == "delta" else None)
        if kind == "done":
            done = payload
    full = "".join(deltas)
    # 流式正文可能带变量块前的尾部换行(收尾 done.reply 已 strip 干净,前端按 done 重绘)
    ok(full.strip() == "啧,又来了。" and chat.VAR_SEP not in full, "流式增量:正文逐块、不含变量块")
    ok(done and done["reply"] == "啧,又来了。", "done 携带整段正文")
    ok(done["vars"]["好感度"] == 5 and done["vars"]["金钱"] == 100, "done 变量结算(增量+新值)")
    ok(set(done["var_changed"]) == {"好感度", "金钱"}, "done 报告改了哪些变量")
    h = chat.history(e)
    ok(len(h) == 2 and h[0]["text"] == "我来看你了" and h[1]["text"] == "啧,又来了。", "流式收尾落盘 user+char")
finally:
    llm.available, llm.stream = _av, _stream

# 未配 LLM:stream_turn 直接给引导(不落盘)
chat.clear(e)
gen = list(chat.stream_turn(w, e, "在吗"))
ok(len(gen) == 1 and gen[0][0] == "done" and gen[0][1]["available"] is False, "未配 LLM:流式给引导")
ok(chat.history(e) == [], "未配 LLM:不落历史")

# ---------- 4) 正则套用输出(webapp 边界,scope=output)----------
import sv.webapp as webapp  # noqa: E402
importer.import_regex({"scriptName": "hl", "findRegex": "/啧/g", "replaceString": "【哼】"}, name="ztestrx")
ok(webapp._regex_render("啧,走开") == "【哼】,走开", "正则渲染:输出文本被改写")
ok(webapp._regex_out({"reply": "啧!"})["reply"] == "【哼】!", "_regex_out:reply 字段套正则")
ok(webapp._regex_out({"note": "x"}) == {"note": "x"}, "_regex_out:无 reply 时原样返回")

# ---------- 5) 预设采样参数流向 LLM + sampler 分流 ----------
samp = {"temperature": 0.6, "top_p": 0.9, "top_k": 40, "max_tokens": 800, "repetition_penalty": 1.1}
ok(llm._samplers(samp, llm._OPENAI_SAMPLERS) == {"temperature": 0.6, "top_p": 0.9, "max_tokens": 800},
   "openai sampler:挑标准键、丢 top_k/repetition_penalty")
ok(llm._samplers(samp, llm._OLLAMA_SAMPLERS, llm._OLLAMA_REMAP) ==
   {"temperature": 0.6, "top_p": 0.9, "top_k": 40, "repeat_penalty": 1.1}, "ollama sampler:含 top_k + 改名 repeat_penalty")

presamp = {"prompts": [{"identifier": "main", "name": "m", "role": "system", "content": "x"}],
           "prompt_order": [{"order": [{"identifier": "main", "enabled": True}]}], "temperature": 0.33, "top_p": 0.8}
pid2 = importer.import_preset(presamp, name="zsamp")["preset"]
config.save_setting({"SV_PRESET": pid2})
ok(chat._gen_params() == {"temperature": 0.33, "top_p": 0.8}, "启用预设:_gen_params 取出采样参数")
captured = {}
_g = llm.generate
llm.generate = lambda s, u, **kw: (captured.update(kw), "回")[1]
try:
    chat._av_old = llm.available
    llm.available = lambda: True
    chat.clear(e)
    chat.turn(w, e, "嗨")
    ok(captured.get("params") == {"temperature": 0.33, "top_p": 0.8}, "turn 把预设采样参数透传给 llm.generate")
finally:
    llm.generate = _g
    llm.available = chat._av_old
config.save_setting({"SV_PRESET": ""})
ok(chat._gen_params() is None, "停用预设:_gen_params 为 None")

# ---------- 6) 作者笔记注入 + 快速回复持久化 ----------
ok("作者笔记" not in chat._system(w, e, chat.player(), {}), "默认无作者笔记")
chat.set_author_note(e, "保持悬疑基调,别急着解谜")
sysn = chat._system(w, e, chat.player(), {})
ok("作者笔记" in sysn and "悬疑基调" in sysn, "作者笔记注入系统提示")
chat.set_author_note(e, "")
ok("作者笔记" not in chat._system(w, e, chat.player(), {}), "清空作者笔记后不再注入")

chat.set_quick_replies([{"label": "打招呼", "message": "嗨,在吗"}, {"message": "继续"}, {"message": ""}])
qr = chat.quick_replies()
ok(len(qr) == 2 and qr[0]["label"] == "打招呼" and qr[1]["label"] == "继续", "快速回复:存取 + 空项剔除 + 缺 label 用 message")

# ---------- 7) 楼层编辑 / 删除 ----------
from sv.config import append_jsonl  # noqa: E402
from sv import memory  # noqa: E402

chat.clear(e)
append_jsonl(e.dir / "chat.jsonl", {"role": "user", "text": "甲", "ts": clock.now_iso()})
append_jsonl(e.dir / "chat.jsonl", {"role": "char", "text": "乙", "ts": clock.now_iso()})
chat.edit_floor(e, 0, "甲改")
ok(chat.history(e)[0]["text"] == "甲改", "edit_floor 改 user 楼")
chat.edit_floor(e, 1, "乙改")
h = chat.history(e)
ok(h[1]["text"] == "乙改" and h[1]["swipes"][h[1]["swipe_id"]] == "乙改", "edit_floor 改 char 楼并同步当前候选")
ok(chat.edit_floor(e, 9, "x")["ok"] is False, "edit_floor 越界拒绝")
r = chat.delete_floor(e, 0)
ok(r["ok"] and r["remaining"] == 1 and chat.history(e)[0]["text"] == "乙改", "delete_floor 删指定楼")

# ---------- 8) 自动总结:滚出窗口才触发,标记单调推进 ----------
chat.clear(e)
ok(chat._summary_upto(e) == 0, "新对话总结标记=0")
_av3, _gen3 = llm.available, llm.generate
llm.available = lambda: True
llm.generate = lambda s, u, **kw: "他们达成了某种默契。"
try:
    for i in range(chat.HISTORY_WINDOW + config.SUMMARY_EVERY + 2):   # 撑过窗口 + 阈值
        append_jsonl(e.dir / "chat.jsonl", {"role": "char" if i % 2 else "user", "text": f"句{i}", "ts": clock.now_iso()})
    import time as _t
    before = chat._summary_upto(e)
    expected_cut = len(chat.history(e)) - chat.HISTORY_WINDOW
    chat._kick_summary(w, e)
    # 标记现在在 worker 成功后才推进(治 LLM 挂掉时永久丢段);等后台线程跑完再校验
    for _ in range(20):
        if chat._summary_upto(e) >= expected_cut:
            break
        _t.sleep(0.1)
    after = chat._summary_upto(e)
    ok(before == 0 and after == expected_cut, "总结成功后标记推进到 cut(由后台 worker 落)")
    chat._kick_summary(w, e)
    _t.sleep(0.2)
    ok(chat._summary_upto(e) == after, "无新内容时不重复推进标记")
    ok(any(x.get("trace") == "auto-summary" for x in memory.all_experiences(e.dir)), "后台总结落一条记忆")
    # 关键回归:llm 模式下总结挂了不能永久丢这段;标记应留在上次成功位置
    # (on 模式会回退抽取式并推进——那是有意的 stub 友好路径,另测)
    failbox = {"n": 0}
    def _fail(*a, **k):
        failbox["n"] += 1; raise RuntimeError("primary down")
    _save_gen = llm.generate; llm.generate = _fail
    _save_mode = getattr(config, "CHAT_SUMMARY", "on")
    config.CHAT_SUMMARY = "llm"
    try:
        append_jsonl(e.dir / "chat.jsonl", {"role": "user", "text": "新句X", "ts": clock.now_iso()})
        append_jsonl(e.dir / "chat.jsonl", {"role": "char", "text": "回X", "ts": clock.now_iso()})
        for _ in range(config.SUMMARY_EVERY):
            append_jsonl(e.dir / "chat.jsonl", {"role": "user", "text": "句Y", "ts": clock.now_iso()})
            append_jsonl(e.dir / "chat.jsonl", {"role": "char", "text": "回Y", "ts": clock.now_iso()})
        chat._kick_summary(w, e)
        for _ in range(20):
            if failbox["n"] > 0: break
            _t.sleep(0.1)
        _t.sleep(0.2)
        ok(chat._summary_upto(e) == after, "llm 模式:LLM 失败时标记不前移(下轮可重试)")
    finally:
        llm.generate = _save_gen
        config.CHAT_SUMMARY = _save_mode
    # 共享 chat_meta.json 不能被总结写抹掉 greeting_id(consistency-1)
    chat.set_greeting(e, 0)
    chat._set_summary_upto(e, 999)
    ok(chat.greeting_id(e) == 0 and chat._summary_upto(e) == 999, "_set_summary_upto 是 read-merge,不抹 greeting_id")
finally:
    llm.available, llm.generate = _av3, _gen3

# ---------- 8b) stub/抽取式:无 LLM 也能落记忆(不破坏 stub 流程)----------
chat.clear(e)
_save_mode2 = getattr(config, "CHAT_SUMMARY", "on")
config.CHAT_SUMMARY = "on"          # on + available=False → extract 同步路径
llm.available = lambda: False
try:
    for i in range(chat.HISTORY_WINDOW + config.SUMMARY_EVERY + 2):
        append_jsonl(e.dir / "chat.jsonl",
                     {"role": "char" if i % 2 else "user", "text": f"情节点{i}", "ts": clock.now_iso()})
    expected_cut = len(chat.history(e)) - chat.HISTORY_WINDOW
    chat._kick_summary(w, e)        # 同步抽取,无需 sleep
    ok(chat._summary_upto(e) == expected_cut, "stub/on:抽取式同步推进标记")
    exps = memory.all_experiences(e.dir)
    ok(any(str(x.get("trace", "")).startswith("auto-summary") for x in exps), "stub/on:落 auto-summary 记忆")
    ok(any("对话印象" in str(x.get("text", "")) for x in exps), "stub/on:抽取式带对话印象前缀")
    # off 门控
    config.CHAT_SUMMARY = "off"
    before = chat._summary_upto(e)
    for _ in range(config.SUMMARY_EVERY + 2):
        append_jsonl(e.dir / "chat.jsonl", {"role": "user", "text": "x", "ts": clock.now_iso()})
        append_jsonl(e.dir / "chat.jsonl", {"role": "char", "text": "y", "ts": clock.now_iso()})
    chat._kick_summary(w, e)
    ok(chat._summary_upto(e) == before, "CHAT_SUMMARY=off:不触发")
finally:
    config.CHAT_SUMMARY = _save_mode2
    llm.available = _av3

chat.clear(e)
ok(chat._summary_upto(e) == 0, "clear 后总结标记复位")

# ---------- 9) 多 provider 容错链 ----------
from sv.config import save_json  # noqa: E402

config.save_setting({"SV_PROVIDER": "openai", "SV_FALLBACK_PROVIDER": "anthropic"})
ok(llm._chain() == [("openai", ""), ("anthropic", "")], "_chain:主 provider + 备援")
_o, _a = llm._openai, llm._anthropic
def _boom(*a, **k):
    raise RuntimeError("primary down")
llm._openai, llm._anthropic = _boom, (lambda *a, **k: "备援回复")
try:
    ok(llm.generate("s", "u") == "备援回复", "generate:主 provider 挂 → 自动切备援")
finally:
    llm._openai, llm._anthropic = _o, _a
config.save_setting({"SV_PROVIDER": "", "SV_FALLBACK_PROVIDER": ""})
ok(len(llm._chain()) == 1, "没配备援:链长 1")

# ---------- 10) 开场白进上下文 + 多开场白选择 ----------
e3 = LocalEntity.create(w, "gz", "管子", role="main")
c3 = e3.card(); c3["greetings"] = ["开场A", "开场B"]; save_json(e3.card_path, c3)
ok(chat.greetings(e3) == ["开场A", "开场B"], "greetings 读多开场白")
ok(chat.greeting(e3) == "开场A", "默认选第 0 个开场白")
chat.set_greeting(e3, 1)
ok(chat.greeting(e3) == "开场B", "set_greeting 切到第 1 个")
_av4, _g4 = llm.available, llm.generate
llm.available = lambda: True; llm.generate = lambda s, u, **k: "答"
try:
    chat.clear(e3); chat.set_greeting(e3, 1)
    chat.turn(w, e3, "你好")
    h3 = chat.history(e3)
    ok(len(h3) == 3 and h3[0]["role"] == "char" and h3[0]["text"] == "开场B", "首轮:选中的开场白落为首楼(进上下文)")
    ok(h3[1]["role"] == "user" and h3[2]["role"] == "char", "开场白之后才是 user + char")
    e4 = LocalEntity.create(w, "nob", "无开场", role="main")
    chat.turn(w, e4, "喂")
    ok(len(chat.history(e4)) == 2, "无开场白角色:不插首楼")
finally:
    llm.available, llm.generate = _av4, _g4

# ---------- 11) 回归:stream_turn 中途出错时仍把已出文本落盘 ----------
e5 = LocalEntity.create(w, "regr", "回归角", role="main")
chat.clear(e5)
def _stream_then_die(s, u, **k):
    yield "已经"
    yield "说了几个字"
    raise RuntimeError("upstream proxy closed")
_save_av, _save_stream = llm.available, llm.stream
llm.available = lambda: True; llm.stream = _stream_then_die
try:
    deltas = []
    try:
        for kind, payload in chat.stream_turn(w, e5, "你好"):
            if kind == "delta": deltas.append(payload)
    except Exception: pass
    h5 = chat.history(e5)
    ok(any(r.get("role") == "user" and r.get("text") == "你好" for r in h5),
       "stream 出错:user 句子已经落盘(不会蒸发)")
    ok(any(r.get("role") == "char" and "已经" in (r.get("text") or "") and "说了几个字" in r.get("text") for r in h5),
       "stream 出错:已收到的字也落盘成 char 楼,刷新可见")
finally:
    llm.available, llm.stream = _save_av, _save_stream

# ---------- 12) 回归:delete_floor 后 vars 同步重算,不残留被删 char 楼的增量 ----------
chat.clear(e); chat.set_var(e, "好感度", 0)
append_jsonl(e.dir / "chat.jsonl", {"role": "user", "text": "你看我", "ts": clock.now_iso()})
baseline_before = {"好感度": 0}
char_row = chat._new_char_row("看你了。", {"好感度": "+5"}, baseline_before)
append_jsonl(e.dir / "chat.jsonl", char_row)
chat._apply_baseline(e, baseline_before, {"好感度": "+5"})
ok(chat.vars(e).get("好感度") == 5, "前置:char 楼把好感度推到 5")
# 删那条 char 楼:好感度应回到 0(否则永久卡在 5)
chat.delete_floor(e, 1)
ok(chat.vars(e).get("好感度", 0) == 0, "delete_floor 后变量回滚:被删 char 楼的 +5 不再残留")

# ---------- 13) 回归:floor_regenerate user 楼时,基线扫被丢弃段里第一条 char 楼 ----------
chat.clear(e); chat.set_var(e, "好感度", 0)
# 模拟:user→char(+10)→char_orphan(+3) 这种被 delete_floor 后罕见但可达的形态
append_jsonl(e.dir / "chat.jsonl", {"role": "user", "text": "想问你", "ts": clock.now_iso()})
append_jsonl(e.dir / "chat.jsonl", chat._new_char_row("第一回答。", {"好感度": "+10"}, {"好感度": 0}))
append_jsonl(e.dir / "chat.jsonl", chat._new_char_row("第二回答(无对应user)。", {"好感度": "+3"}, {"好感度": 10}))
chat._apply_baseline(e, {"好感度": 10}, {"好感度": "+3"})    # vars 现在 = 13
# 让 idx+1 不是 char 楼:此处它就是 char,先 delete idx+1 让它变成 char_orphan 紧跟 user 后续
# 简化场景:直接 regen idx=0 的 user;baseline 应扫到第一条 char 的 vars_before = {好感度:0},非当前 13
_av5, _g5 = llm.available, llm.generate
llm.available = lambda: True; llm.generate = lambda s, u, **k: "新答\n===变量===\n{\"好感度\":\"+1\"}"
try:
    r = chat.floor_regenerate(w, e, 0)
    ok(r.get("vars", {}).get("好感度") == 1,
       "floor_regenerate user 楼:基线扫到首个被丢弃 char 楼的 vars_before(0),新增 +1 应得 1,不是 14")
finally:
    llm.available, llm.generate = _av5, _g5

# ---------- 14) 自动总结 toast 信号:同步 done + status poll/consume ----------
chat.clear(e)
_save_mode3 = getattr(config, "CHAT_SUMMARY", "on")
config.CHAT_SUMMARY = "extract"     # 强制同步抽取,可断言回执字段
llm.available = lambda: False
try:
    for i in range(chat.HISTORY_WINDOW + config.SUMMARY_EVERY + 2):
        append_jsonl(e.dir / "chat.jsonl",
                     {"role": "char" if i % 2 else "user", "text": f"印象{i}", "ts": clock.now_iso()})
    kick = chat._kick_summary(w, e)
    ok(kick.get("done") is True and kick.get("preview"), "extract kick:同步返回 done+preview")
    out = {}
    chat._attach_summary(out, kick)
    ok(out.get("summary_done") is True and out.get("summary_preview"),
       "_attach_summary:挂 summary_done/preview 供前端 toast")
    st = chat.summary_status(e, consume=False)
    ok(st.get("done") is True and st.get("preview"), "summary_status:ready 可见(未消费)")
    st2 = chat.summary_status(e, consume=True)
    ok(st2.get("done") is True and chat.summary_status(e, consume=True).get("done") is False,
       "summary_status consume:取走 ready,再 poll 为空(toast 一次)")
    # pending 路径:llm + available 时 kick 标 pending(不跑真 LLM:立刻不可用回退已测)
    config.CHAT_SUMMARY = "llm"
    llm.available = lambda: True
    # 清 meta pending/ready,再塞够窗口的新段
    chat.clear(e)
    for i in range(chat.HISTORY_WINDOW + config.SUMMARY_EVERY + 2):
        append_jsonl(e.dir / "chat.jsonl",
                     {"role": "char" if i % 2 else "user", "text": f"异步{i}", "ts": clock.now_iso()})
    # stub generate 极快:仍走后台线程 → 先看到 pending
    llm.generate = lambda s, u, **kw: "他们又聊了一会儿。"
    kick2 = chat._kick_summary(w, e)
    ok(kick2.get("pending") is True, "llm kick:立刻返回 pending(后台线程)")
    out2 = {}
    chat._attach_summary(out2, kick2)
    ok(out2.get("summary_pending") is True and not out2.get("summary_done"),
       "_attach_summary:pending 挂 summary_pending")
    import time as _t2
    ready = None
    for _ in range(30):
        ready = chat.pop_summary_ready(e)
        if ready: break
        _t2.sleep(0.1)
    ok(bool(ready and ready.get("preview")), "异步完成后 pop_summary_ready 可取到 preview")
finally:
    config.CHAT_SUMMARY = _save_mode3
    llm.available = _av3
    # generate 可能被上面改过;恢复到节 8 捕获的 _gen3(若不存在则 noop)
    try:
        llm.generate = _gen3
    except NameError:
        pass

chat.clear(e)

if os.path.exists(os.environ["SV_LOCAL_CONF"]):
    os.remove(os.environ["SV_LOCAL_CONF"])

print(f"\n{len(P)} 通过 / {len(F)} 失败")
sys.exit(1 if F else 0)
