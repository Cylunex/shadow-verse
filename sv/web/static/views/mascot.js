/* views/mascot.js — 由 index.html 内联脚本按视图拆分（T1.3，纯搬运·零行为变化）。
   跨模块/内联 onclick 经 window 全局命名空间访问，保持原单一作用域语义。 */

function updateConsole(){const box=el('kbconsole');if(!box)return;
  if(CHAT&&location.hash.startsWith('#/chat')){const tok=CHAT.tok||0;box.textContent=`⌬ ≈${tok>=1000?(tok/1000).toFixed(1)+'k':tok} tok · ${CHAT.name||''}`;}
  else box.textContent=`⌬ ${OV.worlds.length} 世界 · ${OV.nexus.entities.length} 跨世界`;}
function kbSay(html){const s=el('kbsay');if(s)s.innerHTML=html;}
function kbLine(){          // 星瞳:看时段 + 看你在哪一页,说一句应景的话
  let h=12;try{h=new Date().getHours();}catch(e){}
  const greet=h<5?'夜深了':h<11?'早安':h<13?'午安':h<18?'下午好':h<23?'晚上好':'夜深了';
  const fam=(location.hash.slice(1).split('/').filter(Boolean)[0])||'works';
  const byPage={chat:'在听呢。<b>想让谁开口？</b>',companion:'她一直在的。<b>去陪陪她？</b>',
    novel:'笔还搁着。<b>续写哪一章？</b>',works:'想进哪个世界？<b>我带你去。</b>',
    chars:'这些住在你世界里的人，<b>想见见谁？</b>',worldbook:'设定我都替你记着。<b>要翻哪条？</b>',
    assets:'素材都在架上呢。',presets:'文风的旋钮在这儿。',settings:'要调点什么？'};
  return `${greet}。${byPage[fam]||'<b>要做点什么？</b>'}`;
}
function kbGo(fam,line){kbSay(line);setTimeout(()=>{location.hash='#/'+fam;const st=el('kbstage'),mn=el('kbmini');if(st)st.classList.remove('on');if(mn)mn.style.display='';},420);}
(function(){const mini=el('kbmini'),stage=el('kbstage'),close=el('kbclose');
  mini.onclick=()=>{stage.classList.add('on');mini.style.display='none';kbSay(kbLine());updateConsole();};
  close.onclick=()=>{stage.classList.remove('on');mini.style.display='';};})();


/* —— 暴露到全局命名空间（内联 onclick + 跨模块裸引用）—— */
Object.assign(window, { updateConsole, kbSay, kbLine, kbGo });
