// Zero to 1k panel. Runs as the Chrome/Comet side panel AND as the web page served by the finder.
const IN_EXT=!!(window.chrome&&chrome.tabs&&chrome.tabs.update);
const API=location.protocol.startsWith('http')?'':'http://127.0.0.1:5191';
const store={get:(keys,cb)=>{if(IN_EXT&&chrome.storage)return chrome.storage.local.get(keys,cb);const o={};keys.forEach(k=>{try{const v=localStorage.getItem('xr_'+k);if(v!=null)o[k]=JSON.parse(v)}catch(e){}});cb(o)},
             set:o=>{if(IN_EXT&&chrome.storage)return chrome.storage.local.set(o);for(const k in o){try{localStorage.setItem('xr_'+k,JSON.stringify(o[k]))}catch(e){}}}};
const REASONS=['no motion','off-topic','crypto / finance','politics','bot / spam','engagement bait','too big to be seen','nothing to add'];
const PURPOSE={rising:'Posts climbing fast right now. Reply early to borrow their audience.',
               followers:'What your followers just posted. Show up for people who showed up for you.',
               connect:'Real builders who just said hi on connect threads.'};
let TAB='rising',TOPIC='all',TOPICS=[],DATA=null,POLL=null;
const $=s=>document.querySelector(s),esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const k=n=>n>=1e6?(n/1e6).toFixed(1).replace('.0','')+'M':n>=1e3?(n/1e3).toFixed(1).replace('.0','')+'k':String(n);
const mins=m=>m<60?m+' min':m<1440?Math.floor(m/60)+'h':Math.floor(m/1440)+'d';
const ago=ts=>{const m=Math.round((Date.now()/1000-ts)/60);return m<1?'just now':m<60?m+' min ago':Math.floor(m/60)+'h '+(m%60)+'m ago'};
const key=()=>TAB==='rising'?TOPIC:TAB;
async function api(p,opt){const r=await fetch(API+p,opt);if(!r.ok)throw new Error(r.status);return r.json()}

// open a post in the tab beside the panel (extension) or a new tab (web)
async function openHere(url){
  if(!IN_EXT){window.open(url,'_blank');return}
  let win=null;try{win=await chrome.windows.getLastFocused({windowTypes:['normal']})}catch(e){}
  const [tab]=await chrome.tabs.query(win?{active:true,windowId:win.id}:{active:true,lastFocusedWindow:true});
  if(tab&&tab.id!=null){chrome.tabs.update(tab.id,{url});if(win)chrome.windows.update(win.id,{focused:true}).catch(()=>{})}else chrome.tabs.create({url});
}

// ---------- header ----------
function renderHeader(){
  document.querySelectorAll('#tabs button').forEach(b=>b.classList.toggle('on',b.dataset.tab===TAB));
  $('#purpose').textContent=PURPOSE[TAB];
  $('#topics').innerHTML=TAB!=='rising'?'':[{id:'all',label:'All'}].concat(TOPICS).map(t=>`<button data-topic="${t.id}" class="${t.id===TOPIC?'on':''}">${esc(t.label)}</button>`).join('')+`<button class="add" id="addTopic">+ Topic</button>`;
  $('#topics').querySelectorAll('[data-topic]').forEach(b=>b.onclick=()=>{TOPIC=b.dataset.topic;store.set({topic:TOPIC});renderHeader();closeFilters();load()});
  const add=$('#addTopic');if(add)add.onclick=async()=>{const name=prompt('Name the new topic (you can add keywords next)');if(!name)return;
    const r=await api('/api/topic?add='+encodeURIComponent(name)).catch(()=>null);if(r&&r.id){TOPICS=await api('/api/topics');TOPIC=r.id;store.set({topic:TOPIC});renderHeader();openFilters()}};
}
async function refreshCounts(){try{const c=await api('/api/counts');for(const t of ['rising','followers','connect']){const el=$('#c-'+t);if(el)el.textContent=c[t]?c[t]:''}}catch(e){}}

// ---------- list ----------
async function load(){
  try{DATA=await api('/api/items?tab='+key());$('#offline').hidden=true}
  catch(e){$('#offline').hidden=false;$('#list').hidden=true;$('#filters').hidden=true;$('#status').textContent='offline';return}
  if($('#filters').hidden)$('#list').hidden=false;
  render();setStatus();refreshCounts();
  clearTimeout(POLL);if(DATA.busy)POLL=setTimeout(load,2000);
}
function setStatus(){
  $('#fetch').disabled=!!DATA.busy;$('#fetch').textContent=DATA.busy?'Fetching…':'Fetch';
  const n=DATA.items.filter(i=>!DATA.done[i.id]).length;
  $('#status').textContent=DATA.busy?'Searching X…':(DATA.last?`${n} new · ${ago(DATA.last)}`:'Press Fetch to start');
}
function render(){
  const done=DATA.done||{},vis=DATA.items.filter(i=>done[i.id]!==-1),items=vis.filter(i=>!done[i.id]).concat(vis.filter(i=>done[i.id]));  // -1 = cleared: hidden for good
  if(!items.length){$('#list').innerHTML=`<div class="empty">${DATA.last?'Nothing passed the filters. Try again in a few minutes.':'Press Fetch to find posts.'}</div>`;return}
  $('#list').innerHTML=items.map(i=>TAB==='connect'?builder(i,done[i.id]):post(i,done[i.id])).join('');
}
function post(i,d){
  const rising=TAB==='rising',pill=!rising?'':i.verdict==='WATCH'?'<span class="pill watch">Too early</span>':'<span class="pill">Climbing</span>';
  const meta=rising?`@${esc(i.handle)} · <b>${mins(i.age)}</b> · <b>+${k(i.vpm)} views/min</b> · ${k(i.followers)} followers`:`@${esc(i.handle)} · <b>${mins(i.age)} ago</b> · ${k(i.followers)} followers`;
  return `<div class="c ${d?'done':''}" data-id="${i.id}" data-topic="${esc(i.topic||'')}" data-url="${esc(i.url)}">
 <button class="chk" title="Mark done"></button><img class="av" src="${esc(i.avatar)}"><div class="body">
 <div class="hd"><b>${esc(i.name)}</b>${pill}</div><div class="meta">${meta}</div>
 <div class="txt">${esc(i.text)}</div>
 <div class="st"><span>💬 ${i.replies}</span><span>♥ ${k(i.likes)}</span><span>👁 ${k(i.views)}</span><button class="skip">Skip</button></div></div></div>`}
function builder(i,d){return `<div class="c ${d?'done':''}" data-id="${i.id}" data-url="${esc(i.url)}">
 <button class="chk" title="Mark done"></button><img class="av" src="${esc(i.avatar)}"><div class="body">
 <div class="hd"><b>${esc(i.name)}</b></div><div class="meta">@${esc(i.handle)} · ${k(i.followers)} followers · <b>said hi ${mins(i.age)} ago</b></div>
 <div class="bio">${esc(i.bio)}</div><div class="txt">${esc(i.text)}</div>
 <div class="ctx">on @${esc(i.thread_author)}'s thread: ${esc(i.thread_text)}</div>
 <div class="st"><a href="#" data-open="${esc(i.profile)}">Profile</a><a href="#" data-open="${esc(i.thread_url)}">Thread</a><button class="skip">Skip</button></div></div></div>`}
const tabOf=c=>(TAB==='rising'&&c.dataset.topic)?c.dataset.topic:key();
function mark(c,on){const id=c.dataset.id;DATA.done=DATA.done||{};if(on)DATA.done[id]=1;else delete DATA.done[id];
  c.classList.toggle('done',on);setStatus();api(`/api/mark?tab=${tabOf(c)}&id=${id}&on=${on?1:0}`).then(refreshCounts).catch(()=>{})}
function openSkip(c){let b=c.querySelector('.skipbox');if(b){b.remove();return}
  b=document.createElement('div');b.className='skipbox';
  b.innerHTML='<div class="reasons">'+REASONS.map(x=>`<button>${x}</button>`).join('')+'</div><input placeholder="Why skip? Enter to save">';
  c.querySelector('.body').appendChild(b);b.querySelector('input').focus();
  b.addEventListener('click',e=>{e.stopPropagation();if(e.target.matches('.reasons button'))skip(c,e.target.textContent)});
  b.querySelector('input').addEventListener('keydown',e=>{if(e.key==='Enter')skip(c,e.target.value.trim()||'no reason')});}
function skip(c,reason){const i=DATA.items.find(x=>x.id===c.dataset.id)||{};
  api('/api/skip',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tab:tabOf(c),id:i.id,reason,author:'@'+i.handle,name:i.name,text:i.text,bio:i.bio||'',stats:`${i.replies||0}r ${i.likes||0}l ${i.views||0}v ${i.vpm||''}/min age ${i.age}m followers ${i.followers}`,thread:i.thread_text||'',pill:i.verdict||''})}).then(refreshCounts).catch(()=>{});
  DATA.done[i.id]=1;DATA.items=DATA.items.filter(x=>x.id!==i.id);c.remove();setStatus()}
$('#list').addEventListener('click',e=>{
  const c=e.target.closest('.c');if(!c||e.target.closest('.skipbox'))return;
  if(e.target.matches('.chk')){mark(c,!c.classList.contains('done'));return}
  if(e.target.matches('.skip')){openSkip(c);return}
  const o=e.target.closest('[data-open]');if(o){e.preventDefault();openHere(o.dataset.open);return}
  openHere(c.dataset.url);if(!c.classList.contains('done'))mark(c,true);
});

// ---------- filters (gear) ----------
function closeFilters(){$('#filters').hidden=true;$('#list').hidden=false;$('#gear').classList.remove('on')}
async function openFilters(){
  $('#list').hidden=true;$('#filters').hidden=false;$('#gear').classList.add('on');
  if(TAB==='rising'&&TOPIC==='all'){$('#filters').innerHTML='<p class="muted">Pick a topic above to see and edit its keywords and rules.</p>';return}
  const f=await api('/api/filters?tab='+key()).catch(()=>null);if(!f)return;
  if(f.note){$('#filters').innerHTML=`<h3>Settings</h3><p class="muted">${esc(f.note)}</p><pre class="muted" style="white-space:pre-wrap">${esc(JSON.stringify(f.settings,null,2))}</pre>`;return}
  $('#filters').innerHTML=`<h3>Keywords · ${esc(f.label)}</h3><div class="kchips">${f.keywords.map(x=>`<span class="kchip">${esc(x)}<button data-rm="${esc(x)}" title="remove">×</button></span>`).join('')||'<span class="muted">No keywords yet. Add a few below.</span>'}</div>
   <div class="kadd"><input id="nk" placeholder='Add a keyword and press Enter (e.g. "vibe coding")'></div>
   <h3>Rules${f.searched!=null?` <span class="muted">· last fetch kept ${f.kept} of ${f.searched}</span>`:''}</h3>
   ${f.rules.map(r=>`<div class="frule">${r.locked?'<span class="flock">always</span>':`<button class="fsw ${r.on?'on':''}" data-rule="${r.id}"></button>`}<span class="t">${esc(r.text)}</span><span class="n">${r.dropped==null?'':r.dropped+' out'}</span></div>`).join('')}
   <p class="muted" style="margin-top:10px">Changes apply on the next Fetch. Numbers (views, ratios) live in config.local.json: ask your agent.</p>`;
  $('#filters').querySelectorAll('[data-rm]').forEach(b=>b.onclick=async()=>{await api(`/api/keyword?tab=${key()}&remove=${encodeURIComponent(b.dataset.rm)}`);openFilters()});
  $('#nk').onkeydown=async e=>{if(e.key==='Enter'&&e.target.value.trim()){await api(`/api/keyword?tab=${key()}&add=${encodeURIComponent(e.target.value.trim())}`);openFilters()}};
  $('#filters').querySelectorAll('[data-rule]').forEach(b=>b.onclick=async()=>{const on=!b.classList.contains('on');b.classList.toggle('on',on);await api(`/api/rule?id=${b.dataset.rule}&on=${on?1:0}`)});
}
$('#gear').onclick=()=>$('#filters').hidden?openFilters():closeFilters();

// ---------- actions ----------
document.querySelectorAll('#tabs button').forEach(b=>b.onclick=()=>{TAB=b.dataset.tab;store.set({tab:TAB});renderHeader();closeFilters();load()});
$('#fetch').onclick=async()=>{DATA.busy=true;setStatus();await api('/api/fetch?tab='+key()).catch(()=>{});setTimeout(load,1500)};
$('#clear').onclick=()=>{DATA.items.forEach(i=>DATA.done[i.id]=-1);
  const byTab={};document.querySelectorAll('.c').forEach(c=>(byTab[tabOf(c)]=byTab[tabOf(c)]||[]).push(c.dataset.id));
  Promise.all(Object.entries(byTab).map(([t,l])=>api(`/api/mark-many?tab=${t}&ids=${l.join(',')}`))).then(refreshCounts).catch(()=>{});
  render();setStatus()};
setInterval(()=>{if(DATA&&!DATA.busy)setStatus()},30000);
store.get(['tab','topic'],async s=>{TAB=s.tab||'rising';TOPIC=s.topic||'all';
  try{TOPICS=await api('/api/topics')}catch(e){}
  if(TOPIC!=='all'&&!TOPICS.find(t=>t.id===TOPIC))TOPIC='all';
  renderHeader();load()});
