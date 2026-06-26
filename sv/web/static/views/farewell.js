/* views/farewell.js — 回响 / 离别（T2.4 暗宇宙·情感重心）。
   把一个角色带出一个世界、送进另一个世界 = 一支三幕短片，不是一个确认框。
   渲染进既有 #farewell 全屏遮罩（复用 .farewell 暗场 + 冻住身后陪伴页），幕间只改 #fwcard，不动路由。
   全部文字 0 token、离线可合成；动态串经 esc()，onclick 内 id 经 jsq()；relUnwrap 复用 components.js。 */

let FW=null;   // 单一事实源；每次开场重置

function fwcard(){return el('fwcard');}
function fwPortrait(extra){return `<div class="fw-portrait ${FW.av?'':coverClass(FW.world.genre)} ${extra||''}" ${FW.av?`style="background-image:url('${esc(FW.av)}')"`:''}></div>`;}
function fwTrim(s,n){s=(s||'').replace(/\s+/g,' ').trim();return s.length>n?s.slice(0,n)+'…':s;}
function fwSwap(html){const card=fwcard();card.classList.remove('fw-swap');void card.offsetWidth;card.innerHTML=html;card.classList.add('fw-swap');}

/* —— 入场（director）—— */
function openFarewell(wid,eid){
  if(!wid){location.hash='#/companion';return;}
  el('farewell').classList.add('on');
  fwcard().innerHTML='<div class="fw-loading">…</div>';
  FW={wid,eid,entry:'本体进',dest:null,busy:false,committed:false};
  Promise.all([api('/entity/'+wid+'/'+eid),api('/chat/'+wid+'/'+eid).catch(()=>({}))])
    .then(([ent,chat])=>{if(!FW)return;fwAssemble(ent,chat);fwRenderAct1();})
    .catch(e=>{fwcard().innerHTML=
      `<div class="fw-k">✦ 回 响 ✦</div><div class="fw-note">没能唤起她：${esc(e.message)}</div>
       <div class="fw-acts"><button class="btn" onclick="closeFarewell()">回到陪伴</button></div>`;});
}
function fwAssemble(ent,chat){
  const c=ent.card||{},st=ent.state||{};
  FW.card=c;FW.st=st;FW.name=c.name||FW.eid;
  FW.world=OV.worlds.find(w=>w.id===FW.wid)||{name:FW.wid,genre:''};
  FW.av=ent.avatar?('/img/'+ent.avatar):'';
  FW.anchors=ent.anchors||[];FW.exps=ent.experiences||[];
  FW.remembered=FW.exps.length?FW.exps[FW.exps.length-1].text:'';
  const ids=FW.exps.filter(x=>x.level==='身份');
  FW.milestone=ids.length?ids[ids.length-1].text:'';
  FW.pname=(chat.player&&chat.player.name)||'你';
  FW.rel=null;
  for(const x of (chat.var_view||[])){if(x.vis==='rel'){const u=relUnwrap(x.value,FW.pname);if(u)FW.rel=u;}}
  FW.soul=c.soul_id||null;
}
function fwTeardown(){const ov=el('farewell');if(ov)ov.classList.remove('on');const card=fwcard();if(card)card.innerHTML='';FW=null;}
function closeFarewell(){const FWx=FW;fwTeardown();
  if(FWx&&location.hash.indexOf('#/farewell/')===0)location.hash='#/companion/'+FWx.wid+'/'+FWx.eid;}
function fwGotoWorks(){fwTeardown();location.hash='#/works';}

/* —— 离别赠言（offline, 0-token）—— */
function composeParting(){
  const r=FW.rel||{};
  const call=(r['称呼']||FW.pname||'你');
  const stage=r['阶段']||'';
  const trust=(typeof r['信任']==='number')?r['信任']:null;
  const guard=(typeof r['心防']==='number')?r['心防']:null;
  const mood=FW.st.mood||'',goal=FW.st.goal||'',loc=FW.st.location||'';
  const lastExp=FW.remembered,milestone=FW.milestone,anchor=FW.anchors[0]||'';
  let L1;
  if(trust!==null||guard!==null){
    if((trust!==null&&trust>=60)||(guard!==null&&guard<=30))L1=`「${call}……真的要带我走？」`;
    else if((trust!==null&&trust<=0)||(guard!==null&&guard>=70))L1=`「${call}。」（她看着你，没立刻动。）`;
    else L1=`「要走了？」`;
  }else if(/戒备|冷|防/.test(mood))L1=`「……要带我走？」`;
  else if(/怕|慌|不安/.test(mood))L1=`「去哪都行，只要不是一个人。」`;
  else if(/暖|甜|安心|依赖/.test(mood))L1=`「我就知道，你不会把我留在这里。」`;
  else L1=`「……要走了？」`;
  let L2;
  if(loc&&goal)L2=`「这个世界的我，大概还会在${loc}，继续${goal}吧。」`;
  else if(loc)L2=`「这个世界的我，还会留在${loc}吧。」`;
  else if(goal)L2=`「这个世界的我，还想着${goal}吧。」`;
  else L2=`「这个世界的我，会留在这里，走向别的结局吧。」`;
  let L3=null;
  if(lastExp)L3=`「但${call}和我一起经历的——${fwTrim(lastExp,40)}——这一段，我带着走。」`;
  else if(milestone)L3=`「${fwTrim(milestone,40)}……这个，我不会忘。」`;
  else if(anchor)L3=`「不管去哪个世界，我还是${anchor}的我。」`;
  const L4=stage?`（你们之间，正停在「${stage}」。）`:null;
  let lines=[L1,L2,L3,L4].filter(Boolean);
  if(lines.length>4)lines=[L1,L2,L4].filter(Boolean);
  return lines;
}
function composeArrival(){
  const r=FW.rel||{};const call=(r['称呼']||FW.pname||'你');
  const gated=FW.result.entry==='无门强召';
  const lastExp=FW.remembered,anchor=FW.anchors[0]||'',goal=FW.st.goal||'';
  const A1=gated?`「这里……和我记得的任何地方都不一样。」`:`「……门的那头，是${FW.destName}。」`;
  let A2;
  if(lastExp)A2=`「但${call}还在。那段——${fwTrim(lastExp,40)}——也还在。」`;
  else if(anchor)A2=`「可我还是${anchor}的我。这点，换多少个世界都不会变。」`;
  else A2=`「至少，${call}把我带来了。从这里重新开始也好。」`;
  const A3=goal?`「那么——${goal}，在这个世界，再试一次。」`:null;
  return [A1,A2,A3].filter(Boolean);
}

/* —— ACT 1 · 临别 —— */
function buildAct1(){
  const others=OV.worlds.filter(w=>w.id!==FW.wid);
  const say=composeParting().map(esc).join('\n');
  return `${fwPortrait()}
    <div class="fw-k">✦ 回 响 ✦</div>
    <h2>要把 ${esc(FW.name)} 带出《${esc(FW.world.name)}》吗</h2>
    <div class="fw-say">${say}</div>
    <div class="fw-note">原来的世界会照常运转，那里的她会走向别的结局。<br>
      而你带走的，是带着这段经历的她——一段不会被改写的回响。</div>
    <div class="fw-acts fw-hesitate">
      <button class="btn ghost" onclick="closeFarewell()">再陪她一会儿</button>
      ${others.length?`<button class="btn" onclick="fwGotoAct2()">带她走，去新的世界 ✦</button>`
        :`<button class="btn" disabled>带她走，去新的世界 ✦</button>`}
    </div>
    ${others.length?'':`<div class="fw-note" style="margin-top:14px;color:var(--gold)">还没有别的世界可去——先去
       <a style="color:var(--cyan);cursor:pointer" onclick="fwGotoWorks()">作品库</a>造一个，门才有彼端。</div>`}`;
}
function fwRenderAct1(){fwcard().innerHTML=buildAct1();}   // 首渲染直接 innerHTML：触发逐元素 fwRise + 700ms 迟疑拍
function fwGotoAct1(){fwSwap(buildAct1());}

/* —— 门预判（前端镜像 ascension.summon 的链接闸门，读 OV.souls）—— */
function fwSoulWorlds(){
  if(FW.soul){const s=(OV.souls||[]).find(x=>x.id===FW.soul);if(s&&s.worlds&&s.worlds.length)return s.worlds.slice();}
  return [FW.wid];
}
function fwGate(destId){
  const sw=fwSoulWorlds();
  for(const ln of (OV.nexus.links||[])){
    const pair=[ln.a,ln.b];
    if(pair.indexOf(destId)>=0&&pair.some(x=>sw.indexOf(x)>=0))return {gated:false,relation:ln.relation||'连接'};
  }
  return {gated:true,relation:'无门'};
}

/* —— ACT 2 · 选门 —— */
function fwGotoAct2(){
  const others=OV.worlds.filter(w=>w.id!==FW.wid);
  const dests=others.map(w=>{const g=fwGate(w.id);
    return `<button class="fw-dest ${g.gated?'gated':'open'}" data-w="${esc(w.id)}" onclick="fwPickDest('${jsq(w.id)}')">
      <div class="fw-dest-cv ${coverClass(w.genre)}"></div>
      <div class="fw-dest-body"><b>${esc(w.name)}</b><span>${esc(w.genre||'—')}</span>
        <em class="fw-gate ${g.gated?'gated':''}">${g.gated?'⚠ 无门强召 · 凭空将她拽入':('⟡ '+esc(g.relation)+' · 循着旧世界的痕迹过去')}</em>
      </div></button>`;}).join('');
  fwSwap(`
    <div class="fw-k">✦ 她 要 去 哪 ✦</div>
    <h2>${esc(FW.name)} 的下一个世界</h2>
    <div class="fw-threshold">
      <div class="fw-tnode"><span class="fw-sig">${sigil(FW.world.genre)}</span><b>${esc(FW.world.name)}</b><small>她现在的世界</small></div>
      <div class="fw-tgate" id="fwgate" data-state="idle"></div>
      <div class="fw-tnode" id="fwdst"><span class="fw-sig">？</span><b>选一个世界</b><small>&nbsp;</small></div>
    </div>
    <div class="fw-dests">${dests}</div>
    <div class="fw-entry" id="fwentry" style="display:none">
      <button class="btn ghost sm on" data-e="本体进" onclick="fwSetEntry('本体进')">本体进 · 还是她自己</button>
      <button class="btn ghost sm" data-e="换皮进" onclick="fwSetEntry('换皮进')">换皮进 · 借这世界一副身体</button>
    </div>
    <div class="fw-doornote" id="fwdoornote"></div>
    <div class="fw-acts">
      <button class="btn ghost" onclick="fwGotoAct1()">← 再想想</button>
      <button class="btn" id="fwgo" disabled onclick="fwCommit()">送她过去 ✦</button>
    </div>`);
}
function fwPickDest(destId){
  const w=OV.worlds.find(x=>x.id===destId)||{};
  FW.dest=destId;FW.destName=w.name||destId;FW.gate=fwGate(destId);
  fwcard().querySelectorAll('.fw-dest').forEach(b=>{
    const sel=b.dataset.w===destId;b.classList.toggle('sel',sel);
    if(sel){   // 同步被选卡的门况徽标（尤其在 fwOpenDoor 就地开门后）
      b.classList.toggle('gated',FW.gate.gated);b.classList.toggle('open',!FW.gate.gated);
      const em=b.querySelector('.fw-gate');
      if(em){em.className='fw-gate '+(FW.gate.gated?'gated':'');
        em.textContent=FW.gate.gated?'⚠ 无门强召 · 凭空将她拽入':('⟡ '+FW.gate.relation+' · 循着旧世界的痕迹过去');}
    }
  });
  el('fwgate').dataset.state=FW.gate.gated?'no':'has';
  el('fwdst').innerHTML=`<span class="fw-sig">${sigil(w.genre)}</span><b>${esc(FW.destName)}</b><small>${FW.gate.gated?'无门':esc(FW.gate.relation)}</small>`;
  el('fwentry').style.display='flex';
  const go=el('fwgo');go.disabled=false;
  if(FW.gate.gated){go.textContent='强召她过去 ⚠';go.classList.add('warn');fwRenderDoorOpener();}
  else{go.textContent='送她过去 ✦';go.classList.remove('warn');el('fwdoornote').innerHTML='';}
}
function fwSetEntry(mode){FW.entry=mode;
  fwcard().querySelectorAll('.fw-entry .btn').forEach(b=>b.classList.toggle('on',b.dataset.e===mode));}
function fwRenderDoorOpener(){
  const anchorWorlds=fwSoulWorlds();
  const opts=anchorWorlds.map(wd=>`<option value="${esc(wd)}">${esc((OV.worlds.find(x=>x.id===wd)||{}).name||wd)}</option>`).join('');
  el('fwdoornote').innerHTML=`
    <div class="fw-door-open">
      <div class="fw-door-open-h">⚠ 《${esc(FW.destName)}》和她待过的世界之间没有门。要不要先开一道？</div>
      <div class="fw-door-open-row">
        <select id="fwrel"><option>裂隙</option><option>同源</option><option>传承</option><option>共享历史</option></select>
        <span>连到</span>
        <select id="fwfrom">${opts}</select>
        <button class="btn ghost sm" onclick="fwOpenDoor()">开门</button>
      </div>
    </div>`;
}
async function fwOpenDoor(){
  if(!FW||FW.busy)return;FW.busy=true;
  const relation=el('fwrel').value,from=el('fwfrom').value;
  try{
    await post('/link',{a:FW.dest,b:from,relation});
    await refresh();FW.busy=false;
    const dest=FW.dest;fwPickDest(dest);   // 重算门况 → 已有门
    toast(`✓ 已在《${FW.destName}》和《${(OV.worlds.find(x=>x.id===from)||{}).name||from}》之间开了一道「${relation}」`);
  }catch(e){FW.busy=false;toast('✗ '+e.message,true);}
}

/* —— ACT 3 · 渡（执行 + 到达）—— */
function fwRenderCrossing(){
  fwSwap(`<div class="fw-crossing">
    <div class="fw-ring" data-state="${FW.gate&&FW.gate.gated?'no':'has'}">${fwPortrait()}<div class="fw-beam"></div></div>
    <div class="fw-note" id="fwstatus">正在把她凝成一个魂…</div>
  </div>`);
}
async function fwCommit(){
  if(!FW||FW.busy||FW.committed||!FW.dest)return;
  FW.busy=true;fwRenderCrossing();
  const status=()=>el('fwstatus');
  try{
    let soul=FW.soul||(FW.card&&FW.card.soul_id);
    if(!soul){
      if(status())status().textContent='正在把她凝成一个魂…';
      try{const r1=await post('/extract',{world:FW.wid,entity:FW.eid});soul=r1.soul;}
      catch(e){if(/已是魂/.test(e.message))soul=(FW.card&&FW.card.soul_id)||FW.eid;else throw e;}
    }
    FW.soul=soul;
    if(status())status().textContent='为她推开《'+FW.destName+'》的门…';
    const r2=await post('/summon-soul',{soul,world:FW.dest,entry:FW.entry});
    FW.committed=true;FW.busy=false;
    FW.result={destEid:r2.incarnation,entry:r2.entry,via:r2.via};   // 后端为终判
    fwRenderArrival();
  }catch(e){
    FW.busy=false;
    if(/已有实体|FileExists/.test(e.message))fwRenderAlreadyThere();
    else fwRenderFail(e.message);
  }
}
function fwRenderArrival(){
  const gated=FW.result.entry==='无门强召';
  const relTxt=FW.result.via||'';
  const say=composeArrival().map(esc).join('\n');
  fwSwap(`${fwPortrait('fw-arrived')}
    <div class="fw-k">${gated?'✦ 无 门 强 召 ✦':'✦ '+esc(relTxt)+' · 已 渡 ✦'}</div>
    <h2>${esc(FW.name)} 来到了《${esc(FW.destName)}》</h2>
    <div class="fw-say">${say}</div>
    <div class="fw-note">
      ${gated?'没有门，她是被生生带来的——给她点时间适应这个陌生的世界。'
        :'她经「'+esc(relTxt)+'」之门而来，记忆完整。'}<br>
      她带着在《${esc(FW.world.name)}》的全部记忆醒来。那边的她，仍在原地。</div>
    <div class="fw-acts">
      <button class="btn" onclick="fwEnter()">陪她在这里继续 →</button>
      <button class="btn ghost" onclick="fwSeeBoth()">看两个世界里的她</button>
    </div>`);
}
function fwRenderAlreadyThere(){
  const dest=FW.dest,eid=FW.eid,name=FW.name,destName=FW.destName;
  fwSwap(`${fwPortrait()}
    <div class="fw-k">✦ 她 已 在 那 里 ✦</div>
    <h2>${esc(name)} 已经在《${esc(destName)}》了</h2>
    <div class="fw-say">「我已经在这儿了呀。」</div>
    <div class="fw-note">这个世界里已经有她的一具化身。</div>
    <div class="fw-acts">
      <button class="btn" id="fwgoexist">去看看她 →</button>
      <button class="btn ghost" onclick="fwGotoAct2()">换个去处</button>
    </div>`);
  const b=el('fwgoexist');if(b)b.onclick=()=>{fwTeardown();location.hash='#/companion/'+dest+'/'+eid;};
}
function fwRenderFail(msg){
  fwSwap(`${fwPortrait()}
    <div class="fw-k fw-fail">✦ 门 没 能 推 开 ✦</div>
    <div class="fw-say fw-fail">${esc(msg)}</div>
    <div class="fw-acts">
      <button class="btn" onclick="fwCommit()">重试</button>
      <button class="btn ghost" onclick="closeFarewell()">回到陪伴</button>
    </div>`);
}
function fwEnter(){const d=FW.dest,e=FW.result.destEid;fwTeardown();
  refresh().then(()=>{location.hash='#/companion/'+d+'/'+e;},()=>{location.hash='#/companion/'+d+'/'+e;});}
function fwSeeBoth(){const s=FW.soul;fwTeardown();
  refresh().then(()=>{location.hash='#/incarnations/'+s;},()=>{location.hash='#/incarnations/'+s;});}


/* —— 暴露到全局命名空间（内联 onclick + 跨模块裸引用）—— */
Object.assign(window,{ openFarewell, closeFarewell, fwTeardown, fwGotoWorks,
  fwRenderAct1, fwGotoAct1, fwGotoAct2, fwPickDest, fwSetEntry,
  fwOpenDoor, fwCommit, fwEnter, fwSeeBoth });
