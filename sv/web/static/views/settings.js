/* views/settings.js — 由 index.html 内联脚本按视图拆分（T1.3，纯搬运·零行为变化）。
   跨模块/内联 onclick 经 window 全局命名空间访问，保持原单一作用域语义。 */

async function viewSettings(){
  loading();
  let c;try{c=await api('/config');}catch(e){app().innerHTML=`<div class="wrap"><div class="empty">${esc(e.message)}</div></div>`;return;}
  const opt=(arr,v)=>arr.map(o=>`<option ${o===v?'selected':''}>${o}</option>`).join('');
  const sec=(k)=>(c.secrets&&c.secrets[k])||{set:false};
  const keyField=(id,k,label,ph)=>{const s=sec(k);return `<div class="field"><label>${esc(label)} ${s.set?`<span style="color:var(--good)">✓ 已配${s.preview?'('+esc(s.preview)+')':''}</span> <a onclick="clearSecret('${k}')" style="color:var(--bad);cursor:pointer">清除</a>`:''}</label><input id="${id}" type="password" placeholder="${s.set?'留空 = 保持不变':esc(ph)}"></div>`;};
  app().innerHTML=`<div class="wrap">
    <div class="page-head"><h1>设置</h1></div>
    <div class="set-tabs" id="settabs" style="margin-top:18px">
      <div class="set-tab on" data-st="api" onclick="settab(this)">模型 API</div>
      <div class="set-tab" data-st="chat" onclick="settab(this)">对话 / 你</div>
      <div class="set-tab" data-st="render" onclick="settab(this)">渲染</div>
      <div class="set-tab" data-st="data" onclick="settab(this)">状态 / 数据</div>
    </div>
    <div class="set-pane on" data-st="api">
      <p class="lead">① 作为 <b>Agent skill</b> 嵌入时走宿主模型，无需配置。② <b>独立运行</b>想让网页/CLI 自己生成，在这里配 LLM。存本机 <code>sv.local.conf</code>（不入库），保存即时生效。</p>
      <div class="row2"><div class="field"><label>provider</label><select id="cf_provider">${opt(['stub','openai','anthropic','ollama'],c.provider)}</select></div>
        <div class="field"><label>model（留空用默认）</label><input id="cf_model" value="${esc(c.model)}" placeholder="claude-sonnet-4-6 / gpt-4o-mini"></div></div>
      ${keyField('cf_openai_key','OPENAI_API_KEY','OpenAI / 兼容端 Key','sk-... 或兼容端 key')}
      <div class="field"><label>OpenAI Base URL（可指 DeepSeek / 本地）</label><input id="cf_openai_base" value="${esc(c.openai_base_url)}"></div>
      ${keyField('cf_anthropic_key','ANTHROPIC_API_KEY','Anthropic Key','sk-ant-...')}
      <div class="row2"><div class="field"><label>Ollama Base URL</label><input id="cf_ollama" value="${esc(c.ollama_base_url)}"></div>
        <div class="field"><label>temperature</label><input id="cf_temp" value="${esc(c.temperature)}"></div></div>
      <div class="toolrow"><button class="btn" onclick="saveSettings()">💾 保存</button><button class="btn ghost" onclick="testLLM()">🔌 测试连接</button></div>
      <div class="packet" id="cf_test" style="display:none"></div>
    </div>
    <div class="set-pane" data-st="chat">
      <div class="field"><label>你的名字（{{user}}）</label><input id="cf_pl_name" value="${esc((c.player&&c.player.name)||'你')}"></div>
      <div class="field"><label>你的人设（可空，让角色认得你）</label><textarea id="cf_pl_persona" rows="3">${esc((c.player&&c.player.persona)||'')}</textarea></div>
      <div class="toolrow"><button class="btn" onclick="savePlayer()">💾 保存身份</button></div>
      <p class="note">流式输出、世界书触发等行为，已默认开启 / 由引擎管理。</p>
    </div>
    <div class="set-pane" data-st="render">
      <div class="row2"><div class="field"><label>render</label><select id="cf_render">${opt(['none','gitee'],c.render)}</select></div>
        <div class="field"><label>图像尺寸</label><input id="cf_imgsize" value="${esc(c.image_size)}"></div></div>
      ${keyField('cf_gitee_key','GITEE_API_KEY','Gitee AI Key','Gitee z-image key')}
      <div class="toolrow"><button class="btn" onclick="saveSettings()">💾 保存</button></div>
    </div>
    <div class="set-pane" data-st="data">
      <table class="kv">
        <tr><td>LLM</td><td>${c.llm_available?`<span style="color:var(--good)">✓ ${esc(c.provider)}${c.model?' · '+esc(c.model):''}</span>`:'✗ stub（占位）'}</td></tr>
        <tr><td>渲染</td><td>${c.render==='gitee'&&sec('GITEE_API_KEY').set?'<span style="color:var(--good)">✓ gitee</span>':'✗ 未启用'}</td></tr>
        <tr><td>向量记忆</td><td>${esc(c.embed_provider||'none')}</td></tr>
        <tr><td>自演化</td><td>${c.simulate?'on':'off'}</td></tr>
        ${(c.env_overrides&&c.env_overrides.length)?`<tr><td>环境覆盖</td><td>${esc(c.env_overrides.join(', '))}</td></tr>`:''}
      </table>
      <h3 style="margin-top:18px">数据管理</h3>
      <div class="toolrow">
        <button class="btn ghost sm" onclick="actImportCard()">⤓ 导入角色卡</button>
        <button class="btn ghost sm" onclick="actImportPreset()">⤓ 导入预设</button>
        <button class="btn ghost sm" onclick="actImportRegex()">⤓ 导入正则</button>
        <button class="btn ghost sm" onclick="actMergeWorld()">⛙ 融合世界</button>
        <button class="btn ghost sm" onclick="actUndoImport()">⮌ 撤销导入</button>
      </div>
      <p class="note" style="margin-top:8px">导出整本到 <a style="color:var(--violet)" href="#/novel">小说页</a> 点「⤓ 导出」（按世界线 md）；反思 / 质检报告也在小说页右栏。全部数据在本机 <code>universe/</code> 目录，备份 = 拷贝该目录。密钥仅存本机，网页只绑 127.0.0.1。</p>
      <h3 style="margin-top:18px">开发者</h3>
      <p class="note"><a href="/components" target="_blank" style="color:var(--violet)">🧱 创作组件库</a> —— 工艺 / 配方 / 名词库 / 大纲，定义可复用的创作原料（缺数据时引擎回退内置种子）。</p>
      <p class="note" style="margin-top:6px"><a href="/legacy" target="_blank" style="color:var(--violet)">🛠 底层控制台（legacy）</a> —— 调试 / 原语 / 组件试验台，普通创作无需进入。</p>
    </div></div>`;
}
function settab(t){document.querySelectorAll('#settabs .set-tab').forEach(x=>x.classList.remove('on'));t.classList.add('on');
  document.querySelectorAll('.set-pane').forEach(p=>p.classList.toggle('on',p.dataset.st===t.dataset.st));}
async function saveSettings(){const g=id=>{const e=el(id);return e?e.value.trim():'';};
  const body={SV_PROVIDER:g('cf_provider'),SV_MODEL:g('cf_model'),OPENAI_BASE_URL:g('cf_openai_base'),OLLAMA_BASE_URL:g('cf_ollama'),
    SV_LLM_TEMPERATURE:g('cf_temp'),SV_RENDER:g('cf_render'),SV_IMAGE_SIZE:g('cf_imgsize')};
  ['cf_openai_key:OPENAI_API_KEY','cf_anthropic_key:ANTHROPIC_API_KEY','cf_gitee_key:GITEE_API_KEY'].forEach(p=>{const[id,k]=p.split(':');const v=g(id);if(v)body[k]=v;});
  try{await post('/config',body);await refresh();renderNav('settings');toast('✓ 设置已保存，即时生效');}catch(e){toast('✗ '+e.message,true)}}
async function savePlayer(){try{await post('/player',{name:el('cf_pl_name').value.trim()||'你',persona:el('cf_pl_persona').value});toast('✓ 已保存你的身份');}catch(e){toast('✗ '+e.message,true)}}
async function clearSecret(k){if(!confirm('清除已存密钥 '+k+'?'))return;try{await post('/config',{[k]:''});await refresh();route();toast('✓ 已清除');}catch(e){toast('✗ '+e.message,true)}}
async function testLLM(){const box=el('cf_test');box.style.display='block';box.textContent='测试中…（先保存再测）';
  try{const r=await post('/llm-test',{});box.innerHTML=r.ok?`<b style="color:var(--good)">✓ ${esc(r.provider)}${r.stub?'（stub 占位）':''}</b>\n回复样本：${esc(r.sample)}`:`<b style="color:var(--bad)">✗ ${esc(r.provider)} 连接失败</b>\n${esc(r.error)}`;
  }catch(e){box.textContent='✗ '+e.message;}}


/* —— 暴露到全局命名空间（内联 onclick + 跨模块裸引用）—— */
Object.assign(window, { viewSettings, settab, saveSettings, savePlayer, clearSecret, testLLM });
