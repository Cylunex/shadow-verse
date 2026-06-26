/* views/novel.js — 由 index.html 内联脚本按视图拆分（T1.3，纯搬运·零行为变化）。
   跨模块/内联 onclick 经 window 全局命名空间访问，保持原单一作用域语义。 */

async function viewNovel(wid,tid){
  loading();
  if(!wid){const w=OV.worlds.find(w=>w.threads>0)||OV.worlds[0];wid=w&&w.id;}
  if(!wid){app().innerHTML='<div class="wrap"><div class="empty">还没有作品。</div></div>';return;}
  let wd;try{wd=await api('/world/'+wid);}catch(e){app().innerHTML=`<div class="wrap"><div class="empty">${esc(e.message)}</div></div>`;return;}
  if(!wd.threads.length){app().innerHTML=`<div class="wrap"><div class="page-head"><h1>小说 · ${esc(wd.meta.name)}</h1></div>
    <p class="empty">《${esc(wd.meta.name)}》还没有世界线/书。<a style="color:var(--violet);cursor:pointer" onclick="actNewThread('${jsq(wid)}')">＋ 新建一条 ›</a></p></div>`;return;}
  if(!tid)tid=wd.threads[0].id;
  let d;try{d=await api('/thread/'+wid+'/'+tid);}catch(e){app().innerHTML=`<div class="wrap"><div class="empty">${esc(e.message)}</div></div>`;return;}
  window._chs=d.chapters;window._novel={wid,tid,chNo:(d.chapters[0]||{}).no||1};
  const branches=await api('/branches/'+wid+'/'+tid).then(r=>r.branches||[]).catch(()=>[]);
  const otherWorlds=OV.worlds.filter(w=>w.id!==wid&&w.threads>0);
  const chSel=d.chapters.map((c,i)=>`<div class="nv-ch ${i===0?'on':''}" data-ch="${i}" onclick="showCh(${i})">第${c.no}章${c.title?' · '+esc(c.title):''} <span class="w">${c.hanzi}字</span></div>`).join('');
  const threadSel=wd.threads.map(t=>`<div class="nv-ch ${t.id===tid?'on':''}" onclick="location.hash='#/novel/${wid}/${t.id}'">${esc(t.title)} <span class="w">${t.chapters}章</span></div>`).join('');
  const hooks=((d.hooks||{}).items)||[];
  const overdue=new Set(((d.hooks||{}).overdue)||[]);
  const hookHtml=hooks.map(h=>`<div class="hook"><span class="hdot ${h.status==='已回收'?'done':'open'}"></span>${esc(h.desc)}${h.payoff_target?` <span style="color:var(--faint)">→ch${h.payoff_target}</span>`:''}${overdue.has(h.id)?' <span style="color:var(--bad)">⚠过期</span>':''}</div>`).join('');
  const alpha=(d.hooks||{}).alpha;
  const beats=d.beats||[];
  app().innerHTML=`<div class="novel">
    <div class="nv-side">
      <div class="grp">${esc(wd.meta.name)} · 世界线 <a style="color:var(--violet);cursor:pointer;float:right;font-weight:400" onclick="actNewThread('${jsq(wid)}')">＋</a></div>${threadSel}
      <div class="grp" style="margin-top:18px">${esc(d.meta.title)} · 目录</div>${chSel||'<p class="note">还没有章节</p>'}
      <div class="grp" style="margin-top:18px">分支 · 蝴蝶效应 <a style="color:var(--violet);cursor:pointer;float:right;font-weight:400" onclick="actBranch()">＋</a></div>
      ${branches.length?branches.map(b=>`<div class="nv-ch" title="${esc(b.divergence||'')}">⑂ ${esc(b.name||b.id)} <span class="w">第${b.from_chapter}章</span></div>`).join(''):'<p class="note" style="margin:4px 6px">还没有分支。从某章分叉出一条平行线（蝴蝶效应）。</p>'}
      ${otherWorlds.length?`<div class="grp" style="margin-top:18px">其他作品</div>${otherWorlds.map(w=>`<div class="nv-ch" onclick="location.hash='#/novel/${w.id}'">${esc(w.name)}</div>`).join('')}`:''}
    </div>
    <div class="nv-read"><div class="reader2" id="reader">
      <div class="ch-t">载入中</div></div></div>
    <div class="nv-meta">
      <h3>本书</h3>
      <div class="metarow"><span>题材</span><b>${esc(d.meta.genre||'')}</b></div>
      <div class="metarow"><span>章数</span><b>${d.meta.chapter_count||d.chapters.length}</b></div>
      <div class="metarow"><span>字数</span><b>${d.chapters.reduce((a,c)=>a+c.hanzi,0)}</b></div>
      <h3>生效组件 · 写章注入</h3>
      <div class="metarow"><span>📖 名词库</span><b>${((wd.glossary&&wd.glossary.terms)||[]).length} 词</b></div>
      <div class="metarow"><span>🗂 大纲</span><b>${(d.outline&&d.outline.chapters?Object.keys(d.outline.chapters).length:0)} 章细纲</b></div>
      <p class="note" style="margin-top:6px">工艺/配方（去AI味·钩子·扩充·对话·题材配方）+ 名词库 + 大纲随写章自动注入，反思据此查命名漂移/偏离细纲。<a href="/components" target="_blank" style="color:var(--violet)">🧱 组件库 →</a></p>
      <h3>产线 · 写→审→改→落</h3>
      <div class="pipe"><span class="step" onclick="actWriteChapter()">✍ 写一章</span><span class="step" onclick="actNarrateRun()">✨ AI产线</span><span class="step" onclick="actExport()">⤓ 导出</span></div>
      <p class="note">「AI产线」自动写→质检→修订。</p>
      <h3>钩子台账</h3>
      ${alpha?`<div class="hook"><span class="hdot alpha"></span>α 悬念：${esc(alpha)}</div>`:''}
      ${hookHtml||'<p class="note">还没有钩子。</p>'}
      <h3>角色</h3>
      ${(d.entities||[]).map(e=>`<div class="metarow"><span>${esc(e.name)}</span><b>${esc(e.role||'')}</b></div>`).join('')||'<p class="note">—</p>'}
      <h3>跨透镜事件（beats）</h3>
      ${beats.length?`<div class="timeline">${beats.slice(-6).map(b=>`<div class="ev"><div class="w">${esc(b.where||'')} · ${esc(b.lens||'')}</div>${esc((b.text||'').slice(0,90))}</div>`).join('')}</div>`:'<p class="note">RP / 玩一场会在这里落事件。</p>'}
      <h3>质检 · 反思</h3>
      <div class="pipe"><span class="step" onclick="actChecks()">✓ 全书质检</span><span class="step" onclick="actReflect()">🧠 反思自洽</span></div>
      <div id="qaout" class="note" style="margin-top:8px"></div>
      <h3>一稿多吃</h3>
      <div class="pipe"><span class="step" onclick="actConvert('cyoa')">→ CYOA</span><span class="step" onclick="actConvert('screenplay')">→ 剧本</span><span class="step" onclick="actConvert('comic')">→ 漫画</span><span class="step" onclick="actConvert('tabletop')">→ 跑团</span></div>
      <p class="note">把当前章 / 事件线转成另一种镜头（走 convert：配 LLM 一键生成，否则给"转换包"交宿主模型改写）。</p>
    </div></div>`;
  if(d.chapters.length)showCh(0);else el('reader').innerHTML='<div class="empty">还没有章节 —— 点右侧「✍ 写一章」或「✨ AI产线」。</div>';
}
function showCh(i){const c=window._chs[i];if(!c)return;
  if(window._novel)window._novel.chNo=c.no;
  document.querySelectorAll('.nv-side .nv-ch[data-ch]').forEach(n=>n.classList.toggle('on',+n.dataset.ch===i));
  el('reader').innerHTML=`<div class="ch-t">第 ${c.no} 章</div><h2>${esc(c.title||'')}</h2>
    <div class="prose">${md(c.text)}</div>
    <div class="contbar">
      <button class="btn ai sm" onclick="actNarrateRun()">✨ AI 写下一章</button>
      <button class="btn ghost sm" onclick="actReflect()">🧠 反思校验</button>
      <button class="btn ghost sm" onclick="actExport()">⤓ 导出全书</button>
    </div>`;
}
async function actExport(){if(!window._novel)return;const {wid,tid}=window._novel;
  try{const r=await api('/export/thread/'+wid+'/'+tid);const b=new Blob([r.content],{type:'text/markdown;charset=utf-8'});
    const u=URL.createObjectURL(b);const a=document.createElement('a');a.href=u;a.download=r.filename;a.click();URL.revokeObjectURL(u);
    toast(`✓ 已导出《${esc(r.filename)}》(${r.chapters}章 / ${r.hanzi}字)`);}catch(e){toast('✗ '+e.message,true)}}
async function actNarrateRun(){if(!window._novel)return;const {wid,tid}=window._novel;
  if(!(OV.llm&&OV.llm.available)){toast('需先在设置里配 LLM',true);return;}
  formModal('✨ AI 产线写一章',[{n:'intent',label:'这一章想写什么（可空，让它顺着钩子走）',type:'textarea',rows:3,ph:'如：让蓑衣人揭露身份'}],'开始',async v=>{
    closeModal();toast('AI 产线运行中（写→质检→修订）…');
    try{await post('/narrate/run',{world:wid,thread:tid,intent:v.intent||''});toast('✓ 新章已落');route();}catch(e){toast('✗ '+e.message,true)}});}
async function actNewThread(wid){
  if(!wid)wid=(window._novel&&window._novel.wid)||(OV.worlds[0]||{}).id;
  if(!wid)return toast('先建一个作品',true);
  formModal('新建世界线（书）',[
    {n:'title',label:'书名 / 线名',ph:'如 第一卷 · 初遇'},
    {n:'id',label:'id（英文 kebab-case，留空按书名推断；中文请填）',ph:'如 vol-1'},
    {n:'genre',label:'题材（可空，默认随世界）',ph:''},
  ],'新建',async v=>{
    if(!v.title)throw new Error('起个名');
    const id=v.id||asciiSlug(v.title);
    if(!isId(id))throw new Error('id 需为英文 kebab-case；中文名请手动填一个 id');
    await post('/thread/create',{world:wid,id,title:v.title,genre:v.genre});
    closeModal();await refresh();location.hash='#/novel/'+wid+'/'+id;toast('✓ 已建世界线《'+v.title+'》');
  });
}
/* 人在环手写：取写作包 → 交宿主模型/自己写 → 回填正文 → /narrate/commit 落章 */
async function actWriteChapter(){if(!window._novel)return;const {wid,tid}=window._novel;
  const o=openModal(`<h3>✍ 手写下一章 · 人在环（取包 → 回填 → 落）</h3>
    <div class="field"><label>① 这一章想写什么（可空，让它顺着钩子走）</label><input id="w_intent" placeholder="如：让蓑衣人揭露身份"></div>
    <div style="display:flex;gap:8px;align-items:center;margin:2px 0 6px"><button class="btn ghost sm" id="w_pack">取写作包</button><button class="btn ghost sm" id="w_copy" style="display:none">⧉ 复制</button><span class="note" id="w_packnote" style="margin:0"></span></div>
    <div class="packet" id="w_packbox" style="display:none;max-height:30vh;overflow:auto;white-space:pre-wrap;font-size:12px"></div>
    <div class="field" style="margin-top:10px"><label>② 章节标题</label><input id="w_title" placeholder="本章标题"></div>
    <div class="field"><label>③ 章节正文（把你/宿主模型写好的贴进来）</label><textarea id="w_text" rows="9" placeholder="把写好的正文贴进来…"></textarea></div>
    <div class="err" id="w_err"></div>
    <div class="modal-actions"><button class="btn ghost" onclick="closeModal()">取消</button><button class="btn" id="w_ok">落这一章</button></div>`);
  let packText='';
  o.querySelector('#w_pack').onclick=async()=>{const b=o.querySelector('#w_pack');const t0=b.textContent;b.textContent='取包中…';b.disabled=true;o.querySelector('#w_err').textContent='';
    try{const intent=o.querySelector('#w_intent').value.trim();
      const r=await api('/prep/narrate?world='+encodeURIComponent(wid)+'&thread='+encodeURIComponent(tid)+(intent?'&intent='+encodeURIComponent(intent):''));
      packText=JSON.stringify(r,null,2);
      const box=o.querySelector('#w_packbox');box.style.display='block';box.textContent=packText;
      o.querySelector('#w_copy').style.display='';o.querySelector('#w_packnote').textContent='第 '+(r.writing_chapter||'?')+' 章 · 复制给你的写作模型';
    }catch(e){o.querySelector('#w_err').textContent='✗ '+e.message;}finally{b.textContent=t0;b.disabled=false;}};
  o.querySelector('#w_copy').onclick=async()=>{try{await navigator.clipboard.writeText(packText);toast('✓ 写作包已复制');}catch(e){toast('✗ 复制失败，手动选中复制',true);}};
  o.querySelector('#w_ok').onclick=async()=>{const text=o.querySelector('#w_text').value.trim();if(!text){o.querySelector('#w_err').textContent='✗ 先把正文贴进来';return;}
    try{const r=await post('/narrate/commit',{world:wid,thread:tid,chapter_text:text,title:o.querySelector('#w_title').value.trim()});
      closeModal();const fnd=(r.auto_checks||[]).length;toast('✓ 已落第 '+r.chapter+' 章（'+(r.hanzi||0)+'字'+(fnd?(' · '+fnd+' 条质检提示'):'')+'）');route();}
    catch(e){o.querySelector('#w_err').textContent='✗ '+e.message;}};
}
function _qa(html){const o=el('qaout');if(o)o.innerHTML=html;}
async function actChecks(){if(!window._novel)return;const {wid,tid}=window._novel;_qa('<span style="color:var(--faint)">全书质检中…（确定性，0 token）</span>');
  try{const r=await post('/checks',{world:wid,thread:tid});const f=r.findings||[];
    _qa(`<b style="color:var(--ink)">✓ 全书质检（${r.chapters||0} 章）</b><br>`+(f.length?f.map(x=>'· '+esc(x)).join('<br>'):'<span style="color:var(--good)">未见基线问题</span>'));}
  catch(e){_qa('✗ '+esc(e.message));}}
async function actReflect(){if(!window._novel)return;const {wid,tid}=window._novel;
  if(!(OV.llm&&OV.llm.available)){_qa('<span style="color:var(--gold)">反思自洽需配 LLM（确定性质检可直接用「全书质检」）。</span>');return;}
  _qa('<span style="color:var(--faint)">反思校验中…</span>');
  try{const r=await post('/narrate/reflect',{world:wid,thread:tid,last:5});
    const f=r.findings||r.issues||[];_qa('<b style="color:var(--ink)">🧠 反思</b><br>'+(Array.isArray(f)&&f.length?f.map(x=>'· '+esc(typeof x==='string'?x:JSON.stringify(x))).join('<br>'):esc(JSON.stringify(r)).slice(0,600)));}
  catch(e){_qa('✗ '+esc(e.message));}}
async function actConvert(to){if(!window._novel)return;const {wid,tid,chNo}=window._novel;
  const beatsBased=(to==='screenplay'||to==='tabletop');
  const body={world:wid,thread:tid,to,run:!!(OV.llm&&OV.llm.available)};
  if(!beatsBased)body.chapter=chNo||1;
  _qa('<span style="color:var(--faint)">转换中…</span>');
  try{const r=await post('/convert',body);_qa('');const pack=r.pack||{};
    const tname=(pack.target&&pack.target.name)||to;
    const result=r.output||(r.available===false?'':r.note||'');
    openModal(`<h3>一稿多吃 → ${esc(tname)}</h3>
      <p class="note" style="margin-top:0">源：${esc(pack.from||'')}${pack.title?' · '+esc(pack.title):''}</p>
      ${result?`<div class="packet" style="max-height:52vh;overflow:auto;white-space:pre-wrap">${esc(result)}</div>`
        :`<p class="note">未配 LLM —— 这是「转换包」，可整段交给宿主模型改写：</p><div class="packet" style="max-height:46vh;overflow:auto;white-space:pre-wrap">${esc((pack.guide||'')+'\n\n— 源材料 —\n'+(pack.material||'').slice(0,1400))}</div>`}
      <div class="modal-actions"><button class="btn" onclick="closeModal()">好</button></div>`);}
  catch(e){_qa('✗ '+esc(e.message));}}
async function actBranch(){if(!window._novel)return;const {wid,tid}=window._novel;
  formModal('从某章分叉一条平行线（蝴蝶效应）',[
    {n:'from_chapter',label:'从第几章分叉',value:String(window._novel.chNo||1)},
    {n:'name',label:'分支名',ph:'如 若苏栀先出手'},
    {n:'divergence',label:'这一支哪里不同',type:'textarea',rows:2,ph:'第一层不靠悖论，直接强闯'},
  ],'分叉 ⑂',async v=>{await post('/branch',{world:wid,thread:tid,from_chapter:parseInt(v.from_chapter)||1,name:v.name,divergence:v.divergence});closeModal();route();toast('✓ 已分叉一条平行线');});}


/* —— 暴露到全局命名空间（内联 onclick + 跨模块裸引用）—— */
Object.assign(window, { viewNovel, showCh, actExport, actNarrateRun, actNewThread, actWriteChapter, _qa, actChecks, actReflect, actConvert, actBranch });
