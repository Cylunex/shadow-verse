/* views/presets.js — 由 index.html 内联脚本按视图拆分（T1.3，纯搬运·零行为变化）。
   跨模块/内联 onclick 经 window 全局命名空间访问，保持原单一作用域语义。 */

let PR={list:[],active:'',sel:null};
async function viewPresets(){
  loading();
  let d;try{d=await api('/presets');}catch(e){app().innerHTML=`<div class="wrap"><div class="empty">${esc(e.message)}</div></div>`;return;}
  PR.list=d.presets||[];PR.active=d.active_preset||'';
  if(!PR.sel||!PR.list.find(p=>p.id===PR.sel))PR.sel=(PR.list[0]||{}).id||null;
  await renderPresets();
}
async function renderPresets(){
  const list=PR.list.length?PR.list.map(p=>`<div class="entry ${p.id===PR.sel?'on':''}" onclick="presetSelect('${jsq(p.id)}')">
    <span>🎚 ${esc(p.name||p.id)}</span>${p.id===PR.active?'<span class="badge">生效中</span>':`<span style="color:var(--faint);font-size:11px">${p.module_count||0}模块</span>`}</div>`).join('')
    :'<p class="note" style="padding:10px">还没有预设。导入一套 SillyTavern 预设 JSON（采样集 + 文风/越狱/防超雄等模块）。</p>';
  let detail='<p class="empty">选一个预设，查看它的模块与采样参数。</p>';
  if(PR.sel){try{detail=presetDetailHtml(await api('/preset/'+PR.sel));}catch(e){detail=`<div class="empty">${esc(e.message)}</div>`;}}
  app().innerHTML=`<div class="wrap">
    <div class="page-head"><h1>预设</h1><span class="sub">SillyTavern 文风/行为模块 + 采样参数 —— 把手艺做成可勾的开关</span>
      <span style="flex:1"></span><button class="btn sm" onclick="actImportPresetFile()">⤓ 导入 ST 预设</button></div>
    <div class="wb" style="margin-top:18px;grid-template-columns:280px 1fr">
      <div class="list">${list}</div>
      <div class="editor">${detail}</div>
    </div></div>`;
}
function presetDetailHtml(d){
  const samp=Object.entries(d.sampling||{}).map(([k,v])=>`<span class="tag c">${esc(k)} ${esc(''+v)}</span>`).join('')||'<span class="note">（该预设未带采样参数）</span>';
  const roleTag=r=>r==='user'?'<span class="pill style">user</span>':r==='assistant'?'<span class="pill">assistant</span>':'<span class="pill sys">system</span>';
  const mods=(d.modules||[]).map(m=>{const on=m.enabled!==false;const isMarker=m.marker||!m.content;
    return `<div class="mod"><div class="info"><div class="h">${esc(m.name||m.identifier)} ${roleTag(m.role)}${isMarker?'<span class="pill">占位槽</span>':''}</div>
      <div class="d">${isMarker?'ST 注入占位（由世界书/角色卡在对应位置填充）':esc((m.content||'').slice(0,140))}</div></div>
      ${isMarker?'':`<div class="toggle ${on?'on':''}" title="开/关这个模块" onclick="presetToggle('${jsq(m.identifier)}',${on?'false':'true'})"></div>`}</div>`;}).join('')||'<p class="note">无模块</p>';
  return `<div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;flex-wrap:wrap">
      <h3 style="margin:0">${esc(d.name)}</h3>${d.active?'<span class="badge" style="background:#62e6a422;color:var(--good)">生效中</span>':''}<span style="flex:1"></span>
      <button class="btn ${d.active?'ghost':''} sm" onclick="presetUse('${jsq(d.active?'':d.id)}')">${d.active?'停用':'启用这套预设'}</button></div>
    <div class="sw-grp">采样参数（导入时自动适配 → 生效后传给模型）</div><div class="tags" style="margin:0 0 16px">${samp}</div>
    <div class="sw-grp">提示词模块 · 逐个可勾（关掉即不注入；空内容的是 ST 占位槽）</div>
    <div class="modlist">${mods}</div>
    <div class="sw-grp">组装后的系统提示（这套预设实际前置注入的）</div>
    <div class="packet" style="max-height:240px;overflow:auto;white-space:pre-wrap;background:#0d0d18;border:1px solid var(--line);border-radius:10px;padding:11px 13px;font-size:12.5px;color:var(--dim)">${esc(d.assembled||'（空 —— 模块都关了或都是占位槽）')}</div>`;
}
function presetSelect(id){PR.sel=id;renderPresets();}
async function presetToggle(ident,enabled){try{await post('/preset/module',{preset:PR.sel,identifier:ident,enabled:enabled==='true'||enabled===true});renderPresets();}catch(e){toast('✗ '+e.message,true);}}
async function presetUse(pid){try{await post('/config',{SV_PRESET:pid});await refresh();PR.active=pid;toast(pid?'✓ 已启用，对话即时生效':'✓ 已停用');renderPresets();}catch(e){toast('✗ '+e.message,true);}}
async function actPresetUse(pid){return presetUse(pid);}
async function actImportPresetFile(){const inp=document.createElement('input');inp.type='file';inp.accept='.json';
  inp.onchange=async()=>{const f=inp.files&&inp.files[0];if(!f)return;const text=await f.text();
    let name=f.name.replace(/\.json$/i,'');try{const j=JSON.parse(text);if(j.name)name=j.name;}catch(e){toast('✗ 不是合法 JSON',true);return;}
    try{const r=await post('/import/preset',{data:text,name});PR.sel=r.preset;await refresh();await viewPresets();
      toast(`✓ 导入「${esc(r.name)}」 —— 模块 ${r.module_count}（自定义 ${r.custom_count}）、采样 ${Object.keys(r.sampling||{}).length} 项`);}
    catch(e){toast('✗ '+e.message,true);}};
  inp.click();}


/* —— 暴露到全局命名空间（内联 onclick + 跨模块裸引用）—— */
Object.assign(window, { PR, viewPresets, renderPresets, presetDetailHtml, presetSelect, presetToggle, presetUse, actPresetUse, actImportPresetFile });
