/* main.js — 由 index.html 内联脚本按视图拆分（T1.3，纯搬运·零行为变化）。
   跨模块/内联 onclick 经 window 全局命名空间访问，保持原单一作用域语义。 */
/* 入口：按依赖顺序加载各模块（各模块把符号挂到 window），随后启动。 */

import './api.js';
import './components.js';
import './router.js';
import './views/works.js';
import './views/chars.js';
import './views/incarnations.js';
import './views/farewell.js';
import './views/chat.js';
import './views/companion.js';
import './views/novel.js';
import './views/worldbook.js';
import './views/assets.js';
import './views/presets.js';
import './views/settings.js';
import './views/actions.js';
import './views/mascot.js';

/* ===================== boot ===================== */
document.addEventListener('click',e=>{if(!e.target.closest('.navdrop'))document.querySelectorAll('.navdrop.open').forEach(d=>d.classList.remove('open'));});
window.addEventListener('hashchange',async()=>{await route();
  // companion → chat handoff
  if(window._pendingMsg&&CHAT&&CHAT.send){const m=window._pendingMsg;window._pendingMsg=null;setTimeout(()=>CHAT.send(m),120);}
});
(async()=>{try{await refresh();}catch(e){toast('✗ 无法连接后端：'+e.message,true);}await route();})();
