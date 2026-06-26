/* views/worldbook.js — 由 index.html 内联脚本按视图拆分（T1.3，纯搬运·零行为变化）。
   跨模块/内联 onclick 经 window 全局命名空间访问，保持原单一作用域语义。 */

window.WB={wid:null,entries:[],sel:null};
async function viewWorldbook(wid){
  loading();
  if(!wid){wid=(OV.worlds[0]||{}).id;}
  if(!wid){app().innerHTML='<div class="wrap"><div class="empty">还没有世界。</div></div>';return;}
  let d;try{d=await api('/worldbook/'+wid);}catch(e){app().innerHTML=`<div class="wrap"><div class="empty">${esc(e.message)}</div></div>`;return;}
  window.WB={wid,entries:d.entries||[],sel:(d.entries[0]||{}).uid};
  renderWorldbook(d.name);
}
function renderWorldbook(wname){
  const sel=`<select onchange="location.hash='#/worldbook/'+this.value" style="background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:7px 11px;color:var(--ink);font:inherit">${OV.worlds.map(w=>`<option value="${w.id}" ${w.id===WB.wid?'selected':''}>${esc(w.name)}</option>`).join('')}</select>`;
  const list=WB.entries.map(e=>`<div class="entry ${e.uid===WB.sel?'on':''}" onclick="wbSelect(${e.uid})">${esc(e.name||'(无名)')}${e.constant?'<span class="badge">常驻</span>':''}</div>`).join('')
    ||'<p class="note" style="padding:10px">还没有条目。点「＋ 新建条目」，或导入角色卡时会自动带入世界书。</p>';
  const cur=WB.entries.find(e=>e.uid===WB.sel);
  app().innerHTML=`<div class="wrap">
    <div class="page-head"><h1>世界书 <span class="sub">· ${esc(wname||WB.wid)}</span></h1><span style="flex:1"></span>${sel}</div>
    <div class="toolrow"><button class="btn sm" onclick="wbNew()">＋ 新建条目</button>
      <span class="note" style="margin:0">命中关键词即把设定注入对话上下文；常驻条目始终注入。</span></div>
    <div class="wb" style="margin-top:18px">
      <div class="list">${list}</div>
      <div class="editor" id="wbeditor">${cur?wbEditor(cur):'<p class="empty">选一条，或新建。</p>'}</div>
    </div></div>`;
}
function wbEditor(e){
  return `<div class="field"><label>条目名</label><input id="wb_name" value="${esc(e.name||'')}"></div>
    <div class="field"><label>关键词（逗号分隔，命中即注入）</label><input id="wb_keys" value="${esc((e.keys||[]).join(', '))}"></div>
    <div class="field"><label>内容</label><textarea id="wb_content" rows="6">${esc(e.content||'')}</textarea></div>
    <div class="grid2">
      <div class="field"><label>注入位置</label><select id="wb_pos">
        <option value="0" ${e.position==0?'selected':''}>角色描述之前</option>
        <option value="1" ${e.position==1?'selected':''}>角色描述之后</option>
        <option value="4" ${e.position==4?'selected':''}>对话最近处 @D${e.depth||4}</option></select></div>
      <div class="field"><label>排序优先级</label><input id="wb_order" value="${e.order!=null?e.order:100}"></div>
    </div>
    <div class="swline">常驻（始终注入）<div class="toggle ${e.constant?'on':''}" id="wb_const" onclick="this.classList.toggle('on')"></div></div>
    <div class="swline">区分大小写<div class="toggle ${e.case_sensitive?'on':''}" id="wb_cs" onclick="this.classList.toggle('on')"></div></div>
    <div class="modal-actions" style="margin-top:18px">
      ${e.uid!=null?`<button class="btn ghost" style="border-color:#5a2336;color:var(--bad);margin-right:auto" onclick="wbDelete(${e.uid})">删除</button>`:''}
      <button class="btn" onclick="wbSave(${e.uid!=null?e.uid:'null'})">💾 保存</button></div>`;
}
function wbSelect(uid){WB.sel=uid;const e=WB.entries.find(x=>x.uid===uid);
  document.querySelectorAll('.wb .entry').forEach(n=>n.classList.remove('on'));
  document.querySelectorAll('.wb .entry').forEach(n=>{if(n.getAttribute('onclick').includes('('+uid+')'))n.classList.add('on');});
  el('wbeditor').innerHTML=e?wbEditor(e):'';}
function wbNew(){WB.sel=null;el('wbeditor').innerHTML=wbEditor({name:'',keys:[],content:'',position:0,order:100,constant:false});}
async function wbSave(uid){const entry={
  name:el('wb_name').value.trim(),
  keys:el('wb_keys').value.split(/[,，]/).map(s=>s.trim()).filter(Boolean),
  content:el('wb_content').value,
  position:parseInt(el('wb_pos').value),
  order:parseInt(el('wb_order').value)||100,
  constant:el('wb_const').classList.contains('on'),
  case_sensitive:el('wb_cs').classList.contains('on'),
  depth:4};
  if(!entry.name){toast('给条目起个名',true);return;}
  if(!entry.keys.length&&!entry.constant){toast('加关键词，或设为常驻',true);return;}
  try{const r=await post('/worldbook/save',{world:WB.wid,uid:uid===null?undefined:uid,entry});
    WB.entries=r.entries;WB.sel=r.uid;const wname=(OV.worlds.find(w=>w.id===WB.wid)||{}).name;renderWorldbook(wname);toast('✓ 已保存');}catch(e){toast('✗ '+e.message,true)}}
async function wbDelete(uid){if(!confirm('删除这条世界书条目？'))return;
  try{const r=await post('/worldbook/delete',{world:WB.wid,uid});WB.entries=r.entries;WB.sel=(r.entries[0]||{}).uid;
    const wname=(OV.worlds.find(w=>w.id===WB.wid)||{}).name;renderWorldbook(wname);toast('✓ 已删');}catch(e){toast('✗ '+e.message,true)}}


/* —— 暴露到全局命名空间（内联 onclick + 跨模块裸引用）—— */
Object.assign(window, { viewWorldbook, renderWorldbook, wbEditor, wbSelect, wbNew, wbSave, wbDelete });
