const API='http://127.0.0.1:5191';
const CHIPS=['no motion','off-topic','crypto / finance','politics','bot / spam','engagement bait','too big to be seen','nothing to add'];
let TAB='rising',DATA=null,POLL=null;
const $=s=>document.querySelector(s), esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const k=n=>n>=1e6?(n/1e6).toFixed(1).replace('.0','')+'M':n>=1e3?(n/1e3).toFixed(1).replace('.0','')+'k':String(n);
const mins=m=>m<60?m+'m ago':m<1440?Math.floor(m/60)+'h ago':Math.floor(m/1440)+'d ago';
const ago=ts=>{const m=Math.round((Date.now()/1000-ts)/60);return m<1?'just now':m<60?m+' min ago':Math.floor(m/60)+'h '+(m%60)+'m ago'};

// Open a link in the tab beside the panel (the window's active tab), not a new tab.
async function openHere(url){
  // the active tab of the last focused NORMAL browser window (works for side panel and popup fallback)
  let win=null;try{win=await chrome.windows.getLastFocused({windowTypes:['normal']})}catch(e){}
  const [tab]=await chrome.tabs.query(win?{active:true,windowId:win.id}:{active:true,lastFocusedWindow:true});
  if(tab&&tab.id!=null){chrome.tabs.update(tab.id,{url});if(win)chrome.windows.update(win.id,{focused:true}).catch(()=>{})}
  else chrome.tabs.create({url});
}
async function api(path,opt){const r=await fetch(API+path,opt);if(!r.ok)throw new Error(r.status);return r.json()}

async function load(){
  try{DATA=await api('/api/items?tab='+TAB);$('#offline').hidden=true;$('#list').hidden=false}
  catch(e){$('#offline').hidden=false;$('#list').hidden=true;$('#status').textContent='offline';return}
  render();setStatus();
  clearTimeout(POLL);if(DATA.busy)POLL=setTimeout(load,2000);
}
function setStatus(){
  $('#fetch').disabled=!!DATA.busy;$('#fetch').textContent=DATA.busy?'Fetching…':'Fetch';
  const n=DATA.items.filter(i=>!DATA.done[i.id]).length;
  $('#status').textContent=DATA.busy?'Fetching…':(DATA.last?`${n} new · fetched ${ago(DATA.last)}`:'Not fetched yet');
}
function render(){
  const hide=$('#hide').checked,done=DATA.done||{};
  const items=[...DATA.items].sort((a,b)=>(!!done[a.id])-(!!done[b.id])).filter(i=>!(hide&&done[i.id]));
  if(!items.length){$('#list').innerHTML='<div class="empty">Nothing here. Tap Fetch.</div>';return}
  $('#list').innerHTML=items.map(i=>TAB==='connect'?connect(i,done[i.id]):rising(i,done[i.id])).join('');
}
function rising(i,d){return `<div class="c ${i.verdict.toLowerCase()} ${d?'done':''}" data-id="${i.id}" data-url="${esc(i.url)}">
 <button class="chk" title="Mark done"></button><img class="av" src="${esc(i.avatar)}"><div class="body">
 <div class="hd"><b>${esc(i.name)}</b>${i.verdict?`<span class="pill">${i.verdict}</span>`:''}</div><div class="meta">@${esc(i.handle)} · <b>${mins(i.age)}</b> · ${k(i.followers)} followers</div>
 <div class="txt">${esc(i.text)}</div>
 <div class="st"><span>💬 ${i.replies}</span><span>♥ ${k(i.likes)}</span><span>👁 ${k(i.views)}</span>${TAB==='followers'?'':`<span class="fast">⚡${i.vpm}/min</span>`}<button class="skip">Skip</button></div></div></div>`}
function connect(i,d){return `<div class="c ${d?'done':''}" data-id="${i.id}" data-url="${esc(i.url)}">
 <button class="chk" title="Mark done"></button><img class="av" src="${esc(i.avatar)}"><div class="body">
 <div class="hd"><b>${esc(i.name)}</b></div><div class="meta">@${esc(i.handle)} · <b>${i.age}m ago</b> · ${k(i.followers)} followers</div>
 <div class="bio">${esc(i.bio)}</div><div class="txt">${esc(i.text)}</div>
 <div class="ctx">on @${esc(i.thread_author)} (${i.thread_replies} replies): ${esc(i.thread_text)}</div>
 <div class="st"><a href="#" data-open="${esc(i.profile)}">Profile</a><a href="#" data-open="${esc(i.thread_url)}">Thread</a><button class="skip">Skip</button></div></div></div>`}

async function mark(id,on){DATA.done=DATA.done||{};if(on)DATA.done[id]=1;else delete DATA.done[id];
  render();setStatus();api(`/api/mark?tab=${TAB}&id=${id}&on=${on?1:0}`).catch(()=>{})}
function openSkip(c){let b=c.querySelector('.skipbox');if(b){b.remove();return}
  b=document.createElement('div');b.className='skipbox';
  b.innerHTML='<div class="chips">'+CHIPS.map(x=>`<button>${x}</button>`).join('')+'</div><input placeholder="Why skip? Enter to save">';
  c.querySelector('.body').appendChild(b);b.querySelector('input').focus();
  b.addEventListener('click',e=>{e.stopPropagation();if(e.target.matches('.chips button'))skip(c,e.target.textContent)});
  b.querySelector('input').addEventListener('keydown',e=>{if(e.key==='Enter'){skip(c,e.target.value.trim()||'no reason')}});
}
function skip(c,reason){const i=DATA.items.find(x=>x.id===c.dataset.id)||{};
  api('/api/skip',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tab:TAB,id:i.id,reason,author:'@'+i.handle,name:i.name,text:i.text,bio:i.bio||'',stats:`${i.replies||0}r ${i.likes||0}l ${i.views||0}v ${i.vpm||''}/min age ${i.age}m followers ${i.followers}`,thread:i.thread_text||'',pill:i.verdict||''})}).catch(()=>{});
  DATA.done[i.id]=1;DATA.items=DATA.items.filter(x=>x.id!==i.id);render();setStatus()}

$('#list').addEventListener('click',e=>{
  const c=e.target.closest('.c');if(!c)return;
  if(e.target.closest('.skipbox'))return;
  if(e.target.matches('.chk')){mark(c.dataset.id,!c.classList.contains('done'));return}
  if(e.target.matches('.skip')){openSkip(c);return}
  const o=e.target.closest('[data-open]');if(o){e.preventDefault();openHere(o.dataset.open);return}
  openHere(c.dataset.url);if(!c.classList.contains('done'))mark(c.dataset.id,true);
});
async function buildTabs(){let tabs=[{id:'rising',label:'Frontier'},{id:'followers',label:'Followers'},{id:'connect',label:'Connect'}];
  try{tabs=await api('/api/tabs')}catch(e){}
  $('#tabs').innerHTML=tabs.map(x=>`<button data-tab="${x.id}" class="${x.id===TAB?'on':''}">${esc(x.label.split(' ')[0])}</button>`).join('');
  document.querySelectorAll('.tabs button').forEach(b=>b.addEventListener('click',()=>{
    document.querySelectorAll('.tabs button').forEach(x=>x.classList.toggle('on',x===b));TAB=b.dataset.tab;
    chrome.storage.local.set({tab:TAB});showList();load()}));}
function showList(){$('#filters').hidden=true;$('#list').hidden=false;$('#filtersBtn').textContent='Filters'}
async function showFilters(){const f=await api('/api/filters?tab='+TAB).catch(()=>null);if(!f)return;
  $('#list').hidden=true;$('#filters').hidden=false;$('#filtersBtn').textContent='← Posts';
  if(f.note){$('#filters').innerHTML=`<p class="muted">${esc(f.note)}</p>`;return}
  $('#filters').innerHTML=`<h3>Keywords</h3><div class="kchips">${f.keywords.map(k=>`<span class="kchip">${esc(k)}<button data-rm="${esc(k)}">×</button></span>`).join('')}</div>
   <div class="kadd"><input id="nk" placeholder="add keyword, Enter"></div>
   <h3>Rules ${f.searched!=null?`<span class="muted">· ${f.kept} kept of ${f.searched}</span>`:''}</h3>
   ${f.rules.map(r=>`<div class="frule">${r.locked?'<span class="flock">always</span>':`<button class="fsw ${r.on?'on':''}" data-rule="${r.id}"></button>`}<span class="t">${esc(r.text)}</span><span class="n">${r.dropped==null?'':r.dropped+' out'}</span></div>`).join('')}
   <p class="muted" style="margin-top:10px">Changes apply on the next Fetch. Numbers live in config.local.json.</p>`;
  $('#filters').querySelectorAll('[data-rm]').forEach(b=>b.onclick=async()=>{await api(`/api/keyword?tab=${TAB}&remove=${encodeURIComponent(b.dataset.rm)}`);showFilters()});
  $('#nk').onkeydown=async e=>{if(e.key==='Enter'&&e.target.value.trim()){await api(`/api/keyword?tab=${TAB}&add=${encodeURIComponent(e.target.value.trim())}`);showFilters()}};
  $('#filters').querySelectorAll('[data-rule]').forEach(b=>b.onclick=async()=>{const on=!b.classList.contains('on');b.classList.toggle('on',on);await api(`/api/rule?id=${b.dataset.rule}&on=${on?1:0}`)});}
$('#filtersBtn').addEventListener('click',()=>{$('#filters').hidden?showFilters():showList()});
$('#fetch').addEventListener('click',async()=>{DATA.busy=true;setStatus();await api('/api/fetch?tab='+TAB).catch(()=>{});setTimeout(load,1500)});
$('#hide').addEventListener('change',()=>{chrome.storage.local.set({hide:$('#hide').checked});render()});
$('#clear').addEventListener('click',()=>{const ids=DATA.items.map(i=>i.id);ids.forEach(id=>DATA.done[id]=1);
  api(`/api/mark-many?tab=${TAB}&ids=${ids.join(',')}`).catch(()=>{});$('#hide').checked=true;chrome.storage.local.set({hide:true});render();setStatus()});
setInterval(()=>{if(DATA&&!DATA.busy)setStatus()},30000);
chrome.storage.local.get(['tab','hide'],async s=>{if(s.tab)TAB=s.tab;await buildTabs();$('#hide').checked=!!s.hide;load()});
