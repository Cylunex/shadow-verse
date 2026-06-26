/* views/assets.js — 由 index.html 内联脚本按视图拆分（T1.3，纯搬运·零行为变化）。
   跨模块/内联 onclick 经 window 全局命名空间访问，保持原单一作用域语义。 */

async function viewAssets(){
  loading();
  let d;try{d=await api('/codex');}catch(e){app().innerHTML=`<div class="wrap"><div class="empty">${esc(e.message)}</div></div>`;return;}
  const byCat={};for(const e of d.elements){(byCat[e.category]=byCat[e.category]||[]).push(e);}
  const catLabel={worlds:'世界灵感',characters:'角色原型',mechanics:'机制 / 设定',conflicts:'冲突',organizations:'势力 / 组织',scenes:'场景',themes:'母题'};
  const secs=Object.entries(byCat).map(([cat,els])=>`<div class="assetsec"><h2>${esc(catLabel[cat]||cat)} <span style="color:var(--faint);font-weight:400">${els.length}</span></h2>
    <div class="assetgrid">${els.map(e=>`<div class="asset" onclick="assetView('${jsq(cat)}','${jsq(e.id)}')"><h4>${esc(e.id)} <span class="ty">${esc(cat)}</span></h4><div class="d">${esc(e.summary||'')}</div></div>`).join('')}</div></div>`).join('');
  app().innerHTML=`<div class="wrap">
    <div class="page-head"><h1>素材库</h1><span class="sub">造世界的原料 —— 取之即用、可复用</span></div>
    <div class="toolrow"><button class="btn sm" onclick="actNewCodex()">＋ 新建元件</button>
      <button class="btn ghost sm" onclick="actSeedCodex()">🌱 填充起始库</button>
      <button class="btn ghost sm" onclick="actImportPreset()">⤓ 导入预设</button></div>
    ${secs||'<p class="empty">元件库空。点「填充起始库」灌入一批抽象创世素材。</p>'}</div>`;
}
function _codexBody(mdText){let b=(String(mdText||'').split('## 拆解')[1]||'').replace(/^[^\n]*\n/,'').trim();
  return /^<!--[\s\S]*-->$/.test(b)?'':b;}
async function assetView(cat,id){
  let e;try{e=await api('/codex/'+cat+'/'+id);}catch(err){return toast('✗ '+err.message,true);}
  const body=_codexBody(e.md);
  openModal(`<h3>${esc(id)} <span style="color:var(--faint);font-size:13px;font-weight:400">${esc(cat)}</span></h3>
    ${(e.tags&&e.tags.length)?`<div class="chips" style="margin:2px 0 8px">${e.tags.map(t=>`<span class="fchip">${esc(t)}</span>`).join('')}</div>`:''}
    <p class="lead" style="margin-top:0">${esc(e.summary||'')}</p>
    ${body?`<div class="packet" style="max-height:42vh;overflow:auto">${md(body)}</div>`:'<p class="note">还没有拆解正文。点「编辑」补上。</p>'}
    <div class="modal-actions"><button class="btn ghost" onclick="actDelCodex('${jsq(cat)}','${jsq(id)}')">🗑 删除</button><button class="btn ghost" onclick="actEditCodex('${jsq(cat)}','${jsq(id)}')">✎ 编辑</button><button class="btn" onclick="closeModal()">好</button></div>`);
}
async function actEditCodex(cat,id){
  let e;try{e=await api('/codex/'+cat+'/'+id);}catch(err){return toast('✗ '+err.message,true);}
  formModal(`编辑元件 · ${esc(id)}`,[
    {n:'summary',label:'一句话（AI摘要 / 食材说明）',type:'textarea',rows:2,value:e.summary||''},
    {n:'tags',label:'标签（逗号分隔）',value:(e.tags||[]).join(', ')},
    {n:'body',label:'拆解（为什么有效 / 结构 / 可变体）',type:'textarea',rows:8,value:_codexBody(e.md)},
  ],'保存',async v=>{
    await post('/codex/create',{category:cat,id,summary:v.summary,tags:v.tags,body:v.body});
    closeModal();route();toast('✓ 已保存元件');
  });
}


/* —— 暴露到全局命名空间（内联 onclick + 跨模块裸引用）—— */
Object.assign(window, { viewAssets, assetView, actEditCodex, _codexBody });
