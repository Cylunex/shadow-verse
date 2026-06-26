/* views/chars.js — 由 index.html 内联脚本按视图拆分（T1.3，纯搬运·零行为变化）。
   跨模块/内联 onclick 经 window 全局命名空间访问，保持原单一作用域语义。 */

async function viewChars(){
  loading();
  const lists=await Promise.all(OV.worlds.map(w=>api('/world/'+w.id).then(d=>({w,ents:d.entities})).catch(()=>({w,ents:[]}))));
  const xids=new Set(OV.nexus.entities.map(e=>e.id));
  const xmap={};OV.nexus.entities.forEach(e=>xmap[e.id]=e);
  let cards=[];
  for(const {w,ents} of lists)for(const e of ents){
    const cross=xids.has(e.id);const inc=cross?(xmap[e.id].incarnations||[]):[];
    cards.push({wid:w.id,wname:w.name,genre:w.genre,...e,cross,inc});
  }
  const html=cards.map(c=>`<div class="charcard" onclick="location.hash='#/companion/${c.wid}/${c.id}'">
    ${c.cross?'<span class="xw">✦ 跨世界</span>':''}
    <div class="av ${coverClass(c.genre)}"></div>
    <h3>${esc(c.name)}</h3><div class="role">${esc(c.role||'')}</div>
    <div class="from">出自《${esc(c.wname)}》</div>
    ${c.cross&&c.inc.length?`<div class="incar">✦ 现身于 ${c.inc.map(esc).join(' · ')}</div>`:''}</div>`).join('');
  const newcard=`<div class="charcard newcard" onclick="location.hash='#/works'"><div><div style="font-size:32px">＋</div><div style="margin-top:8px;color:var(--faint)">新建角色（去作品里加）</div></div></div>`;
  app().innerHTML=`<div class="wrap">
    <div class="page-head"><h1>角色</h1><span class="sub">住在你世界里的人 —— 有的，能走出原来的世界</span></div>
    <p class="note" style="margin:8px 0 18px">点角色进入「陪伴」；带 <span style="color:var(--violet)">✦</span> 的是跨世界的魂，可被召唤进别的世界。</p>
    <div class="chars">${cards.length?html+newcard:newcard}</div></div>`;
}


/* —— 暴露到全局命名空间（内联 onclick + 跨模块裸引用）—— */
Object.assign(window, { viewChars });
