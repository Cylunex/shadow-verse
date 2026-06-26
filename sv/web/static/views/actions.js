/* views/actions.js — 由 index.html 内联脚本按视图拆分（T1.3，纯搬运·零行为变化）。
   跨模块/内联 onclick 经 window 全局命名空间访问，保持原单一作用域语义。 */

function slug(s){return (s||'').toLowerCase().replace(/[^\w一-鿿]+/g,'-').replace(/^-+|-+$/g,'').slice(0,40)||('w'+Math.floor(performance.now()));}
/* 引擎 id 铁律:必须 ASCII kebab-case(util.is_id)。中文名推断不出 id 时要求显式填。 */
function asciiSlug(s){return (s||'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'').slice(0,40);}
function isId(s){return /^[a-z0-9][a-z0-9-]*$/.test(s||'');}
async function actNewWorld(){formModal('新建作品（世界）',[
  {n:'name',label:'名字',ph:'如 夜行动物'},
  {n:'id',label:'id（英文 kebab-case，留空按名字推断；中文名请填）',ph:'如 ye-xing-dong-wu'},
  {n:'genre',label:'题材',ph:'如 都市校园 / 治愈'},
  {n:'world_md',label:'世界设定（可空，可后补）',type:'textarea',rows:4,ph:'这座城市有四百万人。凌晨三点，醒着的只有我们两个……'},
],'创建',async v=>{if(!v.name)throw new Error('起个名');
  const id=v.id||asciiSlug(v.name);
  if(!isId(id))throw new Error('id 需为英文 kebab-case（小写字母/数字/连字符）；中文名请手动填一个 id');
  await post('/world/create',{id,name:v.name,genre:v.genre,world_md:v.world_md});
  closeModal();await refresh();location.hash='#/chat/'+id;toast('✓ 已建《'+v.name+'》。先给她加个角色吧。');},
  (OV.llm&&OV.llm.available)?{label:'✨ AI 生成设定',run:async(v,set)=>{const r=await post('/gen/world',{prompt:v.name+' '+v.genre,genre:v.genre});set('world_md',r.body||'');}}:null);}
async function actNewEntity(wid){
  const ids=OV.worlds.map(w=>w.id);
  if(!wid&&!ids.length)return toast('先建一个作品',true);
  const fields=[];
  if(!wid)fields.push({n:'world',label:'所属作品',type:'select',options:ids});
  fields.push(
    {n:'name',label:'名字',ph:'如 苏栀'},
    {n:'id',label:'id（英文 kebab-case，留空按名字推断；中文名请填）',ph:'如 su-zhi'},
    {n:'role',label:'戏份',type:'select',options:['main','secondary','cameo','npc'],value:'secondary'},
    {n:'appearance',label:'外貌锚点（英文打底，保持立绘是同一人，可空）',ph:'1girl, black hair, calm eyes …'},
    {n:'profile_md',label:'角色设定（可空，可后补）',type:'textarea',rows:5,ph:'身份 / Identity Core / 声音指纹 / 核心欲望与底线 …'},
  );
  formModal('新建角色',fields,'创建',async v=>{
    const w=wid||v.world;if(!w)throw new Error('选个作品');if(!v.name)throw new Error('起个名');
    const id=v.id||asciiSlug(v.name);
    if(!isId(id))throw new Error('id 需为英文 kebab-case；中文名请手动填一个 id');
    await post('/entity/create',{world:w,id,name:v.name,role:v.role,appearance:v.appearance,profile_md:v.profile_md});
    closeModal();await refresh();location.hash='#/chat/'+w+'/'+id;toast('✓ 已建角色 '+v.name);
  },(OV.llm&&OV.llm.available)?{label:'✨ AI 生成设定',run:async(v,set)=>{const w=wid||v.world;if(!w)throw new Error('先选作品');const r=await post('/gen/entity',{world:w,prompt:v.name||v.id,role:v.role});set('profile_md',r.body||'');}}:null);
}
async function actEntityCard(wid,eid){
  const d=await api('/entity/'+wid+'/'+eid);const c=d.card||{};
  formModal(`资料 · ${esc(c.name||eid)}`,[
    {n:'name',label:'名称',value:c.name||''},
    {n:'role',label:'戏份',type:'select',options:['main','secondary','cameo','npc'],value:c.role||'secondary'},
    {n:'appearance',label:'外貌锚点（保持立绘是同一人）',value:d.appearance||c.appearance||''},
    {n:'profile_md',label:'角色设定 · profile.md',type:'textarea',rows:12,value:d.profile_md||''},
  ],'保存',async v=>{
    await post('/entity/save',{world:wid,entity:eid,name:v.name,role:v.role,appearance:v.appearance,profile_md:v.profile_md});
    closeModal();route();toast('✓ 已保存资料');
  });
}
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
async function actImportRegex(){formModal('导入 SillyTavern 正则',[
  {n:'name',label:'名字'},
  {n:'data',label:'正则 JSON（单条或数组）',type:'textarea',rows:6,ph:'[{"scriptName":"...","findRegex":"/.../","replaceString":"..."}]'},
],'导入',async v=>{if(!v.data)throw new Error('粘贴正则 JSON');await post('/import/regex',{name:v.name,data:v.data});closeModal();toast('✓ 已导入正则');});}
async function actMergeWorld(){const ids=OV.worlds.map(w=>w.id);if(ids.length<2)return toast('至少两个世界才能融合',true);
  formModal('世界融合（把「源」并入「目标」）',[
    {n:'src',label:'源世界（被并入）',type:'select',options:ids},
    {n:'dst',label:'目标世界（保留）',type:'select',options:ids},
    {n:'delete_src',label:'融合后删除源世界',type:'select',options:['是','否'],value:'是'},
  ],'融合',async v=>{if(v.src===v.dst)throw new Error('源 / 目标不能相同');
    await post('/world/merge',{src:v.src,dst:v.dst,delete_src:v.delete_src!=='否'});
    closeModal();await refresh();toast('✓ 已融合《'+v.src+'》→《'+v.dst+'》');location.hash='#/works';});}
async function actUndoImport(){const ids=OV.worlds.map(w=>w.id);if(!ids.length)return toast('还没有世界',true);
  formModal('撤销导入（把某角色回退到导入前）',[
    {n:'world',label:'世界',type:'select',options:ids},
    {n:'entity',label:'角色 id'},
  ],'撤销',async v=>{if(!v.entity)throw new Error('填角色 id');await post('/import/undo',{world:v.world,entity:v.entity});closeModal();await refresh();toast('✓ 已撤销该角色的导入');});}
function openFarewell(wid,eid){ /* reserved for direct link */ route(); }


/* —— 暴露到全局命名空间（内联 onclick + 跨模块裸引用）—— */
Object.assign(window, { slug, asciiSlug, isId, actNewWorld, actNewEntity, actEntityCard, actImportCard, actNewCodex, actSeedCodex, actDelCodex, actImportPreset, actImportRegex, actMergeWorld, actUndoImport, actDelWorld, actExtract, actSummonSoul, openFarewell });
