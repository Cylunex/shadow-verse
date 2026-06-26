/* views/works.js — 由 index.html 内联脚本按视图拆分（T1.3，纯搬运·零行为变化）。
   跨模块/内联 onclick 经 window 全局命名空间访问，保持原单一作用域语义。 */

async function viewWorks(sub,arg){
  loading();
  const W=OV.worlds;
  const modebar=`<div class="modebar"><span class="ml">用任意玩法开局：</span>
    <span class="mchip core" onclick="location.hash='#/chat'">💬 对话RP</span>
    <span class="mchip core" onclick="location.hash='#/novel'">✍ 小说</span>
    <span class="mchip core" onclick="location.hash='#/companion'">💗 陪伴</span>
    <span class="ml" style="margin-left:8px">衍生镜头（小说页「一稿多吃」转换）：</span>
    <span class="mchip" onclick="location.hash='#/novel'" title="小说→CYOA">🎮 CYOA</span><span class="mchip" onclick="location.hash='#/novel'" title="事件线→剧本">🎬 剧本</span>
    <span class="mchip" onclick="location.hash='#/novel'" title="小说→漫画分镜">🖼 漫画</span><span class="mchip" onclick="location.hash='#/novel'" title="事件线→跑团">🎲 跑团</span></div>`;
  const head=`<div class="page-head"><h1>作品</h1><span class="sub">世界孕育故事，故事留下回响</span>
    <div class="viewsw">
      <span class="vbtn ${sub==='gallery'?'on':''}" onclick="location.hash='#/works/gallery'">▦ 画廊</span>
      <span class="vbtn ${sub==='nexus'?'on':''}" onclick="location.hash='#/works/nexus'">✦ 星图</span>
      <span class="vbtn ${sub==='chron'?'on':''}" onclick="location.hash='#/works/chron'">📜 编年史</span>
    </div></div>`;

  if(sub==='nexus')return worksNexus(head);
  if(sub==='chron')return worksChron(head,arg);

  const cards=W.map(w=>{
    const cc=coverClass(w.genre);
    const tags=(w.genre||'').split(/[\s/·,，]+/).filter(Boolean).slice(0,3)
      .map((t,i)=>`<span class="tag ${['v','c','g'][i]||''}">${esc(t)}</span>`).join('');
    return `<div class="work" onclick="openWork('${w.id}')">
      <div class="cover ${cc}"><div class="vig"></div><div class="sigil">${sigil(w.genre)}</div></div>
      <div class="body"><h3>${esc(w.name)}</h3>
        <div class="desc">${esc(w.genre||'')} · ${w.threads} 条世界线 · ${w.entities} 个角色${w.provenance==='forge'?' · AIGC 锻造':''}</div>
        <div class="tags">${tags}</div>
        <div class="foot"><span>by 你</span><span>${w.entities} 👤 · ${w.threads} 📖</span></div></div>
      <div class="menu" onclick="event.stopPropagation();worldMenu('${jsq(w.id)}','${jsq(w.name)}')">⋯</div></div>`;
  }).join('');
  const newcard=`<div class="work newcard" onclick="actNewWorld()"><div><div style="font-size:34px">＋</div><div style="margin-top:8px">新建作品</div><div style="font-size:12px;margin-top:4px">手写 · 导入卡 · ✨ AI 制作</div></div></div>`;
  app().innerHTML=`<div class="wrap">${head}${modebar}
    <div class="toolrow"><div class="searchbar">🔍 <input id="wsearch" placeholder="搜索作品…"></div>
      <button class="btn ghost sm" onclick="actImportCard()">⤓ 导入卡</button>
      <button class="btn sm" onclick="actNewWorld()">＋ 新建作品</button></div>
    <div class="works" id="worksgrid">${W.length?cards+newcard:newcard}</div>
    ${W.length?'':'<p class="note" style="text-align:center;margin-top:20px">还没有作品。点「新建作品」或导入角色卡；也可在终端跑 <code>python -m sim.seed</code> 播一组 demo。</p>'}</div>`;
  const s=el('wsearch');if(s)s.oninput=()=>{const q=s.value.trim().toLowerCase();
    document.querySelectorAll('#worksgrid .work:not(.newcard)').forEach((c,i)=>{const w=W[i];
      c.style.display=(!q||((w.name+w.genre).toLowerCase().includes(q)))?'':'none';});};
}
function openWork(wid){location.hash='#/chat/'+wid;}
function worldMenu(wid,name){
  openModal(`<h3>${esc(name)}</h3>
    <div class="modal-actions" style="flex-wrap:wrap;justify-content:flex-start;gap:8px">
      <button class="btn ghost sm" onclick="closeModal();location.hash='#/chat/${wid}'">💬 对话</button>
      <button class="btn ghost sm" onclick="closeModal();location.hash='#/novel/${wid}'">✍ 小说</button>
      <button class="btn ghost sm" onclick="closeModal();location.hash='#/worldbook/${wid}'">📜 世界书</button>
      <button class="btn ghost sm" onclick="closeModal();location.hash='#/works/chron/${wid}'">📜 编年史</button>
      <button class="btn ghost sm" style="border-color:#5a2336;color:var(--bad)" onclick="actDelWorld('${jsq(wid)}','${jsq(name)}')">🗑 删除</button>
    </div>`);
}
function worksNexus(head){
  const W=OV.worlds,L=OV.nexus.links||[];
  const wmap={};W.forEach(w=>wmap[w.id]=w.name);const wname=id=>wmap[id]||id;
  // 跨世界角色：合并旧 nexus 实体 + 新「魂」(ascension)；魂为准。incarnations 统一成世界 id 列表。
  const xm=new Map();
  (OV.nexus.entities||[]).forEach(e=>xm.set(e.id,{id:e.id,name:e.name,incs:e.incarnations||[],soul:false}));
  (OV.souls||[]).forEach(s=>xm.set(s.id,{id:s.id,name:s.name,incs:s.worlds||[],soul:true}));
  const X=[...xm.values()];
  const cx=400,cy=170,R=130,vw=800,vh=360;const pos={};
  W.forEach((w,i)=>{const a=-Math.PI/2+i*2*Math.PI/Math.max(1,W.length);pos[w.id]=[cx+R*Math.cos(a),cy+R*Math.sin(a)];});
  let edges='';for(const e of L){const a=pos[e.a],b=pos[e.b];if(a&&b){
    edges+=`<line class="nx-edge" x1="${a[0]}" y1="${a[1]}" x2="${b[0]}" y2="${b[1]}"/><text class="nx-elabel" x="${(a[0]+b[0])/2}" y="${(a[1]+b[1])/2-4}">${esc(e.relation||'')}</text>`;}}
  // 跨世界角色标在其化身世界之间
  for(const x of X){const incs=x.incs;for(let i=0;i<incs.length-1;i++){const a=pos[incs[i]],b=pos[incs[i+1]];
    if(a&&b)edges+=`<text class="nx-elabel" x="${(a[0]+b[0])/2}" y="${(a[1]+b[1])/2+14}" style="fill:var(--violet)">${esc(x.name)} ✦</text>`;}}
  const colors=['#a98bff','#5fe3d2','#ffce86','#97c459','#ff8fb0'];
  let nodes='';W.forEach((w,i)=>{const[x,y]=pos[w.id];const c=colors[i%colors.length];
    nodes+=`<g class="nx-node" onclick="location.hash='#/works/chron/${w.id}'"><circle cx="${x}" cy="${y}" r="34" fill="#16162a" stroke="${c}"/><text class="nx-name" x="${x}" y="${y+54}">${esc(w.name)}</text></g>`;});
  // 世界互联（/link）：按无序世界对归并，每对一行 + 断开
  const pairs=new Map();
  for(const e of L){const k=[e.a,e.b].sort().join('|');if(!pairs.has(k))pairs.set(k,{a:e.a,b:e.b,rels:[]});pairs.get(k).rels.push(e.relation||'连接');}
  const linkRows=[...pairs.values()].map(p=>`<div class="linkrow"><span class="lr-pair">${esc(wname(p.a))} <span class="lr-arr">⇄</span> ${esc(wname(p.b))}</span><span class="lr-rel">${p.rels.map(esc).join(' · ')}</span><button class="lr-x" title="断开这道门" onclick="actUnlinkWorlds('${jsq(p.a)}','${jsq(p.b)}')">✕</button></div>`).join('');
  const xline=X.length?`<p class="note">跨世界的她：${X.map(x=>x.soul?`<a style="color:var(--violet);cursor:pointer" onclick="location.hash='#/incarnations/${x.id}'">${esc(x.name)} ✦</a>`:`<a style="color:var(--violet);cursor:pointer" onclick="location.hash='#/chars'">${esc(x.name)} ✦</a>`).join('、')} —— 点开看她在每个世界里的化身。</p>`
    :'<p class="note">还没有跨世界的角色。在「陪伴」页把一个角色「带出这个世界」，她就能穿行别的世界。</p>';
  app().innerHTML=`<div class="wrap">${head}
    <p class="lead" style="margin:6px 0 14px">你创造的世界与角色如何彼此相连 —— 连线是世界间的「门」，✦ 是在世界间穿行的她。<b style="color:var(--violet)">连一道门</b>，魂就能经它跨越；没有门时只能「无门强召」。</p>
    <div class="toolrow" style="margin-bottom:14px"><span style="flex:1"></span><button class="btn sm" onclick="actLinkWorlds()">＋ 连接两个世界</button></div>
    ${W.length?`<div class="nexusmap"><svg viewBox="0 0 ${vw} ${vh}" xmlns="http://www.w3.org/2000/svg">${edges}${nodes}</svg></div>`:'<div class="empty">还没有世界。</div>'}
    ${linkRows?`<div class="linkpanel"><div class="lp-title">世界互联（门）</div>${linkRows}</div>`:(W.length>1?'<p class="note" style="margin-top:12px">还没有连接。点「连接两个世界」开一道门（裂隙 / 同源 / 传承…），让角色能跨越过去。</p>':'')}
    ${xline}</div>`;
}
async function actLinkWorlds(){
  const ids=OV.worlds.map(w=>w.id);
  if(ids.length<2)return toast('至少要有两个世界才能连接',true);
  formModal('连接两个世界 · 开一道门',[
    {n:'a',label:'世界 A',type:'select',options:ids},
    {n:'b',label:'世界 B',type:'select',options:ids,value:ids[1]},
    {n:'relation',label:'门的性质',type:'select',options:['裂隙','同源','传承','梦境','转世','镜像','其他']},
    {n:'note',label:'描述（可空）',ph:'如 临江是无限塔的一层副本'},
  ],'连接 ✦',async v=>{
    if(v.a===v.b)throw new Error('两个世界不能相同');
    await post('/link',{a:v.a,b:v.b,relation:v.relation,note:v.note||''});
    closeModal();await refresh();route();
    toast(`✓ 已连接 ${v.a} ⇄ ${v.b}（${v.relation}）。魂现在可经这道门跨越，而非「无门强召」。`);
  });
}
async function actUnlinkWorlds(a,b){
  if(!confirm(`断开《${a}》⇄《${b}》之间的所有连接？\n（连接撤掉后，魂仍可强召，但会标记为「无门强召」。）`))return;
  try{await post('/unlink',{a,b});await refresh();route();toast('✓ 已断开');}catch(e){toast('✗ '+e.message,true);}
}
async function worksChron(head,wid){
  if(!wid)wid=(OV.worlds[0]||{}).id;
  if(!wid){app().innerHTML=`<div class="wrap">${head}<div class="empty">还没有世界。</div></div>`;return;}
  let d;try{d=await api('/timeline/'+wid)}catch(e){app().innerHTML=`<div class="wrap">${head}<div class="empty">${esc(e.message)}</div></div>`;return;}
  const sel=`<select onchange="location.hash='#/works/chron/'+this.value" style="background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:7px 11px;color:var(--ink);font:inherit">${OV.worlds.map(w=>`<option value="${w.id}" ${w.id===wid?'selected':''}>${esc(w.name)}</option>`).join('')}</select>`;
  const evs=d.events.map(e=>{
    if(e.kind==='growth')return `<div class="cev star"><div class="w">${esc(e.where||'')} · ${esc(e.name||'')}</div><div class="h">★ 成长时刻 <span class="star">★</span></div><div class="d">${esc(e.text)}</div></div>`;
    return `<div class="cev"><div class="w">${esc(e.where||'')} · ${esc(e.lens||'')} · ${esc(e.thread_title||'')}</div><div class="h">${esc(e.text).slice(0,40)}</div><div class="d">${esc(e.text)}</div></div>`;
  }).join('');
  const xw=(d.cross_world||[]).map(id=>`<div class="cev xw"><div class="w">— · 跨世界</div><div class="h">${esc(id)} 在此有化身</div><div class="d">一个灵魂带着别处的记忆，降临此世界。</div></div>`).join('');
  app().innerHTML=`<div class="wrap">${head}
    <div style="display:flex;align-items:center;gap:12px;margin:6px 0 16px"><span class="lead">《${esc(d.name)}》编年史 —— 跨所有世界线的事件与 ★ 成长，跨世界去向也标在这里。</span><span style="flex:1"></span>${sel}</div>
    <div class="chron">${evs+xw||'<div class="empty">还没有事件 —— 在对话里推几轮、或写一章，就会沉淀到这里。</div>'}</div></div>`;
}


/* —— 暴露到全局命名空间（内联 onclick + 跨模块裸引用）—— */
Object.assign(window, { viewWorks, openWork, worldMenu, worksNexus, worksChron, actLinkWorlds, actUnlinkWorlds });
