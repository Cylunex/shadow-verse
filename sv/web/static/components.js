/* components.js — 由 index.html 内联脚本按视图拆分（T1.3，纯搬运·零行为变化）。
   跨模块/内联 onclick 经 window 全局命名空间访问，保持原单一作用域语义。 */

/* genre → cover + sigil */
function coverClass(g){g=g||'';
  if(/赛博|cyber|科幻|霓虹|未来|机甲|星际/.test(g))return'cv-cyber';
  if(/武侠|仙侠|江湖|玄幻|修真|古风|黑道|无限/.test(g))return'cv-wuxia';
  if(/治愈|日常|校园|青春|日式|恋爱|甜/.test(g))return'cv-heal';
  return'cv-night';}
function sigil(g){g=g||'';
  if(/赛博|cyber|科幻|霓虹|机甲|星际/.test(g))return'🌧️';
  if(/武侠|仙侠|江湖|玄幻|修真|无限/.test(g))return'⚔️';
  if(/都市|黑道/.test(g))return'🌃';
  if(/治愈|日常|校园|青春|日式/.test(g))return'⛩️';
  return'🌌';}
function avBg(rel,genre){return rel?`background-image:url('/img/${esc(rel)}')`:'';}

/* 关系攻略轴(镜像 sv/attrs.REL_AXES,纯展示元) */
const REL_AXES=[
  {key:'好感',color:'#ff8fb0',min:-100,max:100},
  {key:'心动',color:'#ff6b9c',min:0,max:100},
  {key:'信任',color:'#5ee0d0',min:-100,max:100},
  {key:'依赖',color:'#9b82ff',min:0,max:100},
  {key:'亲密',color:'#ffb3c8',min:0,max:100},
  {key:'默契',color:'#8fd0ff',min:0,max:100},
  {key:'安全感',color:'#7fce9f',min:0,max:100},
  {key:'心防',color:'#a8a6c8',min:0,max:100},
  {key:'占有欲',color:'#ffcd6b',min:0,max:100},
];
/* 关系 var 的真实形状是 {对象名:{好感..阶段..}} —— 剥掉外层人名层，拿到真正的攻略对象 */
function relUnwrap(val,playerName){
  if(!val||typeof val!=='object')return null;
  if(REL_AXES.some(a=>typeof val[a.key]==='number')||val['阶段'])return val; // 已是内层
  const pk=(playerName&&val[playerName])?playerName:Object.keys(val)[0];
  const inner=pk?val[pk]:null;
  return (inner&&typeof inner==='object')?inner:null;
}
function _hudIframe(html){
  const theme=getComputedStyle(document.documentElement);
  const vars=['--ink','--dim','--faint','--violet','--cyan','--gold','--surface','--surface2','--line'].map(v=>`${v}:${theme.getPropertyValue(v)||''}`).join(';');
  const body=String(html).replace(/(\d+(?:\.\d+)?)vh\b/g,'calc(var(--sv-vh) * $1)');
  const wrapped=`<!DOCTYPE html><html><head><meta charset="utf-8"><style>:root{${vars};--sv-vh:${window.innerHeight/100}px;color-scheme:dark}*{box-sizing:border-box}html,body{margin:0;overflow:hidden;background:transparent;color:var(--ink,#d8dee5);font-family:system-ui,'Segoe UI',sans-serif;font-size:14px}</style></head><body>${body}<script>(function(){var s=false;function post(){s=false;parent.postMessage({_svh:document.documentElement.scrollHeight},'*')}function h(){if(s)return;s=true;(window.requestAnimationFrame||setTimeout)(post)}if(window.ResizeObserver)new ResizeObserver(h).observe(document.body);[].forEach.call(document.images,function(im){if(!im.complete)im.addEventListener('load',h)});window.addEventListener('load',h);window.onerror=function(m){parent.postMessage({_sverr:String(m)},'*');return false};setTimeout(h,60);h()})()<\/script></body></html>`;
  return `<iframe class="hud" sandbox="allow-scripts" srcdoc="${wrapped.replace(/"/g,'&quot;')}" style="width:100%;border:0;background:transparent;display:block"></iframe>`;
}
window.addEventListener('message',ev=>{const d=ev.data;if(!d)return;
  if(typeof d._svh==='number')document.querySelectorAll('iframe.hud').forEach(f=>{if(f.contentWindow===ev.source)f.style.height=Math.min(d._svh+4,1200)+'px';});
  else if(d._sverr)console.warn('[HUD 面板脚本错误]',d._sverr);});
function closeModal(){const o=document.querySelector('.overlay');if(o)o.remove();}
function openModal(html){closeModal();const o=document.createElement('div');o.className='overlay';
  o.onclick=e=>{if(e.target===o)closeModal();};o.innerHTML='<div class="modal">'+html+'</div>';document.body.appendChild(o);return o;}
function formModal(title,fields,submitLabel,onSubmit,aux){
  const body=fields.map(f=>{
    if(f.type==='select')return `<div class="field"><label>${esc(f.label)}</label><select id="f_${f.n}">${f.options.map(o=>`<option ${o===f.value?'selected':''}>${esc(o)}</option>`).join('')}</select></div>`;
    if(f.type==='textarea')return `<div class="field"><label>${esc(f.label)}</label><textarea id="f_${f.n}" rows="${f.rows||4}" placeholder="${esc(f.ph||'')}">${esc(f.value||'')}</textarea></div>`;
    return `<div class="field"><label>${esc(f.label)}</label><input id="f_${f.n}" placeholder="${esc(f.ph||'')}" value="${esc(f.value||'')}"></div>`;
  }).join('');
  const auxBtn=aux?`<button class="btn ghost" id="m_aux" style="margin-right:auto">${esc(aux.label)}</button>`:'';
  const o=openModal(`<h3>${esc(title)}</h3>${body}<div class="err" id="m_err"></div>
    <div class="modal-actions">${auxBtn}<button class="btn ghost" onclick="closeModal()">取消</button><button class="btn" id="m_ok">${esc(submitLabel)}</button></div>`);
  const vals=()=>{const v={};fields.forEach(f=>v[f.n]=o.querySelector('#f_'+f.n).value.trim());return v;};
  const setF=(n,val)=>{const e=o.querySelector('#f_'+n);if(e)e.value=val;};
  o.querySelector('#m_ok').onclick=async()=>{try{await onSubmit(vals());}catch(e){o.querySelector('#m_err').textContent='✗ '+e.message;}};
  if(aux){const ab=o.querySelector('#m_aux');ab.onclick=async()=>{const t0=ab.textContent;ab.textContent='生成中…';ab.disabled=true;
    try{await aux.run(vals(),setF);}catch(e){o.querySelector('#m_err').textContent='✗ '+e.message;}finally{ab.textContent=t0;ab.disabled=false;}};}
  return o;
}


/* —— 暴露到全局命名空间（内联 onclick + 跨模块裸引用）—— */
Object.assign(window, { coverClass, sigil, avBg, REL_AXES, relUnwrap, _hudIframe, closeModal, openModal, formModal });
