/* views/chat.js — 由 index.html 内联脚本按视图拆分（T1.3，纯搬运·零行为变化）。
   跨模块/内联 onclick 经 window 全局命名空间访问，保持原单一作用域语义。 */

window.CHAT=null;
function _av(){return (CHAT&&CHAT.avatar)?('/img/'+CHAT.avatar):''}
function _msgctrl(floor){return (floor!=null&&floor>=0)?`<div class="mtools"><a onclick="traceToggle(${floor})">🔍 溯源</a><a onclick="actEditFloor(${floor})">✎ 编辑</a><a onclick="actRegenFloor(${floor})">🔄 重生成</a><a onclick="actDelFloor(${floor})">🗑 删除</a></div>`:'';}
function _avHtml(){const a=_av();return a?`<img class="cavatar" src="${a}">`:`<div class="cav ${CHAT?coverClass(CHAT.genre):''}"></div>`;}
function bubbleHtml(role,text,floor){
  if(role==='char'){
    const m=String(text).match(/```html\s*([\s\S]*?)```/i);
    const ctrl=_msgctrl(floor);
    const trace=(floor!=null&&floor>=0)?`<div class="trace" id="trace${floor}"></div>`:'';
    if(m){const prose=esc(String(text).replace(m[0],'').trim());
      return `<div class="brow char msg">${_avHtml()}<div class="bcol"><div class="bubble char">${prose?prose+'<br>':''}${_hudIframe(m[1])}</div>${ctrl}${trace}</div></div>`;}
    return `<div class="brow char msg">${_avHtml()}<div class="bcol"><div class="bubble char">${esc(text)}</div>${ctrl}${trace}</div></div>`;
  }
  return `<div class="brow user"><div class="bubble user">${esc(text)}</div></div>`;}
function renderTrace(d){
  const wb=(d.worldbook||[]).map(x=>`<span class="tag2">${esc(x.name||(x.keys&&x.keys[0])||'条目')}${x.constant?' · 常驻':''}</span>`).join('')||'<span style="color:var(--faint)">无命中</span>';
  const mem=(d.memory||[]).map(m=>`<div style="margin:2px 0">· ${esc(m.text)} <span style="color:var(--faint)">(${esc(m.where||m.level||'')})</span></div>`).join('')||'<span style="color:var(--faint)">无</span>';
  const an=(d.anchors||[]).map(a=>`<span class="tag2">${esc(a)}</span>`).join('')||'<span style="color:var(--faint)">无</span>';
  return `<div class="tt">⌖ 这句话从哪来 · 把看不见的机器摊开</div>
    <div class="tr"><span class="tk">触发世界书</span><span>${wb}</span></div>
    <div class="tr"><span class="tk">检索记忆</span><span>${mem}</span></div>
    <div class="tr"><span class="tk">起作用锚点</span><span>${an}</span></div>`;}
async function traceToggle(f){const t=el('trace'+f);if(!t||!CHAT)return;
  const open=t.classList.toggle('on');
  if(!open||t.dataset.loaded)return;
  t.dataset.loaded='1';
  // 取本楼之前最近的一条「你」的话作为检索上下文
  let q='',prev=(t.closest('.brow')||{}).previousElementSibling;
  while(prev){if(prev.classList&&prev.classList.contains('user')){q=(prev.querySelector('.bubble')||{}).textContent||'';break;}prev=prev.previousElementSibling;}
  t.innerHTML=`<div class="tt">⌖ 这句话从哪来</div><div class="tr" style="color:var(--faint)">载入中…</div>`;
  try{const d=await api('/trace?world='+encodeURIComponent(CHAT.wid)+'&entity='+encodeURIComponent(CHAT.eid)+'&q='+encodeURIComponent(q));t.innerHTML=renderTrace(d);}
  catch(e){t.dataset.loaded='';t.innerHTML=`<div class="tt">⌖ 这句话从哪来</div><div class="tr">✗ ${esc(e.message)}</div>`;}}
function _addBubble(role,text){const box=el('chatbox');const w=document.createElement('div');
  w.innerHTML=bubbleHtml(role,text);const row=w.firstElementChild;box.appendChild(row);
  scrollChat();return row.querySelector('.bubble');}
function scrollChat(){const s=document.querySelector('.scroll');if(s)s.scrollTop=s.scrollHeight;}
function _lastCharBubble(){const rows=el('chatbox').querySelectorAll('.brow.char .bubble');return rows[rows.length-1]||null;}

function updateSwBar(r){const c=el('swcount');if(c&&r&&typeof r.swipe_n==='number')c.textContent=((r.swipe_id||0)+1)+'/'+r.swipe_n;
  if(r&&r.vars)renderVars(r.vars);if(r&&r.var_changed&&r.var_changed.length)toast('变量更新：'+r.var_changed.join('、'));}
async function chatSwipe(delta){if(!CHAT)return;const tgt=_lastCharBubble();if(!tgt)return;
  const old=tgt.textContent;if(delta>0)tgt.textContent='…';
  try{const r=await post('/chat/swipe',{world:CHAT.wid,entity:CHAT.eid,delta});
    if(r.note){tgt.textContent=old;toast(r.note);return;}
    finalizeBubble(tgt,r);}
  catch(e){tgt.textContent=old;toast('✗ '+e.message,true)}}
function chatRegen(){return chatSwipe(1);}
async function chatClear(){if(!CHAT)return;if(!confirm('清空与该角色的对话？'))return;
  await post('/chat/clear',{world:CHAT.wid,entity:CHAT.eid});route();}
async function chatUndo(){if(!CHAT)return;await post('/chat/undo',{world:CHAT.wid,entity:CHAT.eid});route();}

/* var board (extends legacy renderVars with vis:rel) */
function renderVars(v){const box=el('varpanel');if(!box)return;
  const meta=(CHAT&&CHAT.varmeta)||{};
  const ks=Object.keys(v||{}).filter(k=>(meta[k]||{}).vis!=='hidden');
  if(!ks.length){box.innerHTML='<p class="note">暂无可见状态。对话中角色会自动产生（如 好感/心防/HP），或在右侧用 AI 建一张状态卡。</p>';return;}
  box.innerHTML=ks.map(k=>{const m=meta[k]||{},val=v[k];const label=esc(m.label||k),icon=m.icon?'':'';
    if(m.vis==='rel'){const rel=relUnwrap(val,CHAT&&CHAT.playerName);
      if(rel){
        const stg=rel['阶段']?`<span class="stage" style="padding:2px 10px;font-size:11px">${esc(rel['阶段'])}</span>`:'';
        const axes=REL_AXES.filter(a=>typeof rel[a.key]==='number').slice(0,5).map(a=>{
          const pct=Math.max(0,Math.min(100,(rel[a.key]-a.min)/((a.max-a.min)||1)*100));
          return `<div class="var"><div class="vh"><span class="vn">${a.key}</span><span class="vv">${rel[a.key]}</span></div><div class="vtrack"><div class="vf" style="width:${pct}%;background:${a.color}"></div></div></div>`;}).join('');
        return `<div style="margin-bottom:10px"><div class="vh" style="margin-bottom:8px"><span class="vn">${label}</span>${stg}</div>${axes}<a class="note" style="color:var(--violet);cursor:pointer" onclick="location.hash='#/companion/${CHAT.wid}/${CHAT.eid}'">完整关系板 ›</a></div>`;
      }
    }
    let disp;
    if((m.vis==='bar')&&typeof val==='number'){const mn=(m.min!=null?m.min:0),mx=(m.max!=null?m.max:100);
      const pct=Math.max(0,Math.min(100,(val-mn)/((mx-mn)||1)*100));
      return `<div class="var"><div class="vh"><span class="vn">${label}</span><span class="vctl"><span class="vv">${esc(''+val)}</span><a onclick="varSet('${jsq(k)}')">改</a><a onclick="varDel('${jsq(k)}')">✕</a></span></div><div class="vtrack"><div class="vf" style="width:${pct}%;background:${m.color||'var(--violet)'}"></div></div></div>`;}
    if(Array.isArray(val))disp=val.map(x=>esc(''+x)).join('、')||'—';
    else if(val&&typeof val==='object')disp=esc(JSON.stringify(val));
    else disp=esc(''+val);
    return `<div class="var"><div class="vh"><span class="vn">${label}</span><span class="vctl"><span class="vv">${disp}</span><a onclick="varSet('${jsq(k)}')">改</a><a onclick="varDel('${jsq(k)}')">✕</a></span></div></div>`;}).join('');}
async function varAdd(){if(!CHAT)return;formModal('加变量',[{n:'name',label:'变量名',ph:'如 好感 / HP / 金钱 / 进度'},{n:'value',label:'初始值',value:'0'}],'加',
  async v=>{if(!v.name)return;const r=await post('/chat/var',{world:CHAT.wid,entity:CHAT.eid,name:v.name,value:v.value});closeModal();renderVars(r.vars)})}
async function varSet(name){if(!CHAT)return;const val=prompt('设「'+name+'」(可写 +5 / -3 增减，或直接写新值)：');if(val==null)return;
  const r=await post('/chat/var',{world:CHAT.wid,entity:CHAT.eid,name,value:val});renderVars(r.vars)}
async function varDel(name){if(!CHAT)return;if(!confirm('删变量「'+name+'」？'))return;const r=await post('/chat/var/del',{world:CHAT.wid,entity:CHAT.eid,name});renderVars(r.vars)}
async function varInit(){if(!CHAT)return;if(!confirm('让 AI 据人设建一张状态卡？会覆盖现有变量。'))return;toast('AI 建卡中…');
  try{const r=await post('/chat/init-vars',{world:CHAT.wid,entity:CHAT.eid});
    if(r.available===false){toast(r.note||'需配 LLM',true);return;}
    CHAT.varmeta={};Object.entries(r.meta||{}).forEach(([k,m])=>CHAT.varmeta[k]=m);
    Object.entries(r.rules||{}).forEach(([k,rl])=>{CHAT.varmeta[k]=Object.assign({min:rl.min,max:rl.max},CHAT.varmeta[k]||{});});
    renderVars(r.data);toast('✓ 已建 '+Object.keys(r.data||{}).length+' 个状态变量');}
  catch(e){toast('✗ '+e.message,true)}}

async function viewChat(wid,eid){
  loading();
  if(!wid){wid=(OV.worlds[0]||{}).id;}
  if(!wid){app().innerHTML='<div class="wrap"><div class="empty">还没有作品。去 <a style="color:var(--violet)" href="#/works">作品库</a> 新建或导入一个。</div></div>';return;}
  if(!eid){eid=await firstEntity(wid);if(!eid){app().innerHTML=`<div class="wrap"><div class="empty">《${esc(wid)}》还没有角色。<a style="color:var(--violet);cursor:pointer" onclick="actNewEntity('${jsq(wid)}')">＋ 新建角色</a></div></div>`;return;}}
  let d,ent,drv;
  try{[d,ent,drv]=await Promise.all([api('/chat/'+wid+'/'+eid),api('/entity/'+wid+'/'+eid).catch(()=>({})),api('/drives/'+wid+'/'+eid).catch(()=>({drives:[]}))]);}
  catch(e){app().innerHTML=`<div class="wrap"><div class="empty">${esc(e.message)}</div></div>`;return;}
  const world=OV.worlds.find(w=>w.id===wid)||{};
  window.CHAT={wid,eid,avatar:d.avatar,genre:world.genre,varmeta:{},anchors:(ent.anchors||[]),
    base_chars:d.base_chars||0,qr:d.quick_replies||[],greetings:d.greetings||[],gid:d.greeting_id||0,
    greetingText:d.greeting||'',playerName:(d.player&&d.player.name)||'你',
    histWin:d.history_window||12,hist:d.history||[],busy:false,stopped:false,ooc:false,name:d.name};
  (d.var_view||[]).forEach(x=>{CHAT.varmeta[x.name]={label:x.label,vis:x.vis,color:x.color,icon:x.icon,min:x.min,max:x.max};});
  Object.entries(d.var_meta||{}).forEach(([k,m])=>{CHAT.varmeta[k]=Object.assign({},CHAT.varmeta[k],m);});

  // conversation list = worlds (click → that world's primary entity)
  const convs=OV.worlds.map(w=>`<div class="conv ${w.id===wid?'on':''}" onclick="location.hash='#/chat/${w.id}'">
    <div class="av ${coverClass(w.genre)}"></div><div class="t"><div class="nm">${esc(w.name)}</div><div class="pv">${esc(w.genre||'')} · ${w.entities}人</div></div></div>`).join('');

  const bubbles=d.history.length?d.history:[];
  const openingProse=(d.history.length?'':(d.greeting||'')) ;
  const gsw=(!d.history.length&&CHAT.greetings.length>1)?`<div class="gswipe">开场白 <a onclick="gswipe(-1)">◀</a> <span id="gscount">${(CHAT.gid+1)}/${CHAT.greetings.length}</span> <a onclick="gswipe(1)">▶</a></div>`:'';
  const opening=openingProse?`<div class="opening"><div class="lead">${md(openingProse)}</div>${gsw}</div>`:'';
  const av=_av();
  const headAv=av?`<div class="av" style="background-image:url('${av}')"></div>`:`<div class="av ${coverClass(world.genre)}"></div>`;

  app().innerHTML=`<div class="chatgrid">
    <div class="convlist">
      <button class="btn newconv" onclick="actNewWorld()">＋ 新建作品</button>
      <div class="convsearch">🔍 <input placeholder="搜索…" oninput="convFilter(this.value)"></div>
      <div class="convgrp">作品</div><div id="convlist">${convs}</div>
    </div>
    <div class="chatmain">
      <div class="chathead">${headAv}
        <div><div class="nm">${esc(world.name||wid)} · ${esc(d.name)}</div><div class="meta">${esc(world.genre||'')}${d.preset_active?' · 🎚 '+esc(d.preset_active):''}</div></div>
        <div class="ch-acts">
          <button class="btn ghost sm" onclick="location.hash='#/companion/${wid}/${eid}'">💗 陪伴视角</button>
          <button class="btn ghost sm" onclick="location.hash='#/novel/${wid}'">📖 沉淀成小说</button>
          ${ent.card&&ent.card.soul_id?`<button class="btn ghost sm" onclick="actSummonSoul('${jsq(ent.card.soul_id)}','${jsq(d.name)}')">✦ 召唤进别的世界</button>`
            :`<button class="btn ghost sm" onclick="actExtract('${jsq(wid)}','${jsq(eid)}','${jsq(d.name)}')">✦ 带去别的世界</button>`}
        </div>
      </div>
      <div class="scroll"><div class="thread" id="chatbox">${opening}${bubbles.map((b,i)=>bubbleHtml(b.role,b.text,i)).join('')}</div></div>
      <div class="composer" id="composer">
        <div class="oocbar"><span class="ooc-toggle" id="ooctgl" onclick="toggleOoc()">🎬 导演指令</span><span class="ooc-hint" id="oochint">关：你在对 ${esc(d.name)} 说话</span>
          <span style="flex:1"></span>
          <span class="swipe" style="margin:0"><a onclick="chatSwipe(-1)">◀</a> <span id="swcount" style="color:var(--faint)">1/1</span> <a onclick="chatSwipe(1)">▶</a> <a onclick="chatRegen()">🔄换一个</a> <a onclick="chatUndo()">↩撤回</a></span>
        </div>
        <div class="qrbar" id="qrbar"></div>
        <div class="box">
          <textarea id="chatmsg" placeholder="对 ${esc(d.name)} 说点什么……"></textarea>
          <button class="sendbtn" id="chatsend">➤</button>
          <button class="sendbtn" id="chatstop" style="display:none;background:var(--bad)">⏹</button>
        </div>
      </div>
    </div>
    <div class="rpanel">
      <div class="ptabs">
        <div class="ptab on" data-pt="info" onclick="ptab(this)">作品</div>
        <div class="ptab" data-pt="sw" onclick="ptab(this)">开关</div>
        <div class="ptab" data-pt="param" onclick="ptab(this)">参数</div>
        <div class="ptab" data-pt="chars" onclick="ptab(this)">角色</div>
      </div>
      <div class="pbody">
        <div class="ptab-pane on" data-pt="info">
          <div class="cardinfo"><div class="cov ${coverClass(world.genre)}"></div>
            <h3>${esc(world.name||wid)}</h3><div class="by">${esc(world.genre||'')}</div>
            <p>${esc((ent.profile_md||'').slice(0,260)||d.player&&('你扮演：'+esc(d.player.name))||'')}</p>
            <div class="tags">${(world.genre||'').split(/[\s/·,，]+/).filter(Boolean).slice(0,4).map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div>
          </div>
        </div>
        <div class="ptab-pane" data-pt="sw">
          <div class="sw-grp">生效预设 · 手艺开关 ${d.preset_active?`<a style="float:right;color:var(--violet);cursor:pointer;font-size:11px" href="#/presets">管理 ›</a>`:''}</div>
          <div id="swmods">${d.preset_active?'<p class="note">载入模块…</p>':'<p class="note">未启用预设。到 <a style="color:var(--violet)" href="#/presets">预设页</a> 导入一套 SillyTavern 预设（活人感/对白优化/防超雄/文风·五感…），每个模块都能在这里逐个勾。</p>'}</div>
          <div class="sw-grp">作者笔记 · 导演旁注</div>
          <textarea id="authornote" rows="4" placeholder="给模型的旁注（基调/方向/避免什么），贯穿注入但不复述" style="width:100%;background:#0d0d18;border:1px solid var(--line);color:var(--ink);border-radius:10px;padding:9px 11px;font:inherit;font-size:13px;resize:vertical">${esc(d.author_note||'')}</textarea>
          <button class="btn ghost sm" style="margin-top:8px;width:100%;justify-content:center" onclick="actSaveNote()">保存笔记</button>
        </div>
        <div class="ptab-pane" data-pt="param">
          <div class="sw-grp">实时状态（角色产生 / 你可改）<a style="float:right;color:var(--gold);cursor:pointer;font-size:11px" onclick="varInit()">🎲AI建卡</a> <a style="float:right;color:var(--violet);cursor:pointer;font-size:11px;margin-right:8px" onclick="varAdd()">＋</a></div>
          <div id="varpanel"></div>
        </div>
        <div class="ptab-pane" data-pt="chars">
          <div class="drives"><div class="dh">🜂 她的内核 · 锚点（跨世界不变量）</div>
            ${(ent.anchors&&ent.anchors.length)?ent.anchors.map((a,i)=>`<div class="drive"><span class="di">${i+1}</span><span class="dt">${esc(a)}</span></div>`).join(''):'<p class="note" style="margin:0">这个角色还没有锚点。提取为魂后会沉淀出跨世界不变量。</p>'}
            <div class="dh" style="margin-top:13px">⚡ 当前驱动 · Desire 层 <span style="text-transform:none;letter-spacing:0">据目标/最近经历投影</span></div>
            ${(drv&&drv.drives&&drv.drives.length)?drv.drives.map(x=>`<div class="drive"><span class="di ${x.source==='目标'?'now':'recent'}">${esc(x.kind)}</span><span class="dt">${esc(x.text)}</span></div>`).join(''):'<p class="note" style="margin:0">此刻没有明确的近期驱动 —— 她的行动由上面的锚点支撑。</p>'}
          </div>
          <div class="pchar"><div class="hd">${headAv}<div class="t"><div class="nm">${esc(d.name)}</div><div class="rl">${ent.card?esc(ent.card.role||''):''}${ent.card&&ent.card.soul_id?' · ✦ 跨世界':''}</div></div></div>
            <div class="ops"><span class="op" onclick="location.hash='#/companion/${wid}/${eid}'">陪伴</span><span class="op" onclick="actEntityCard('${jsq(wid)}','${jsq(eid)}')">资料</span><span class="op" onclick="actExtract('${jsq(wid)}','${jsq(eid)}','${jsq(d.name)}')">提取为魂</span></div>
          </div>
          <p class="note">在「角色」页可查看全部角色与跨世界化身。</p>
        </div>
      </div>
    </div>
  </div>`;

  renderVars(d.vars);
  renderQR();recountCtx();
  if(d.preset_active)fillSwMods(d.preset_active);
  // last swipe count
  const lc=[...(d.history||[])].reverse().find(x=>x.role==='char'&&x.swipes);
  if(lc&&el('swcount'))el('swcount').textContent=((lc.swipe_id||0)+1)+'/'+lc.swipes.length;
  scrollChat();

  function recountCtx(){let chars=CHAT.base_chars||0;
    const bs=[...document.querySelectorAll('#chatbox .bubble')].slice(-(CHAT.histWin||12));
    bs.forEach(b=>chars+=(b.textContent||'').length);
    const tok=Math.round(chars/1.6);CHAT.tok=tok;updateConsole();}
  CHAT.recountCtx=recountCtx;

  const finalize=(bubble,r)=>{finalizeBubble(bubble,r);};
  const sendBlocking=async(bubble,msg)=>{const r=await post('/chat',{world:wid,entity:eid,message:msg});finalize(bubble,r);};
  let abort=null,deltasSeen=0;
  const setBusy=b=>{const s=el('chatsend'),st=el('chatstop'),inp=el('chatmsg'),qb=el('qrbar');
    if(s)s.style.display=b?'none':'';if(st)st.style.display=b?'':'none';if(inp)inp.disabled=b;
    if(qb){qb.style.pointerEvents=b?'none':'';qb.style.opacity=b?'0.5':'';}};
  const sendStream=async(bubble,msg)=>{
    deltasSeen=0;abort=new AbortController();
    const resp=await fetch('/api/chat/stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({world:wid,entity:eid,message:msg}),signal:abort.signal});
    if(!resp.ok||!resp.body)throw new Error('stream unavailable');
    const reader=resp.body.getReader(),dec=new TextDecoder();let buf='',acc='',fin=null;
    for(;;){const{value,done}=await reader.read();if(done)break;
      buf+=dec.decode(value,{stream:true});let i;
      while((i=buf.indexOf('\n\n'))>=0){const line=buf.slice(0,i).split('\n').find(l=>l.startsWith('data:'));buf=buf.slice(i+2);
        if(!line)continue;let o;try{o=JSON.parse(line.slice(5).trim())}catch(e){continue}
        if(o.t!=null){const s=document.querySelector('.scroll');const nearBottom=s?(s.scrollHeight-s.scrollTop-s.clientHeight<80):true;
          deltasSeen++;acc+=o.t;bubble.classList.remove('typing');bubble.textContent=acc;recountCtx();if(nearBottom)scrollChat();}
        else if(o.done)fin=o;}}
    if(fin&&fin.error){const err=new Error(fin.error);err.partial=acc;throw err;}
    if(fin&&fin.available===false){bubble.textContent=fin.reply;return;}
    finalize(bubble,fin||{reply:acc});};
  const send=async(forced)=>{
    if(CHAT.busy)return;
    const inp=el('chatmsg');const msg=(forced!=null?forced:inp.value).trim();if(!msg)return;
    if(forced==null)inp.value='';autoGrow(inp);
    // 首发处理开场白:有真实开场白(greetings 非空)→ 后端会把它落成 floor 0,所以这里把 .opening 替换为真实的 floor-0 气泡,
    // 让 DOM 行与后端 history 一一对应(否则楼层会错位,编辑/删除会打到上一行)。无真实开场白时(仅占位)→ 直接移除。
    const op=document.querySelector('#chatbox .opening');
    if(op){if((CHAT.greetings||[]).length>0){const g=document.createElement('div');g.innerHTML=bubbleHtml('char',CHAT.greetingText||'',0);op.replaceWith(g.firstElementChild);}else{op.remove();}}
    _addBubble('user',msg);const w=_addBubble('char','…');w.classList.add('typing');
    CHAT.busy=true;setBusy(true);CHAT.stopped=false;
    try{
      if(d.llm_available){
        try{await sendStream(w,msg);}
        catch(e){if(CHAT.stopped)throw e;if(deltasSeen>0){w.textContent=(w.textContent||'')+'\n✗ 中断：'+e.message;throw e;}await sendBlocking(w,msg);}
      }else{await sendBlocking(w,msg);}
    }catch(e){if(CHAT.stopped){w.classList.remove('typing');if(!w.textContent||w.textContent==='…')w.textContent='（已停止）';else w.textContent+=' ⏹';}
      else if(!w.textContent.includes('✗')){w.textContent='✗ '+e.message;}}
    finally{CHAT.busy=false;setBusy(false);recountCtx();inp.focus();}};
  CHAT.send=send;
  el('chatsend').onclick=()=>send();
  el('chatstop').onclick=()=>{CHAT.stopped=true;if(abort)abort.abort();};
  const ta=el('chatmsg');
  ta.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}});
  ta.addEventListener('input',()=>autoGrow(ta));
  ta.focus();
}
function autoGrow(ta){if(!ta)return;ta.style.height='46px';ta.style.height=Math.min(ta.scrollHeight,160)+'px';}
function finalizeBubble(bubble,r){const row=bubble.closest('.brow');
  // determine floor index
  const rows=[...el('chatbox').querySelectorAll('.brow')];const fi=rows.indexOf(row);
  const tmp=document.createElement('div');tmp.innerHTML=bubbleHtml('char',r.reply!=null?r.reply:bubble.textContent,fi);
  if(row&&tmp.firstElementChild)row.replaceWith(tmp.firstElementChild);else bubble.textContent=r.reply||'';
  updateSwBar(r);}
async function fillSwMods(pid){const box=el('swmods');if(!box)return;
  try{const det=await api('/preset/'+pid);const mods=(det.modules||[]).filter(m=>!(m.marker||!m.content));
    box.innerHTML=`<div class="note" style="margin:0 0 6px">🎚 <b style="color:var(--ink)">${esc(det.name||pid)}</b></div>`+(mods.length?mods.map(m=>{const on=m.enabled!==false;
      return `<div class="sw"><div class="l">${esc(m.name||m.identifier)}<small>${esc((m.content||'').slice(0,44))}</small></div><div class="toggle ${on?'on':''}" onclick="chatPresetToggle('${jsq(pid)}','${jsq(m.identifier)}',${on?'false':'true'})"></div></div>`;}).join('')
      :'<p class="note">该预设只有占位槽，无可勾模块。</p>');}
  catch(e){box.innerHTML='<p class="note">✗ '+esc(e.message)+'</p>';}}
async function chatPresetToggle(pid,ident,enabled){try{await post('/preset/module',{preset:pid,identifier:ident,enabled:enabled==='true'||enabled===true});fillSwMods(pid);toast('✓ 模块已更新（下条起生效）');}catch(e){toast('✗ '+e.message,true);}}
function renderQR(){const bar=el('qrbar');if(!bar||!CHAT)return;const qr=CHAT.qr||[];
  bar.innerHTML=qr.map((q,i)=>`<button class="qr" onclick="qrSend(${i})" title="${esc(q.message)}">${esc(q.label||q.message)}</button>`).join('')
    +`<button class="qr edit" onclick="actQuickReplies()">＋ 快速回复</button>`;}
function qrSend(i){const q=(CHAT&&CHAT.qr||[])[i];if(q&&CHAT.send)CHAT.send(q.message);}
function ptab(t){document.querySelectorAll('.ptabs .ptab').forEach(x=>x.classList.remove('on'));t.classList.add('on');
  document.querySelectorAll('.ptab-pane').forEach(p=>p.classList.toggle('on',p.dataset.pt===t.dataset.pt));}
function toggleOoc(){if(!CHAT)return;CHAT.ooc=!CHAT.ooc;const c=el('composer'),tg=el('ooctgl'),h=el('oochint'),ta=el('chatmsg');
  c.classList.toggle('director',CHAT.ooc);tg.classList.toggle('on',CHAT.ooc);
  ta.placeholder=CHAT.ooc?'导演指令：如 [下一幕下雨] [她更冷淡些] [跳到第二天]':('对 '+CHAT.name+' 说点什么……');
  h.textContent=CHAT.ooc?'开：导演旁白 ——[方括号] 内容作为指令发给她，引导剧情走向':('关：你在对 '+CHAT.name+' 说话');}
function convFilter(q){q=(q||'').trim().toLowerCase();
  document.querySelectorAll('#convlist .conv').forEach((c,i)=>{const w=OV.worlds[i];c.style.display=(!q||(w.name+w.genre).toLowerCase().includes(q))?'':'none';});}
async function gswipe(delta){if(!CHAT)return;const n=(CHAT.greetings||[]).length;if(n<2)return;
  const idx=((CHAT.gid||0)+delta+n)%n;try{await post('/chat/set-greeting',{world:CHAT.wid,entity:CHAT.eid,idx});route();}catch(e){toast('✗ '+e.message,true)}}
async function actSaveNote(){if(!CHAT)return;const t=el('authornote').value;
  try{await post('/chat/author-note',{world:CHAT.wid,entity:CHAT.eid,text:t});toast('✓ 作者笔记已存，下条起生效');}catch(e){toast('✗ '+e.message,true)}}
async function actQuickReplies(){const cur=(CHAT&&CHAT.qr||[]).map(q=>q.label&&q.label!==q.message?q.label+' | '+q.message:q.message).join('\n');
  formModal('快速回复（每行一条；可写「按钮名 | 发送内容」）',[{n:'list',label:'每行一条',type:'textarea',rows:7,value:cur,ph:'问她在等谁\n陪你坐一会儿 | "陪你坐一会儿"'}],'保存',async v=>{
    const items=v.list.split('\n').map(s=>s.trim()).filter(Boolean).map(s=>{const i=s.indexOf('|');return i>=0?{label:s.slice(0,i).trim(),message:s.slice(i+1).trim()}:{label:s,message:s};});
    const r=await post('/quick-replies',{items});closeModal();if(CHAT)CHAT.qr=r.quick_replies;renderQR();toast('✓ 快速回复已存');});}
function _floorText(i){const h=CHAT&&CHAT.hist;if(h&&h[i]&&h[i].text!=null)return h[i].text;
  const rows=document.querySelectorAll('#chatbox .brow');const b=rows[i]&&rows[i].querySelector('.bubble');return b?b.textContent:'';}
async function actEditFloor(i){if(!CHAT)return;
  let txt=_floorText(i);                                  // 先拉权威原文(含 html HUD 代码块),免 DOM 兜底丢面板
  try{const d=await api('/chat/'+CHAT.wid+'/'+CHAT.eid);if(d.history&&d.history[i]&&d.history[i].text!=null)txt=d.history[i].text;}catch(e){}
  formModal('编辑这楼',[{n:'text',label:'内容',type:'textarea',rows:6,value:txt}],'保存',async v=>{
    await post('/chat/edit',{world:CHAT.wid,entity:CHAT.eid,floor:i,text:v.text});closeModal();route();toast('✓ 已改');});}
async function actDelFloor(i){if(!CHAT)return;if(!confirm('删除这一楼？'))return;
  try{await post('/chat/delete',{world:CHAT.wid,entity:CHAT.eid,floor:i});route();toast('✓ 已删');}catch(e){toast('✗ '+e.message,true)}}
async function actRegenFloor(i){if(!CHAT)return;const rows=document.querySelectorAll('#chatbox .brow');
  if(i<rows.length-1&&!confirm('从这楼重生成会丢弃它之后的对话，继续？'))return;
  toast('重生成中…');try{await post('/chat/floor-regen',{world:CHAT.wid,entity:CHAT.eid,idx:i});route();toast('✓ 已重生成');}catch(e){toast('✗ '+e.message,true)}}


/* —— 暴露到全局命名空间（内联 onclick + 跨模块裸引用）—— */
Object.assign(window, { _av, _msgctrl, _avHtml, bubbleHtml, renderTrace, traceToggle, _addBubble, scrollChat, _lastCharBubble, updateSwBar, chatSwipe, chatRegen, chatClear, chatUndo, renderVars, varAdd, varSet, varDel, varInit, viewChat, autoGrow, finalizeBubble, fillSwMods, chatPresetToggle, renderQR, qrSend, ptab, toggleOoc, convFilter, gswipe, actSaveNote, actQuickReplies, _floorText, actEditFloor, actDelFloor, actRegenFloor });
