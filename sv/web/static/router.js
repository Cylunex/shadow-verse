/* router.js — 由 index.html 内联脚本按视图拆分（T1.3，纯搬运·零行为变化）。
   跨模块/内联 onclick 经 window 全局命名空间访问，保持原单一作用域语义。 */

window.OV={worlds:[],nexus:{entities:[],links:[]},codex:{count:0},genres:[],llm:{}};
async function refresh(){window.OV=await api('/overview')}
const NAV=[
  {fam:'chat',label:'对话',icon:'💬',href:'#/chat'},
  {fam:'companion',label:'陪伴',icon:'💗',href:'#/companion'},
  {fam:'novel',label:'小说',icon:'✍',href:'#/novel'},
  {fam:'works',label:'作品',icon:'🎴',href:'#/works'},
  {fam:'chars',label:'角色',icon:'👤',href:'#/chars'},
];
function renderNav(active){
  const main=NAV.map(n=>`<a href="${n.href}" data-fam="${n.fam}" class="${active===n.fam?'on':''}">${n.icon} <span class="lbl">${n.label}</span></a>`).join('');
  const resOn=['worldbook','assets','presets'].includes(active);
  const drop=`<div class="navdrop ${resOn?'on':''}"><span class="dt" onclick="this.closest('.navdrop').classList.toggle('open')">🗂 <span class="lbl">资源</span> <span style="font-size:10px;opacity:.7">▾</span></span>
    <div class="navmenu"><div class="inner">
      <a href="#/worldbook" class="${active==='worldbook'?'on':''}">📜 世界书</a>
      <a href="#/assets" class="${active==='assets'?'on':''}">🧩 素材</a>
      <a href="#/presets" class="${active==='presets'?'on':''}">🎚 预设</a>
    </div></div></div>`;
  const settings=`<a href="#/settings" data-fam="settings" class="${active==='settings'?'on':''}">⚙ <span class="lbl">设置</span></a>`;
  el('nav').innerHTML=main+drop+settings;
  const ok=OV.llm&&OV.llm.available;const pill=el('llmpill');
  pill.className='llmpill '+(ok?'ok':'no');pill.textContent=ok?('LLM ✓ '+(OV.llm.provider||'')):'LLM 未配';
  pill.style.cursor='pointer';pill.onclick=()=>location.hash='#/settings';
}
async function route(){
  const hash=location.hash.slice(1)||'/';
  const p=hash.split('/').filter(Boolean);
  const fam=(hash==='/')?'works':(p[0]||'works');
  renderNav(fam);
  try{
    if(hash==='/'||fam==='works')return viewWorks(p[1]||'gallery',p[2]);
    if(fam==='chat')return viewChat(p[1],p[2]);
    if(fam==='companion')return viewCompanion(p[1],p[2]);
    if(fam==='novel')return viewNovel(p[1],p[2]);
    if(fam==='chars')return viewChars();
    if(fam==='worldbook')return viewWorldbook(p[1]);
    if(fam==='assets')return viewAssets();
    if(fam==='presets')return viewPresets();
    if(fam==='settings')return viewSettings();
    if(fam==='farewell')return openFarewell(p[1],p[2]);
    viewWorks('gallery');
  }catch(e){app().innerHTML=`<div class="wrap"><div class="empty">✗ ${esc(e.message)}</div></div>`;}
}

/* helper: a world's primary entity id */
async function firstEntity(wid){const w=await api('/world/'+wid);
  if(!w.entities.length)return null;
  const main=w.entities.find(e=>e.role==='main')||w.entities[0];return main.id;}


/* —— 暴露到全局命名空间（内联 onclick + 跨模块裸引用）—— */
Object.assign(window, { refresh, NAV, renderNav, route, firstEntity });
