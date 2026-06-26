/* views/incarnations.js — 化身对照（T2.4 暗宇宙）：同一个魂在不同世界里的化身并排看。
   只读投影 /api/soul/<sid>/incarnations；跨模块/内联 onclick 经 window 全局命名空间访问。 */

async function viewIncarnations(sid){
  loading();
  if(!sid)sid=((OV.souls||[])[0]||{}).id;
  if(!sid){app().innerHTML=`<div class="wrap"><div class="empty">还没有跨世界的魂。<br>去 <a style="color:var(--violet)" href="#/companion">陪伴</a> 页把一个角色「带出这个世界」，她就会成为可在多个世界对照的魂。</div></div>`;return;}
  let d;try{d=await api('/soul/'+sid+'/incarnations')}
  catch(e){app().innerHTML=`<div class="wrap"><div class="empty">✗ ${esc(e.message)}</div></div>`;return;}
  const name=d.name||sid;
  const origin=d.origin&&d.origin.world?`起源于《${esc(d.origin.world)}》`:'';
  const anchors=(d.anchors&&d.anchors.length)?d.anchors.map(a=>`<span class="kw">${esc(a)}</span>`).join(''):'<span class="note">还没有锚点 —— 提取为魂后会沉淀出来。</span>';
  const idmem=(d.identity&&d.identity.length)?d.identity.map(t=>`<div class="mem">${esc(t)}</div>`).join(''):'<p class="note">还没有跨世界共享的身份记忆。她在每个世界各自经历，身份级的时刻会汇到这里。</p>';
  const incs=d.incarnations||[];
  const cols=incs.map(i=>{
    if(i.missing)return `<div class="inccol"><div class="ic-head missing"><div class="ic-name"><b>${esc(i.entity||'?')}</b><span>《${esc(i.world)}》</span></div></div>
      <div class="ic-body"><p class="note">这具化身所在的世界已不存在了。</p></div></div>`;
    const av=i.avatar?`style="background-image:url('/img/${esc(i.avatar)}')"`:'';
    const cls=i.avatar?'':coverClass(i.genre);
    const st=i.state||{};
    const exps=(i.experiences||[]).slice().reverse().map(x=>`<div class="mile ${x.level==='身份'?'star':''}"><div class="mt">${esc(x.where||'')}${x.level==='身份'?' · ★':''}</div><div class="md">${esc(x.text)}</div></div>`).join('')
      ||'<p class="note">这个世界里还没有共同经历 —— 进去陪她聊聊。</p>';
    const shown=(i.experiences||[]).length;
    const more=(i.exp_count>shown)?`<div class="ic-more">…共 ${i.exp_count} 段经历，更早的在编年史里</div>`:'';
    return `<div class="inccol">
      <div class="ic-head ${cls}" ${av}><div class="vig"></div>
        <div class="ic-name"><b>${esc(i.name)}</b><span>《${esc(i.world_name)}》· ${esc(i.genre||'')}</span></div></div>
      <div class="ic-body">
        <div class="ic-stat"><span><i>◷</i> ${esc(st.location||'—')}</span><span><i>♡</i> ${esc(st.mood||'—')}</span><span><i>✎</i> ${esc(st.goal||'—')}</span></div>
        <button class="btn ghost sm" style="width:100%;justify-content:center;margin:2px 0 14px" onclick="location.hash='#/companion/${jsq(i.world)}/${jsq(i.entity)}'">💗 进这个世界陪她</button>
        <div class="ic-exptitle">这个世界里的经历</div><div class="miles">${exps}${more}</div>
      </div></div>`;
  }).join('');
  app().innerHTML=`<div class="wrap">
    <div class="page-head"><h1>${esc(name)} · 化身对照</h1><span class="sub">同一个灵魂，在不同世界里的样子${origin?' · '+origin:''}</span>
      <span style="flex:1"></span><button class="btn ghost sm" onclick="if(history.length>1)history.back();else location.hash='#/chars'">← 返回</button></div>
    <section class="incsoul">
      <h2>不变的内核 <small>跨世界一致 · 锚点</small></h2><div class="kwrow">${anchors}</div>
      <h2 style="margin-top:18px">她记得的 <small>所有化身共享的身份级深记忆</small></h2>${idmem}
    </section>
    <p class="lead" style="margin:6px 0 14px">下面是她在每个世界里此刻的样子与各自的经历 —— 内核相同，际遇不同。</p>
    <div class="inccols">${cols}</div></div>`;
}


/* —— 暴露到全局命名空间（内联 onclick + 跨模块裸引用）—— */
Object.assign(window, { viewIncarnations });
