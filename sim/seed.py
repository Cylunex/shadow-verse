"""演示种子 —— 以宿主 Agent(Model A)身份,用引擎真造一个多元宇宙片段。

造:元件库 → 锻造两个世界/角色/线 → 写两章真正文 + 沉淀 → 玩一场 → 升格+互联+跨世界召唤化身。
跑:PYTHONUTF8=1 python -m sim.seed   (写进默认 universe/,会先清空 demo 数据)
"""
from __future__ import annotations

import shutil

from sv import codex, forge, lenses, nexus
from sv.config import CODEX_DIR, NEXUS_DIR, WORLDS_DIR
from sv.entity import LocalEntity
from sv.world import World


def _fresh():
    for d in (CODEX_DIR, WORLDS_DIR, NEXUS_DIR):
        if d.exists():
            shutil.rmtree(d)


def run():
    _fresh()
    print("· 清空旧 demo,开始播种…")

    # ---------- L0 元件库 ----------
    codex.add("worlds", "infinite-tower", "无限攀登的高塔,每层一个自洽规则世界,登顶者可改写一条现实", tags=["无限流", "规则", "高概念"])
    codex.add("worlds", "neon-jianghu", "霓虹都市表皮下的旧式江湖,刀与义气活在数据废墟里", tags=["都市", "黑道", "赛博"])
    codex.add("mechanics", "rule-horror", "规则怪谈:照做活、违则死;规则自相矛盾处即是生路,也是钩子", tags=["规则", "悬疑"])
    codex.add("mechanics", "qi-debt", "气债:借力越界要还,透支者被反噬,克制是强者的礼仪", tags=["力量", "守恒"])
    codex.add("characters", "cold-protector", "外冷内热的守护者,话少手狠,把所有人挡在身后却说不在乎", tags=["主角", "弧光"])
    codex.add("conflicts", "betrayal-within", "最深的刀来自队伍内部;信任本身成为赌注", tags=["背叛", "悬疑"])
    codex.add("themes", "protect-what-remains", "在不断失去的世界里,守住还剩下的那一点", tags=["母题"])
    sr = codex.seed_starter()   # 灌入起始元件库(亲手提炼的抽象元件)
    print(f"  元件 {len(codex.all_elements())} 个(demo 7 + 起始库新增 {sr['added']})")

    # ---------- 世界一:无限之塔 ----------
    w1 = forge.world_commit(
        "infinite-tower", "无限之塔", genre="无限流", prompt="一座无限攀登的规则之塔",
        from_codex=["infinite-tower", "rule-horror"],
        body="""# 无限之塔

> 世界 id:`infinite-tower` ｜ 题材:无限流 ｜ 尺度基线:max

## 基调 / 氛围
冷峻、压迫、解谜。每一层都像一间会杀人的密室。关键词:规则、悖论、攀登。

## 核心规则
- **登塔律**(触发:进入/登顶):每层张贴若干规则,照做者存,违者亡。登顶可改写现实一条。
- **悖论生路**(触发:矛盾/卡关):当规则自相矛盾,矛盾的夹缝就是唯一活路——也是这一层真正的题。
- **不可回头**(触发:撤退):门只向上开,退意即死。
- **代价律**(触发:作弊/越界):每用一次塔外之力,塔要回收同等的"你在乎的东西"。

## 核心冲突
人要登顶改写现实,塔要人付出在乎之物。越往上,越分不清救人和利用人。

## 时间设定
塔内无昼夜,以"层"计时。塔外世界停在登塔者离开的那一刻。

## 与其它世界的连接(暗宇宙)
塔的某些层会裂开,通向真实世界的角落——「临江」就是从第七层的裂隙里漏出来的一座城。

## 世界契约(外来实体进出规则)
- 入场:本体进 / 换皮进(成为某层的"住户")
- 离场:带走所得
- 带入物:保留随身物
""")
    World_w1 = World.load("infinite-tower")
    print(f"  世界:{w1['name']}")

    forge.entity_commit(World_w1, "su-zhi", "苏栀", role="main", from_codex=["cold-protector"], body="""# 苏栀

> 实体 id:`su-zhi` ｜ 戏份:main

## 身份
二十六岁,曾是临江最年轻的话事人,被人从背后捅进了塔。眉骨有道旧疤,笑起来反而吓人。

## Identity Core
- 把人挡在身后,是她唯一不肯改的毛病。
- 不伤无辜——哪怕规则逼她。
- 信过的人背叛过她,所以她再不肯先开口信谁。

## 声音指纹
话短,常以"啧"开头。说狠话时反而轻。从不解释自己为什么救人。

## 核心欲望与底线
想登顶改写那一夜——但她嘴上只说"先活过这一层"。底线:绝不拿同伴当代价。

## 核心事实
- 绷紧护人
- 不伤无辜
- 被最信的人从背后捅过
""")
    forge.entity_commit(World_w1, "lin-wan", "林晚", role="secondary", body="""# 林晚

> 实体 id:`lin-wan` ｜ 戏份:secondary

## 身份
跟着苏栀一起被卷进塔的女孩,看似柔弱,记性好得可怕,能背下整面墙的规则。

## Identity Core
- 不肯当被保护的那个。
- 一旦认定一个人,就豁得出去。

## 核心欲望与底线
想证明自己不是累赘。底线:不丢下同行的人。

## 核心事实
- 过目不忘
- 嘴硬心软
""")
    forge.entity_commit(World_w1, "lu-jia", "路甲", role="cameo", body="# 路甲\n\n第一层撞见的倒霉登塔者,话没说完就违规了。\n")

    forge.thread_commit(World_w1, "first-climb", "首登", genre="无限流", prompt="苏栀与林晚的第一次攀登",
                        pacing="每层推进一条规则+至少一次人物关系升温", body="""# 首登 · 叙事线

> 线 id:`first-climb` ｜ 世界:infinite-tower ｜ 题材:无限流 ｜ 尺度:max

## 立意 / 一句话
两个被同一个人背叛的人,在一座要人付代价的塔里,学着重新信一次。

## 节奏契约
- 每层推进一条规则 + 至少一次人物关系升温

## 大纲
α 悬念:把苏栀捅进塔的"背后那一刀"到底是谁。
- 第一层:矛盾规则,苏栀靠悖论破局,林晚第一次有用。
- 第二层:代价律逼她选,她护住了林晚。
- (待写)第七层裂隙:临江漏进来。
""")
    t1 = __import__("sv.thread", fromlist=["Thread"]).Thread.load(World_w1, "first-climb")

    ch1 = """塔的第一层只有一间惨白的房间,墙上贴着两条规则。

第一条:墙上所有规则都为真。
第二条:第一条规则是假的。

路甲念到一半就笑了,说这不就是个文字游戏,抬脚去推那扇向上的门。门没动,他人却软了下去,像被抽掉了骨头,无声无息地瘫成一摊。

林晚倒抽一口冷气,后退半步撞进苏栀怀里。苏栀没看那摊东西,只盯着墙。她盯了很久,久到林晚以为她也要犯傻。

"啧。"她终于开口,声音很轻,"两条规则打架,塔就是在告诉你——别信墙,信夹缝。"

林晚的脑子转得比谁都快。她忽然明白了:既然两条规则不能同时为真,那"照做"本身就是陷阱,真正的活路是找出墙上没写、却被这对矛盾圈出来的那条缝。她的目光扫过房间四角,落在门框下沿一道几乎看不见的刻痕上。

"那里。"她指过去,手在抖,声音却稳,"刻痕拼起来是第三条规则。墙没写,是怕被人一眼看穿。"

苏栀顺着她指的方向蹲下去,指腹擦过那行细小的字:**背对门,门自开。**

她没多问林晚怎么看出来的,只是反手把她拢到身后,自己背过身去,一步步倒退着走向那扇门。门在她背后,悄无声息地,向上裂开了一道缝。

冷风从缝里灌进来,带着上一层的味道。苏栀回头看了林晚一眼,那一眼里没有夸奖,只有一句没说出口的话:跟紧点。

林晚忽然觉得,这座要人命的塔，好像也没那么冷了。"""

    ch2 = """第二层是一条没有尽头的回廊,每隔十步一盏灯,灯下一面镜子。

规则只有一条,刻在第一面镜子上:**你可以借一次塔外的力,但塔要收回你最在乎的东西。**

苏栀站在镜子前没动。她知道这一层的题在哪——回廊尽头有东西在等她们,凭她现在的伤,正面撑不过去。借力,就能赢;可"最在乎的东西",此刻就站在她半步之后,正用力攥着她的衣角。

"我来。"林晚先开了口,"我没什么可被收走的,我借——"

"闭嘴。"

她打断得很快,快到自己都愣了一下。她很少这样对人说话。林晚被她吓得松了手。

苏栀转过身,第一次正面看她。塔的灯把她眉骨那道疤照得很深。

"你以为你没有可被收走的东西。"她说,"塔不这么算。它会从我这儿收。"

她没再解释,抬手按上镜子。冰冷的力顺着手臂爬上来,她闷哼一声,膝盖一软,却死死站住了。回廊尽头那团黑暗被她一拳轰开,碎成漫天的灰。

代价来得无声无息。她低头,发现自己想不起那一夜捅她的那张脸了——那张她恨了三年、发誓要亲手登顶改写的脸,被塔干干净净地收走了。

林晚扶住她,声音发颤:"你在乎的……是什么?"

苏栀没答。她只是觉得心里空了一块,空得她反而踏实。她把林晚往身后带了带,像每一次那样,挡在她和黑暗之间。

"走了。"她说,"别回头。"""

    r1 = lenses.narrate_commit(World_w1, t1, {
        "chapter_text": ch1, "title": "矛盾的规则",
        "sediments": [
            {"entity": "su-zhi", "text": "靠悖论破解第一层,没问林晚怎么看穿的就护她到身后", "level": "持久", "trace": "第1章"},
            {"entity": "lin-wan", "text": "第一次靠过目不忘救了场,觉得塔没那么冷了", "level": "身份", "trace": "第1章"},
            {"entity": "lu-jia", "text": "违规身亡", "level": "瞬时"},
        ],
        "state_updates": {"su-zhi": {"location": "塔·第二层", "mood": "戒备", "goal": "活过这一层"},
                          "lin-wan": {"location": "塔·第二层", "mood": "微暖", "goal": "证明自己不是累赘"}},
        "beat": "第一层:悖论破局,林晚初次有用",
    })
    r2 = lenses.narrate_commit(World_w1, t1, {
        "chapter_text": ch2, "title": "同行者",
        "sediments": [
            {"entity": "su-zhi", "text": "为护林晚借塔外之力,代价是被收走了仇人的脸——心里空了反而踏实", "level": "身份", "trace": "第2章·成长时刻:违背执念护人"},
            {"entity": "lin-wan", "text": "看见他为自己付代价,第一次意识到他把她算作'最在乎'", "level": "身份", "trace": "第2章"},
        ],
        "state_updates": {"su-zhi": {"location": "塔·第三层", "mood": "空而踏实", "goal": "继续登塔"},
                          "lin-wan": {"location": "塔·第三层", "mood": "动容"}},
        "beat": "第二层:代价律,苏栀护住林晚、丢了仇人的脸",
        "summary": "# 首登 · 摘要\n\n苏栀与林晚被同一人背叛后卷入无限之塔。第一层靠悖论破局(林晚过目不忘初显);第二层苏栀为护林晚借力,被塔收走仇人的脸。两人从互不交底到并肩。α 悬念『背后那一刀是谁』因代价被模糊,埋下更深的钩。",
    })
    print(f"  线『首登』:{r1['chapter']}→{r2['chapter']} 章,沉淀 {len(r1['sedimented'])+len(r2['sedimented'])} 条")

    lenses.play_commit(World_w1, t1, {
        "scene": "第三层歇脚,篝火般的应急灯下", "session": "session-001",
        "transcript": "林晚:你想不起那张脸了,会难过吗?\n苏栀:啧。少了张要恨的脸,睡得着觉。\n林晚:……那你现在最想守住的是什么?\n苏栀沉默了很久,把外套丢给她,没回答。",
        "growth": [{"entity": "lin-wan", "text": "试探他的在乎,得到一件外套作答", "trigger": False},
                   {"entity": "su-zhi", "text": "用沉默和一件外套承认了答案", "trigger": True, "trace": "成长时刻:承认在乎"}],
    })
    print("  小剧场 session-001 已落")

    # ---------- 世界二:临江 ----------
    forge.world_commit("linjiang", "临江", genre="都市黑道", prompt="霓虹表皮下的旧式江湖",
                       from_codex=["neon-jianghu"],
                       body="""# 临江

> 世界 id:`linjiang` ｜ 题材:都市黑道 ｜ 尺度基线:max

## 基调 / 氛围
霓虹、雨、旧义气。摩天楼的影子底下,还有人讲规矩、用刀。关键词:江湖、雨夜、规矩。

## 核心规则
- **规矩大于法**(触发:冲突):在临江,先问规矩,再问对错。
- **欠债要还**(触发:人情/仇怨):人情与仇怨都记账,迟早连本带利。

## 核心冲突
新钱要洗白旧江湖,老规矩的人不肯跪下。

## 与其它世界的连接(暗宇宙)
临江是从「无限之塔」第七层裂隙漏出来的一座城——这里的人不知道,自己活在一层副本里。

## 世界契约
- 入场:本体进 / 换皮进(成为临江土著)
- 离场:带走所得
- 带入物:保留随身物
""")
    w2 = World.load("linjiang")
    forge.entity_commit(w2, "zhao-ting", "赵霆", role="secondary", body="# 赵霆\n\n临江新晋的狠角色,笑面虎,想把旧江湖连根拔了。\n\n## 核心事实\n- 笑里藏刀\n- 不讲旧规矩\n")
    print("  世界:临江 + 赵霆")

    # ---------- L4 枢纽:跨世界穿梭 ----------
    nexus.ascend(World_w1, "su-zhi")
    nexus.link_worlds("infinite-tower", "linjiang", "第七层裂隙通向临江", note="临江是塔的一层副本")
    nexus.summon("su-zhi", w2, entry="换皮进")
    from sv.nexus import NexusEntity
    NexusEntity.load("su-zhi").sediment("linjiang", "在临江以陌生身份醒来,雨夜里仍下意识把路人挡到身后", level="身份", where="cross-world")
    print("  苏栀:升格为跨世界实体 → 临江开化身(换皮进)")

    print("\n✓ 种子完成。启动网页:python -m sv.webapp")


if __name__ == "__main__":
    run()
