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
function assetView(cat,id){const e=null;openModal(`<h3>${esc(id)}</h3><p class="lead">分类：${esc(cat)}</p>
  <p class="note">元件详情与编辑在<a href="/legacy" target="_blank" style="color:var(--violet)"> 控制台 </a>更完整。</p>
  <div class="modal-actions"><button class="btn ghost" onclick="actDelCodex('${jsq(cat)}','${jsq(id)}')">🗑 删除</button><button class="btn" onclick="closeModal()">好</button></div>`);}


/* —— 暴露到全局命名空间（内联 onclick + 跨模块裸引用）—— */
Object.assign(window, { viewAssets, assetView });
