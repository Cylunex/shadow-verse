/* api.js — 由 index.html 内联脚本按视图拆分（T1.3，纯搬运·零行为变化）。
   跨模块/内联 onclick 经 window 全局命名空间访问，保持原单一作用域语义。 */

const esc=(s)=>(s==null?'':(''+s)).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
/* jsq：把值安全嵌进“双引号属性里的单引号 JS 字符串”——先做 JS 转义(\ ' 换行)，再交给 esc 做属性转义 */
const jsq=(s)=>esc(String(s==null?'':s).replace(/\\/g,'\\\\').replace(/'/g,"\\'").replace(/\r/g,'').replace(/\n/g,'\\n'));
async function api(p){const r=await fetch('/api'+p);if(!r.ok)throw new Error((await r.json().catch(()=>({}))).error||r.status);return r.json()}
async function post(p,b){const r=await fetch('/api'+p,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});
  const j=await r.json();if(!r.ok||j.ok===false)throw new Error(j.error||r.status);return j}
function toast(msg,bad){const t=document.createElement('div');t.className='toast'+(bad?' bad':'');t.textContent=msg;document.body.appendChild(t);setTimeout(()=>t.remove(),4200)}
function md(t){const lines=(t||'').split('\n');let h='',ul=false;const cu=()=>{if(ul){h+='</ul>';ul=false}};
  for(let ln of lines){
    if(/^###\s/.test(ln)){cu();h+='<h3>'+esc(ln.slice(4))+'</h3>'}
    else if(/^##\s/.test(ln)){cu();h+='<h2>'+esc(ln.slice(3))+'</h2>'}
    else if(/^#\s/.test(ln)){cu();h+='<h1>'+esc(ln.slice(2))+'</h1>'}
    else if(/^>\s?/.test(ln)){cu();h+='<blockquote>'+inl(ln.replace(/^>\s?/,''))+'</blockquote>'}
    else if(/^[-*]\s/.test(ln)){if(!ul){h+='<ul>';ul=true}h+='<li>'+inl(ln.slice(2))+'</li>'}
    else if(ln.trim()===''){cu()}
    else{cu();h+='<p>'+inl(ln)+'</p>'}}
  cu();return h}
function inl(s){return esc(s).replace(/\*\*(.+?)\*\*/g,'<b>$1</b>').replace(/`(.+?)`/g,'<code>$1</code>')}
const el=(id)=>document.getElementById(id);
const app=()=>el('app');
function loading(){app().innerHTML='<div class="loading">载入中…</div>';}


/* —— 暴露到全局命名空间（内联 onclick + 跨模块裸引用）—— */
Object.assign(window, { esc, jsq, api, post, toast, md, inl, el, app, loading });
