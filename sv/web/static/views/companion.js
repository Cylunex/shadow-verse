/* views/companion.js — 由 index.html 内联脚本按视图拆分（T1.3，纯搬运·零行为变化）。
   跨模块/内联 onclick 经 window 全局命名空间访问，保持原单一作用域语义。 */

async function viewCompanion(wid,eid){
  loading();
  if(!wid){wid=(OV.worlds[0]||{}).id;}
  if(!wid){app().innerHTML='<div class="wrap"><div class="empty">还没有角色。去 <a style="color:var(--violet)" href="#/works">作品库</a> 开始。</div></div>';return;}
  if(!eid){eid=await firstEntity(wid);}
  if(!eid){app().innerHTML='<div class="wrap"><div class="empty">这个世界还没有角色。</div></div>';return;}
  let ent,chat,drv;
  try{[ent,chat,drv]=await Promise.all([api('/entity/'+wid+'/'+eid),api('/chat/'+wid+'/'+eid).catch(()=>({})),api('/drives/'+wid+'/'+eid).catch(()=>({drives:[]}))]);}
  catch(e){app().innerHTML=`<div class="wrap"><div class="empty">${esc(e.message)}</div></div>`;return;}
  const c=ent.card||{},st=ent.state||{};const name=c.name||eid;
  const world=OV.worlds.find(w=>w.id===wid)||{};
  const av=ent.avatar?('/img/'+ent.avatar):'';
  const portrait=av?`style="background-image:url('${av}')"`:'';
  const portraitCls=av?'':coverClass(world.genre);
  // relationship object from vars (vis:rel) —— 真实形状是 {对象名:{...}},用 relUnwrap 剥到内层
  const pname=(chat.player&&chat.player.name)||'你';
  let relObj=null;const meta={};(chat.var_view||[]).forEach(x=>meta[x.name]=x);
  for(const x of (chat.var_view||[])){if(x.vis==='rel'){const u=relUnwrap(x.value,pname);if(u)relObj=u;}}
  let relHtml,stageHtml='';
  if(relObj){
    stageHtml=relObj['阶段']?`<div class="stage">${esc(relObj['阶段'])}${relObj['称呼']?' · 称你「'+esc(relObj['称呼'])+'」':''}</div>`:'';
    relHtml=`<div class="rel" style="margin-top:16px">`+REL_AXES.filter(a=>typeof relObj[a.key]==='number').map(a=>{
      const pct=Math.max(0,Math.min(100,(relObj[a.key]-a.min)/((a.max-a.min)||1)*100));
      return `<div class="relrow"><div class="rt"><span class="rn">${a.key}</span><span class="rv">${relObj[a.key]}</span></div><div class="reltrack"><div class="rf" style="width:${pct}%;background:${a.color}"></div></div></div>`;}).join('')+`</div>`;
  }else{
    // fallback: visible numeric bars
    const bars=(chat.var_view||[]).filter(x=>x.vis==='bar'&&typeof x.value==='number');
    relHtml=bars.length?`<div class="rel" style="margin-top:16px">`+bars.map(x=>{const mn=x.min!=null?x.min:0,mx=x.max!=null?x.max:100;const pct=Math.max(0,Math.min(100,(x.value-mn)/((mx-mn)||1)*100));
      return `<div class="relrow"><div class="rt"><span class="rn">${esc(x.label||x.name)}</span><span class="rv">${x.value}</span></div><div class="reltrack"><div class="rf" style="width:${pct}%;background:${x.color||'var(--violet)'}"></div></div></div>`;}).join('')+`</div>`
      :`<p class="note" style="margin:0 0 12px">还没有关系数值。建立一张 galgame 式攻略板（好感/心动/信任/心防/亲密…9 轴 + 阶段/称呼/里程碑），对话里就会随剧情推进。</p>
        <button class="btn ghost sm" onclick="actApplyRel('${jsq(wid)}','${jsq(eid)}')">＋ 建立关系攻略板</button>`;
  }
  // milestones from experiences (身份级标★)
  const exps=ent.experiences||[];
  const miles=exps.length?exps.slice(-8).map(x=>`<div class="mile ${x.level==='身份'?'star':''}"><div class="mt">${esc(x.where||'')}${x.level==='身份'?' · ★成长':''}</div><div class="md">${esc(x.text)}</div></div>`).join(''):'<p class="note">还没有共同经历。聊起来，重要的瞬间会沉淀在这里。</p>';
  const remembered=exps.length?exps[exps.length-1].text:'';
  // Desire 层投影:此处去掉与下方「她记得」重复的那条(最近经历),免同屏重复
  const drvList=((drv&&drv.drives)||[]).filter(x=>x.text!==remembered);
  const soulId=c.soul_id;
  const fwBtn=`<button class="btn ghost sm" onclick="location.hash='#/farewell/${wid}/${eid}'">✦ 带 ${esc(name)} 去别的世界</button>`
    +(soulId?` <button class="btn ghost sm" onclick="location.hash='#/incarnations/${jsq(soulId)}'">✦ 看各世界里的她</button>`:'');

  app().innerHTML=`<div class="wrap">
    <div class="page-head"><h1>陪伴</h1><span class="sub">一个一直在的人</span>
      <span style="flex:1"></span><button class="btn ghost sm" onclick="location.hash='#/chat/${wid}/${eid}'">💬 进入对话</button></div>
    <div class="comp" style="margin-top:18px">
      <div class="her">
        <div class="portrait ${portraitCls}" ${portrait}><div class="vig"></div><div class="name"><b>${esc(name)}</b><span>出自《${esc(world.name||wid)}》${soulId?' · 🜂 魂':''}</span></div></div>
        <div class="stat">
          <div class="line"><i>◷</i> 此刻：${esc(st.location||'—')}</div>
          <div class="line"><i>♡</i> 心情：${esc(st.mood||'—')}</div>
          <div class="line"><i>✎</i> 目标：${esc(st.goal||'—')}</div>
          <div style="display:flex;gap:8px;margin-top:10px">
            <button class="btn ghost sm" style="flex:1;justify-content:center" onclick="actAvatar('${jsq(wid)}','${jsq(eid)}')">🖼 头像</button>
            <button class="btn ghost sm" style="flex:1;justify-content:center" onclick="actRenderEntity('${jsq(wid)}','${jsq(eid)}')">🎭 立绘</button>
          </div>
        </div>
      </div>
      <div class="compmain">
        <section><h2>关系 <small>你们之间发生过的事的总和</small></h2>${stageHtml}${relHtml}</section>
        <section><h2>⚡ 她此刻想 <small>Desire 层 · 据目标与最近经历投影</small></h2>
          ${drvList.length?`<div class="drives" style="background:none;border:none;padding:0;margin:0">`+drvList.map(x=>`<div class="drive"><span class="di ${x.source==='目标'?'now':'recent'}">${esc(x.kind)}</span><span class="dt">${esc(x.text)}</span></div>`).join('')+`</div>`:'<p class="note" style="margin:0">此刻没有明确的近期驱动 —— 由她的锚点（见下）支撑。</p>'}</section>
        <section><h2>她是谁 <small>不会变的内核 · 锚点</small></h2>
          <div class="kwrow">${(ent.anchors&&ent.anchors.length)?ent.anchors.map(a=>`<span class="kw">${esc(a)}</span>`).join(''):'<span class="note">还没有锚点 —— 提取为魂后会沉淀出来。</span>'}</div></section>
        ${remembered?`<section><h2>她记得 <small>从共同经历里被唤起的一刻</small></h2><div class="mem">${esc(remembered)}</div></section>`:''}
        <section><h2>你们的重要时刻</h2><div class="miles">${miles}</div></section>
        <section><h2>✦ 回响 <small>把 ${esc(name)} 带出这个世界</small></h2>
          <p style="color:var(--dim);font-size:13px;line-height:1.75;margin:0 0 13px">你可以把 ${esc(name)} 从《${esc(world.name||wid)}》里带出来 —— ${soulId?'她已是一个魂，可被召唤进别的世界，带着记忆继续陪你。':'先把她提取为「魂」（跨世界不变量），之后就能召唤她降临别的世界。'}原来的世界照常运转，而你带走的，是带着这段经历的她。</p>
          ${fwBtn}</section>
        <div class="composer" style="border:none;padding:0;background:none"><div class="box" style="max-width:none">
          <textarea id="compmsg" placeholder="回 ${esc(name)}……" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();compSend('${wid}','${eid}')}"></textarea>
          <button class="sendbtn" onclick="compSend('${wid}','${eid}')">➤</button></div></div>
      </div>
    </div></div>`;
}
async function actApplyRel(wid,eid){try{await post('/apply-relationship',{world:wid,entity:eid});toast('✓ 已建立关系攻略板，对话里会随剧情推进');route();}catch(e){toast('✗ '+e.message,true)}}
async function actRenderEntity(wid,eid){toast('生成立绘中…（需配出图后端）');
  try{const r=await post('/render/entity',{world:wid,entity:eid});
    if(r&&(r.enabled===false||r.error)){toast(r.note||r.error||'未配出图后端 —— 设置 › 渲染',true);return;}
    toast('✓ 立绘已生成');route();}catch(e){toast('✗ '+e.message,true)}}
function actAvatar(wid,eid){const inp=document.createElement('input');inp.type='file';inp.accept='image/*';
  inp.onchange=async()=>{const f=inp.files&&inp.files[0];if(!f)return;
    const bytes=new Uint8Array(await f.arrayBuffer());let bin='';for(let i=0;i<bytes.length;i++)bin+=String.fromCharCode(bytes[i]);
    const ext=(f.name.split('.').pop()||'png').toLowerCase();
    try{await post('/entity/avatar',{world:wid,entity:eid,img_b64:btoa(bin),ext});toast('✓ 头像已上传');route();}catch(e){toast('✗ '+e.message,true)}};
  inp.click();}
function compSend(wid,eid){const t=el('compmsg');if(!t||!t.value.trim())return;const msg=t.value.trim();
  location.hash='#/chat/'+wid+'/'+eid;
  // hand off the message to chat once it loads
  window._pendingMsg=msg;}


/* —— 暴露到全局命名空间（内联 onclick + 跨模块裸引用）—— */
Object.assign(window, { viewCompanion, actApplyRel, actRenderEntity, actAvatar, compSend });
