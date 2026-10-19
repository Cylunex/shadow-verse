/* views/tavern.js — 混沌酒馆小切片:chips + 题材过滤 + 最近入座 + 陪伴板 peek(非 P5) */
const TAVERN_LAST_KEY='sv_tavern_last';
const TAVERN_PEEK_AXES=['好感','心动','信任','亲密'];

function tavernRemember(wid){
  if(!wid)return;
  try{localStorage.setItem(TAVERN_LAST_KEY,String(wid))}catch(e){}
}
function tavernLast(){
  try{return localStorage.getItem(TAVERN_LAST_KEY)||''}catch(e){return ''}
}
function tavernGenreOf(w){
  return ((w&&w.genre)||'').split(/[\s/·,，]+/).filter(Boolean)[0]||'';
}

/** 轻量 peek:最近入座世界(或首个世界)的主角色关系板 — GET /api/rel-board */
async function tavernLoadPeek(){
  const W=OV.worlds||[];
  if(!W.length)return null;
  const last=tavernLast();
  const wid=(last&&W.some(w=>w.id===last))?last:W[0].id;
  let eid;
  try{eid=await firstEntity(wid);}catch(e){return null;}
  if(!eid)return null;
  try{
    const b=await api('/rel-board/'+encodeURIComponent(wid)+'/'+encodeURIComponent(eid));
    return {wid,eid,worldName:(W.find(w=>w.id===wid)||{}).name||wid,...b};
  }catch(e){return null;}
}

function tavernPeekHtml(peek){
  if(!peek)return '';
  const rel=peek.rel||{};
  const stage=rel['阶段']||'陌生人';
  const call=rel['称呼']?' · 称你「'+esc(rel['称呼'])+'」':'';
  const who=voiceWho({voice:(peek.voice&&peek.voice.key)||peek.voice},peek.name);
  const axes=TAVERN_PEEK_AXES.map(k=>{
    const a=REL_AXES.find(x=>x.key===k)||{key:k,min:0,max:100,color:'var(--violet)'};
    const val=typeof rel[k]==='number'?rel[k]:0;
    const pct=relBarPct(a,val);
    return `<div class="peek-axis"><span class="pn">${esc(k)}</span>
      <div class="peek-track"><div class="peek-fill" style="width:${pct}%;background:${a.color}"></div></div>
      <span class="pv">${val}</span></div>`;
  }).join('');
  const bare=!peek.has_rel;
  const ms=(rel['里程碑']||[]).filter(Boolean).slice(-2);
  const msHtml=ms.length?`<div class="peek-ms">${ms.map(m=>`<span class="kw" style="background:#ffcd6b18;border-color:#5a4a2a;color:var(--gold)">★ ${esc(m)}</span>`).join('')}</div>`:'';
  const note=bare?`<p class="note" style="margin:8px 0 0">还没有攻略板 —— 进陪伴可一键建立。</p>`:'';
  return `<div class="tavern-sec">
    <div class="tavern-sec-h">陪伴速览 <span class="note" style="margin:0">${esc(peek.worldName)} · ${esc(peek.name)}</span></div>
    <div class="peek-card" onclick="location.hash='#/companion/${jsq(peek.wid)}/${jsq(peek.eid)}'" title="打开陪伴">
      <div class="peek-head">
        <div class="peek-who"><span class="peek-flame">💗</span><b>${esc(peek.name)}</b>
          <span class="note" style="margin:0">与${esc(who)} · ${esc(stage)}${call}</span></div>
        <button type="button" class="btn ghost sm" onclick="event.stopPropagation();location.hash='#/companion/${jsq(peek.wid)}/${jsq(peek.eid)}'">打开</button>
      </div>
      <div class="peek-axes">${axes}</div>
      ${msHtml}${note}
    </div>
  </div>`;
}

async function viewTavern(){
  loading();
  const W=OV.worlds||[];
  const souls=OV.souls||[];
  const links=(OV.nexus&&OV.nexus.links)||[];
  const last=tavernLast();
  const genres=[...new Set(W.map(tavernGenreOf).filter(Boolean))];
  const ordered=last?[...W].sort((a,b)=>(a.id===last?-1:0)-(b.id===last?-1:0)):W.slice();
  const peek=await tavernLoadPeek();

  const filters=genres.length?`<div class="chips tavern-filters" id="tavernfilters">
    <span class="fchip on" data-g="" onclick="tavernFilter(this,'')">全部</span>
    ${genres.map(g=>`<span class="fchip" data-g="${esc(g)}" onclick="tavernFilter(this,'${jsq(g)}')">${esc(g)}</span>`).join('')}
  </div>`:'';

  const chips=ordered.map(w=>{
    const g=tavernGenreOf(w);
    const tag=g?`<span class="wchip-g">${esc(g)}</span>`:'';
    const isLast=w.id===last;
    return `<button type="button" class="wchip${isLast?' last':''}" data-genre="${esc(g)}" data-wid="${esc(w.id)}"
      onclick="tavernEnter('${jsq(w.id)}','chat')" title="${isLast?'最近入座 · ':''}入座 · 对话">
      <span class="wchip-dot ${coverClass(w.genre)}"></span>
      <span class="wchip-body"><b>${esc(w.name)}${isLast?' <span class="wchip-last">最近</span>':''}</b>
        <span class="wchip-meta">${tag}${w.entities||0} 角色 · ${w.threads||0} 线</span></span>
      <span class="wchip-doors" onclick="event.stopPropagation()">
        <span class="wchip-door" title="陪伴" onclick="tavernEnter('${jsq(w.id)}','companion')">💗</span>
        <span class="wchip-door" title="小说" onclick="location.hash='#/novel/${jsq(w.id)}'">✍</span>
      </span>
    </button>`;
  }).join('');

  const lamps=souls.length?souls.map(s=>{
    const n=(s.worlds&&s.worlds.length)||(s.incarnations&&s.incarnations.length)||0;
    return `<button type="button" class="lamp" onclick="location.hash='#/incarnations/${jsq(s.id)}'" title="看各世界化身">
      <span class="lamp-flame">✦</span><b>${esc(s.name)}</b><span class="lamp-meta">${n} 世界</span></button>`;
  }).join(''):'';

  const empty=W.length?'':`<div class="tavern-empty">
    <p>酒馆还空着。先开一扇世界之门，或从作品库动手。</p>
    <div class="tavern-doors">
      <button class="btn sm" onclick="actNewWorld()">＋ 新建世界</button>
      <button class="btn ghost sm" onclick="location.hash='#/works'">🎴 作品库</button>
    </div></div>`;
  const doorNote=links.length?`已有 ${links.length} 道世界之门`:'世界之间还没有门 · 在星图可连';
  const lastName=(W.find(w=>w.id===last)||{}).name;
  const lastHint=lastName?` · 最近入座「${lastName}」`:'';

  app().innerHTML=`<div class="wrap tavern-hub">
    <div class="tavern-hero">
      <div class="tavern-eyebrow">混沌酒馆</div>
      <h1>入座</h1>
      <p class="lead">三千世界在此交汇。点一枚世界 chip 入座对话；✦ 心灯是跨世界的魂。</p>
      <div class="tavern-doors">
        <button class="btn sm" onclick="location.hash='#/companion'">💗 去陪伴</button>
        <button class="btn ghost sm" onclick="location.hash='#/works'">🎴 作品画廊</button>
        <button class="btn ghost sm" onclick="location.hash='#/works/nexus'">✦ 星图</button>
        <button class="btn ghost sm" onclick="location.hash='#/chars'">👤 角色</button>
      </div>
      <p class="note" style="margin-top:10px">${esc(doorNote)}${esc(lastHint)}</p>
    </div>
    ${tavernPeekHtml(peek)}
    <div class="tavern-sec">
      <div class="tavern-sec-h">三千世界 <span class="note" style="margin:0">${W.length?W.length+' 扇门 · 点 chip 入座':''}</span></div>
      ${filters}
      <div class="wchips" id="tavernchips">${chips||''}</div>
      <p class="note" id="tavernfilternote" style="display:none;margin-top:10px">这个题材下还没有世界。</p>
      ${empty}
    </div>
    ${souls.length?`<div class="tavern-sec">
      <div class="tavern-sec-h">心灯 · 跨世界的魂 <span class="note" style="margin:0">${souls.length} 盏</span></div>
      <div class="lamps">${lamps}</div>
    </div>`:''}
  </div>`;
}

function tavernFilter(elChip,genre){
  const box=document.getElementById('tavernfilters');
  if(box)box.querySelectorAll('.fchip').forEach(c=>c.classList.toggle('on',c===elChip));
  let n=0;
  document.querySelectorAll('#tavernchips .wchip').forEach(chip=>{
    const show=!genre||chip.getAttribute('data-genre')===genre;
    chip.style.display=show?'':'none';
    if(show)n++;
  });
  const note=document.getElementById('tavernfilternote');
  if(note)note.style.display=(genre&&n===0)?'':'none';
}

async function tavernEnter(wid,mode){
  mode=mode||'chat';
  tavernRemember(wid);
  try{
    const eid=await firstEntity(wid);
    if(!eid){toast('这个世界还没有角色 —— 先去加一个',true);location.hash='#/chars';return;}
    location.hash='#/'+mode+'/'+wid+'/'+eid;
  }catch(e){toast('✗ '+(e.message||e),true);}
}

Object.assign(window, { viewTavern, tavernEnter, tavernFilter, tavernRemember, tavernLast, tavernLoadPeek });
