/* views/actions.js — 由 index.html 内联脚本按视图拆分（T1.3，纯搬运·零行为变化）。
   跨模块/内联 onclick 经 window 全局命名空间访问，保持原单一作用域语义。 */

function slug(s){return (s||'').toLowerCase().replace(/[^\w一-鿿]+/g,'-').replace(/^-+|-+$/g,'').slice(0,40)||('w'+Math.floor(performance.now()));}
async function actNewWorld(){formModal('新建作品（世界）',[
  {n:'name',label:'名字',ph:'如 夜行动物'},
  {n:'genre',label:'题材',ph:'如 都市校园 / 治愈'},
  {n:'world_md',label:'世界设定（可空，可后补）',type:'textarea',rows:4,ph:'这座城市有四百万人。凌晨三点，醒着的只有我们两个……'},
],'创建',async v=>{if(!v.name)throw new Error('起个名');
  const id=slug(v.name);await post('/world/create',{id,name:v.name,genre:v.genre,world_md:v.world_md});
  closeModal();await refresh();location.hash='#/worldbook/'+id;toast('✓ 已建《'+v.name+'》。接下来加角色（控制台）或写世界书。');},
  (OV.llm&&OV.llm.available)?{label:'✨ AI 生成设定',run:async(v,set)=>{const r=await post('/gen/world',{prompt:v.name+' '+v.genre,genre:v.genre});set('world_md',r.body||'');}}:null);}
async function actImportCard(){formModal('导入角色卡（SillyTavern）',[
  {n:'card',label:'粘贴卡 JSON（或用控制台传 PNG）',type:'textarea',rows:6,ph:'{ "name": "...", "description": "..." }'},
  {n:'world_name',label:'新世界名（留空用卡名）',ph:''},
],'导入',async v=>{if(!v.card)throw new Error('粘贴卡 JSON');
  const r=await post('/import/card',{card:v.card,target:'new',world_name:v.world_name||''});
  closeModal();await refresh();toast('✓ 已导入到新世界');location.hash='#/chat/'+(r.world||r.world_id||'');});}
async function actNewCodex(){const cats=(await api('/codex')).categories;formModal('新建元件',[
  {n:'category',label:'分类',type:'select',options:cats},
  {n:'id',label:'id（kebab-case）',ph:'如 sleepless-city'},
  {n:'summary',label:'一句话'},{n:'tags',label:'标签（逗号分隔）'},
],'创建',async v=>{await post('/codex/create',v);closeModal();route();toast('✓ 已加元件');});}
async function actSeedCodex(){try{const r=await post('/codex/seed',{});toast(`✓ 起始库：新增 ${r.added}，共 ${r.total}`);route();}catch(e){toast('✗ '+e.message,true)}}
async function actDelCodex(cat,id){if(!confirm(`删除元件 [${cat}] ${id}?`))return;try{await post('/delete/codex',{category:cat,id});closeModal();route();toast('✓ 已删');}catch(e){toast('✗ '+e.message,true)}}
async function actImportPreset(){formModal('导入 SillyTavern 预设',[{n:'name',label:'名字'},{n:'data',label:'预设 JSON',type:'textarea',rows:6}],'导入',
  async v=>{await post('/import/preset',{name:v.name,data:v.data});closeModal();route();toast('✓ 已导入预设');});}
async function actDelWorld(wid,name){if(!confirm(`删除作品「${name}」及其全部世界线/角色？并清理跨世界连接。不可撤销。`))return;
  try{await post('/delete/world',{id:wid});closeModal();await refresh();location.hash='#/works';toast('✓ 已删除');}catch(e){toast('✗ '+e.message,true)}}
async function actExtract(wid,eid,name){if(!confirm(`把 ${name} 提取/升华为跨世界的「魂」？\n她将获得跨世界不变量（声音/底线/身份记忆），从此可被召唤进别的世界。原世界的她照常存在。`))return;
  try{const r=await post('/extract',{world:wid,entity:eid});await refresh();toast(`✓ ${name} 已成魂（soul: ${esc(r.soul||r.soul_id||'')}）。现在可以「召唤进别的世界」了。`);route();}catch(e){toast('✗ '+e.message,true)}}
async function actSummonSoul(soul,name){const ids=OV.worlds.map(w=>w.id);if(!ids.length)return toast('还没有别的世界',true);
  formModal(`✦ 召唤 ${name} 降临别的世界`,[
    {n:'world',label:'目标世界',type:'select',options:ids},
    {n:'entry',label:'进入方式',type:'select',options:['本体进','换皮进']},
  ],'召唤 ✦',async v=>{const r=await post('/summon-soul',{soul,world:v.world,entry:v.entry});closeModal();await refresh();
    toast(`✦ ${name} 已降临《${v.world}》——带着记忆。`);location.hash='#/companion/'+v.world+'/'+(r.incarnation||r.as||r.entity||'');});}
function openFarewell(wid,eid){ /* reserved for direct link */ route(); }


/* —— 暴露到全局命名空间（内联 onclick + 跨模块裸引用）—— */
Object.assign(window, { slug, actNewWorld, actImportCard, actNewCodex, actSeedCodex, actDelCodex, actImportPreset, actDelWorld, actExtract, actSummonSoul, openFarewell });
