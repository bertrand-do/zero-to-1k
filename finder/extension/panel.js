// Zero to 1k panel. Runs as the Chrome/Comet side panel AND as the web page served by the finder.
const IN_EXT=!!(window.chrome&&chrome.tabs&&chrome.tabs.update);
const API=location.protocol.startsWith('http')?'':'http://127.0.0.1:5191';
const store={get:(keys,cb)=>{if(IN_EXT&&chrome.storage)return chrome.storage.local.get(keys,cb);const o={};keys.forEach(k=>{try{const v=localStorage.getItem('xr_'+k);if(v!=null)o[k]=JSON.parse(v)}catch(e){}});cb(o)},
             set:o=>{if(IN_EXT&&chrome.storage)return chrome.storage.local.set(o);for(const k in o){try{localStorage.setItem('xr_'+k,JSON.stringify(o[k]))}catch(e){}}}};
const REASONS=['no motion','off-topic','crypto / finance','politics','bot / spam','engagement bait','too big to be seen','nothing to add'];
const PURPOSE={rising:'Posts climbing fast right now. Reply early to borrow their audience.',
               mutuals:'Who you owe: people who commented on your posts (green) or answered your replies (grey) in the last 48h, most recent first. Real mutuals (you follow each other) first, then ⭐ regulars (commented on 5+ days this month). Once you reply on their post they drop off until they comment again.',
               followers:'What your followers just posted. Show up for people who showed up for you.',
               following:'What the people you follow just posted. Stay on their radar so they notice you back.',
               connect:'Real builders who just said hi on connect threads.',
               watched:'Big accounts you watch. Checked every 30s, you get a Mac ping the minute they post.',
               trending:'Terms and tools suddenly showing up across AI and founder posts. Checked every 30 min, no pings.',
               cleanup:'People you follow who don\'t follow you back. Silent unfollowers first (they followed you before), then small accounts, then big ones you probably want to keep. Read-only: open a profile and unfollow on X yourself.',
               memes:'Your meme library. Cmd+V to save an image, a GIF file or a GIF link (Giphy, Tenor), tag it, click a meme to copy it, then paste it in your reply. ← → cycles tags.'};
const SLOW={mutuals:'takes 3 to 5 min, keep replying meanwhile',cleanup:'takes a couple of min'};   // tabs whose Fetch pages through a lot of X data
let FSTART=0,TAB='mutuals',TOPIC='all',TOPICS=[],DATA=null,POLL=null,MTAG='all',MEMES={items:[],tags:[]};
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
  if(TAB==='memes'){renderMemeChips();return}
  $('#topics').innerHTML=TAB!=='rising'?'':[{id:'all',label:'All'}].concat(TOPICS).map(t=>`<button data-topic="${t.id}" class="${t.id===TOPIC?'on':''}">${esc(t.label)}</button>`).join('')+`<button class="add" id="addTopic">+ Topic</button>`;
  $('#topics').querySelectorAll('[data-topic]').forEach(b=>b.onclick=()=>{TOPIC=b.dataset.topic;store.set({topic:TOPIC});renderHeader();closeFilters();load()});
  const add=$('#addTopic');if(add)add.onclick=async()=>{const name=prompt('Name the new topic (you can add keywords next)');if(!name)return;
    const r=await api('/api/topic?add='+encodeURIComponent(name)).catch(()=>null);if(r&&r.id){TOPICS=await api('/api/topics');TOPIC=r.id;store.set({topic:TOPIC});renderHeader();openFilters()}};
}
async function refreshCounts(){try{const c=await api('/api/counts');for(const t of ['rising','mutuals','followers','following','connect','watched','trending','cleanup','memes']){const el=$('#c-'+t);if(el)el.textContent=c[t]?c[t]:''}}catch(e){}}

// ---------- list ----------
async function load(){
  if(TAB==='memes')return loadMemes();
  try{DATA=await api('/api/items?tab='+key());$('#offline').hidden=true}
  catch(e){$('#offline').hidden=false;$('#list').hidden=true;$('#filters').hidden=true;$('#status').textContent='offline';return}
  if($('#filters').hidden)$('#list').hidden=false;
  render();setStatus();refreshCounts();
  clearTimeout(POLL);if(DATA.busy)POLL=setTimeout(load,2000);else if(TAB==='watched'||TAB==='trending')POLL=setTimeout(load,10000);
}
function setStatus(){
  $('#fetch').hidden=TAB==='watched'||TAB==='trending'||TAB==='memes';
  $('#clear').hidden=$('#gear').hidden=TAB==='memes';
  if(TAB==='memes'){const n=MEMES.items.length;$('#status').textContent=n?`${n} meme${n>1?'s':''} · Cmd+V to add`:'Cmd+V to add your first meme';return}
  if(TAB==='trending'){$('#status').textContent=RUNNING===false?`Paused${DATA.last?' · last check '+ago(DATA.last):''}`:DATA.err?'Check failed, retrying…':(DATA.last?`Live · checked ${ago(DATA.last)}`:'Starting…');return}
  if(TAB==='watched'){$('#status').textContent=RUNNING===false?`Paused${DATA.last?' · last check '+ago(DATA.last):''}`:DATA.err?'Check failed, retrying…':(DATA.last?`Live · checked ${ago(DATA.last)}`:'Starting…');return}
  if(TAB==='mutuals'){let m=$('#mstats');if(!m){m=document.createElement('div');m.id='mstats';m.className='purpose';$('#purpose').after(m)}const s=DATA.stats;m.hidden=false;m.textContent=s&&s.paybacks?`Paid back ${s.paybacks} · ${s.came_back} came back within 3 days (${Math.round(s.rate*100)}%)`:'Measuring: paybacks need 3 days before they count.'}
  else if(TAB==='cleanup'&&DATA.n_followers){let m=$('#mstats');if(!m){m=document.createElement('div');m.id='mstats';m.className='purpose';$('#purpose').after(m)}m.hidden=false;m.textContent=`Checked ${DATA.n_followers.toLocaleString()} followers vs ${DATA.n_following.toLocaleString()} you follow. The data source can miss a few followers: glance at a profile before unfollowing.`}
  else{const m=$('#mstats');if(m)m.hidden=true}
  $('#fetch').disabled=!!DATA.busy;$('#fetch').textContent=DATA.busy?'Fetching…':'Fetch';
  const n=DATA.items.filter(i=>!DATA.done[i.id]).length;
  if(!DATA.busy)FSTART=0;else if(!FSTART)FSTART=Date.now();
  $('#status').textContent=DATA.busy?(SLOW[TAB]?`Searching X… ${Math.floor((Date.now()-FSTART)/60000)} min · ${SLOW[TAB]}`:'Searching X…'):(DATA.last?`${n} new · ${ago(DATA.last)}`:'Press Fetch to start');
}
function render(){
  if(TAB==='trending')return renderTrending();
  const done=DATA.done||{},vis=DATA.items.filter(i=>done[i.id]!==-1),items=vis.filter(i=>!done[i.id]).concat(vis.filter(i=>done[i.id]));  // -1 = cleared: hidden for good
  if(!items.length){$('#list').innerHTML=`<div class="empty">${DATA.last?'Nothing passed the filters. Try again in a few minutes.':'Press Fetch to find posts.'}</div>`;return}
  if(TAB==='cleanup'){const G={silent:'Silent unfollowers · followed you before, gone now',small:'Never followed back · under 10k followers',big:'Big accounts · 10k+, probably followed on purpose, keep'};   // keep group order, done stay in place
    $('#list').innerHTML=vis.map((i,n)=>(n&&vis[n-1].group===i.group?'':`<div class="grp">${G[i.group]} <span class="count">${vis.filter(x=>x.group===i.group).length}</span></div>`)+post(i,done[i.id])).join('');return}
  $('#list').innerHTML=items.map(i=>TAB==='connect'?builder(i,done[i.id]):post(i,done[i.id])).join('');
}
function renderTrending(){
  const it=DATA.items||[];
  if(!it.length){$('#list').innerHTML='<div class="empty">Collecting the first posts. Check back in a few minutes.</div>';return}
  const note=DATA.learning?`<div class="learn">Learning baseline (needs ~${DATA.learning_hours}h). Flags switch on once there is enough history.</div>`:'';
  $('#list').innerHTML=note+it.map((r,n)=>{
    const pill=r.flag==='SPIKING'?'<span class="pill">SPIKING</span>':r.flag==='NEW'?'<span class="pill new">NEW</span>':'';
    const ratio=r.ratio!=null?` · <b>${r.ratio}x</b> usual`:(r.flag==='NEW'?' · <b>never seen before</b>':'');
    return `<details class="tc"><summary><span class="tt">${esc(r.term)}</span>${pill}<span class="meta">${r.authors} authors · ${k(r.views)} views${ratio}</span></summary>`+
      r.examples.map(e=>`<a class="ex" href="#" data-open="${esc(e.url)}"><b>@${esc(e.handle)}</b> · ${k(e.views)} views<br>${esc(e.text)}</a>`).join('')+`</details>`}).join('');
}
function post(i,d){
  const rising=TAB==='rising'||TAB==='watched',pill=TAB==='mutuals'?`<span class="pill${i.tier===2?' t2':''}">${esc(i.verdict)}</span>${i.owe?`<span class="pill owe ${i.bal>0?'pos':i.bal<0?'neg':'even'}" title="last 30 days: their comments on your posts minus your replies on theirs">${esc(i.owe)}</span>`:''}${i.mut===false?'<span class="pill nm" title="you don\'t follow each other both ways; on X replies between mutual follows rank ~4x">not mutual</span>':''}`:TAB==='cleanup'?(i.talk?`<span class="pill">commented on your posts ${i.talk}x</span>`:''):TAB==='watched'?(i.age<15?'<span class="pill">Just posted</span>':''):!rising?(i.oneway?'<span class="pill t2">one-way</span>':''):i.verdict==='WATCH'?'<span class="pill watch">Too early</span>':'<span class="pill">Climbing</span>';
  if(TAB==='cleanup')return `<div class="c ${d?'done':''}" data-id="${i.id}" data-url="${esc(i.url)}">
 <button class="chk" title="Mark done"></button><img class="av" src="${esc(i.avatar)}"><div class="body">
 <div class="hd"><b>${esc(i.name||'@'+i.handle)}</b>${pill}</div><div class="meta wrap">@${esc(i.handle)} · ${k(i.followers)} followers${i.seen?` · <b>last seen following ${new Date(i.seen+'T12:00').toLocaleDateString(undefined,{day:'numeric',month:'short'})}</b>`:''}</div>
 <div class="bio">${esc(i.text)}</div><div class="st"><span>Opens their profile</span><button class="skip">Skip</button></div></div></div>`;
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
  if(TAB==='memes')return memeClick(e);
  if(TAB==='trending'){const o=e.target.closest('[data-open]');if(o){e.preventDefault();openHere(o.dataset.open)}return}
  const c=e.target.closest('.c');if(!c||e.target.closest('.skipbox'))return;
  if(e.target.matches('.chk')){mark(c,!c.classList.contains('done'));return}
  if(e.target.matches('.skip')){openSkip(c);return}
  const o=e.target.closest('[data-open]');if(o){e.preventDefault();openHere(o.dataset.open);return}
  openHere(c.dataset.url);if(!c.classList.contains('done'))mark(c,true);
});


// ---------- memes ----------
const inInput=e=>e.target instanceof Element&&!!e.target.closest('input,textarea');
const mimg=m=>API+'/memes/'+encodeURIComponent(m.file);
async function loadMemes(){
  try{MEMES=await api('/api/memes');$('#offline').hidden=true}
  catch(e){$('#offline').hidden=false;$('#list').hidden=true;$('#status').textContent='offline';return}
  $('#list').hidden=false;if(MTAG!=='all'&&MTAG!=='untagged'&&!MEMES.tags.find(t=>t[0]===MTAG))MTAG='all';
  renderMemeChips();renderMemes();setStatus();const c=$('#c-memes');if(c)c.textContent=MEMES.items.length||'';
}
function memeTags(){const untagged=MEMES.items.filter(m=>!m.tags.length).length;
  return [['all',MEMES.items.length]].concat(MEMES.tags).concat(untagged?[['untagged',untagged]]:[])}
function renderMemeChips(){
  $('#topics').innerHTML=memeTags().map(([t,n])=>`<button data-mtag="${esc(t)}" class="${t===MTAG?'on':''}">${t==='all'?'All':t==='untagged'?'Untagged':'#'+esc(t)} <span class="count">${n}</span></button>`).join('');
  $('#topics').querySelectorAll('[data-mtag]').forEach(b=>b.onclick=()=>{MTAG=b.dataset.mtag;store.set({mtag:MTAG});renderMemeChips();renderMemes()});
}
function renderMemes(){
  const L=MEMES.items.filter(m=>MTAG==='all'||(MTAG==='untagged'?!m.tags.length:m.tags.includes(MTAG)));
  if(!L.length){$('#list').innerHTML=`<div class="empty">${MEMES.items.length?'No memes with this tag yet.':'Copy any image (right-click, Copy image), come back here and press Cmd+V.<br>You can also drop image files here.'}</div>`;return}
  $('#list').innerHTML='<div class="mgrid">'+L.map(m=>`<div class="meme" data-mid="${m.id}"><img src="${mimg(m)}" loading="lazy">
   <div class="mtags">${m.tags.map(t=>'#'+esc(t)).join(' ')||'<i>no tags</i>'}</div>
   <div class="mact"><button data-act="tag" title="Edit tags">✎</button><button data-act="del" title="Delete">×</button></div></div>`).join('')+'</div>';
}
function toast(s){const t=$('#toast');t.textContent=s;t.hidden=false;clearTimeout(toast.h);toast.h=setTimeout(()=>t.hidden=true,1800)}
async function toPng(blob){
  if(blob.type==='image/png')return blob;
  const bmp=await createImageBitmap(blob);const c=document.createElement('canvas');c.width=bmp.width;c.height=bmp.height;c.getContext('2d').drawImage(bmp,0,0);
  return await new Promise(r=>c.toBlob(r,'image/png'));
}
async function copyMeme(m){
  if(m.file.endsWith('.gif')){   // browsers can't put a GIF on the clipboard, so the finder copies the file itself (Mac only)
    const r=await api('/api/meme-clip?id='+m.id).catch(()=>null);
    if(r&&r.ok){toast('GIF copied. Cmd+V in your reply');api('/api/meme-use?id='+m.id).catch(()=>{});return}
  }
  try{const b=await (await fetch(mimg(m))).blob();const png=await toPng(b);
    await navigator.clipboard.write([new ClipboardItem({'image/png':png})]);
    toast(m.file.endsWith('.gif')?'Copied (as a still image). Cmd+V in your reply':'Copied. Cmd+V in your reply');api('/api/meme-use?id='+m.id).catch(()=>{})}
  catch(e){toast('Could not copy: click the panel first, then try again')}
}
function tagEditor(m,isNew){
  const el=document.querySelector(`.meme[data-mid="${m.id}"]`);if(!el)return;let box=el.querySelector('.mtagbox');if(box){box.remove();return}
  box=document.createElement('div');box.className='mtagbox';
  const known=MEMES.tags.map(t=>t[0]);
  box.innerHTML=`<input value="${esc(m.tags.join(', '))}" placeholder="${isNew?'Tag it: funny, shipping, monday…':'tags, comma separated'}" list="mtaglist"><datalist id="mtaglist">${known.map(t=>`<option value="${esc(t)}">`).join('')}</datalist>
   <div class="msug">${known.slice(0,10).map(t=>`<button data-sug="${esc(t)}">#${esc(t)}</button>`).join('')}</div>`;
  el.appendChild(box);const inp=box.querySelector('input');inp.focus();
  const save=async()=>{await api(`/api/meme-tags?id=${m.id}&tags=${encodeURIComponent(inp.value)}`).catch(()=>{});loadMemes()};
  inp.onkeydown=e=>{e.stopPropagation();if(e.key==='Enter')save();if(e.key==='Escape')box.remove()};
  box.querySelectorAll('[data-sug]').forEach(b=>b.onclick=ev=>{ev.stopPropagation();const cur=inp.value.split(',').map(s=>s.trim()).filter(Boolean);
    if(!cur.includes(b.dataset.sug))cur.push(b.dataset.sug);inp.value=cur.join(', ');inp.focus()});
  box.onclick=e=>e.stopPropagation();
}
function memeClick(e){
  const el=e.target.closest('.meme');if(!el)return;const m=MEMES.items.find(x=>x.id===el.dataset.mid);if(!m)return;
  const a=e.target.closest('[data-act]');
  if(a&&a.dataset.act==='tag')return tagEditor(m);
  if(a&&a.dataset.act==='del'){if(a.classList.contains('sure')){api('/api/meme-del?id='+m.id).then(loadMemes)}else{a.classList.add('sure');a.textContent='delete?';setTimeout(()=>{a.classList.remove('sure');a.textContent='×'},2500)}return}
  if(e.target.closest('.mtagbox'))return;
  copyMeme(m);
}
async function addMemeUrl(url){
  toast('Saving GIF…');const tags=(MTAG!=='all'&&MTAG!=='untagged')?[MTAG]:[];
  const m=await api('/api/meme-url',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url,tags})}).catch(()=>null);
  if(!m||m.error){toast('Could not save that link'+(m&&m.error?': '+m.error:''));return}
  await loadMemes();toast('Saved. Add tags, then Enter');tagEditor(MEMES.items.find(x=>x.id===m.id)||m,true);
}
async function addMemeBlob(blob){
  if(!blob||!blob.type.startsWith('image/'))return;
  const data=await new Promise(r=>{const f=new FileReader();f.onload=()=>r(f.result);f.readAsDataURL(blob)});
  const tags=(MTAG!=='all'&&MTAG!=='untagged')?[MTAG]:[];
  const m=await api('/api/meme',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({data,tags})}).catch(()=>null);
  if(!m){toast('Save failed: is the finder running?');return}
  await loadMemes();toast('Saved. Add tags, then Enter');tagEditor(MEMES.items.find(x=>x.id===m.id)||m,true);
}
document.addEventListener('paste',e=>{
  if(TAB!=='memes'||inInput(e))return;
  const items=[...(e.clipboardData||{}).items||[]].filter(i=>i.type.startsWith('image/'));
  const text=((e.clipboardData&&e.clipboardData.getData('text/plain'))||'').trim();
  if(!items.length&&/^https?:\/\/\S+$/.test(text)){e.preventDefault();addMemeUrl(text);return}
  if(!items.length){toast('No image on the clipboard. Copy an image, or paste a GIF link');return}
  e.preventDefault();const gif=items.find(i=>i.type==='image/gif');(gif?[gif]:items).forEach(i=>addMemeBlob(i.getAsFile()));
});
document.addEventListener('dragover',e=>{if(TAB==='memes')e.preventDefault()});
document.addEventListener('drop',e=>{if(TAB!=='memes')return;e.preventDefault();[...e.dataTransfer.files].forEach(addMemeBlob)});
document.addEventListener('keydown',e=>{
  if(TAB!=='memes'||inInput(e)||e.metaKey||e.ctrlKey)return;
  if(e.key!=='ArrowRight'&&e.key!=='ArrowLeft')return;
  const T=memeTags().map(t=>t[0]);let i=T.indexOf(MTAG);i=(i+(e.key==='ArrowRight'?1:-1)+T.length)%T.length;
  MTAG=T[i];store.set({mtag:MTAG});renderMemeChips();renderMemes();e.preventDefault();
});

// ---------- background jobs on/off ----------
let RUNNING=null;
function renderJobs(){const b=$('#jobs');if(RUNNING==null){b.hidden=true;return}b.hidden=false;
  b.classList.toggle('off',!RUNNING);b.innerHTML=RUNNING?'<span class="dot"></span>Live':'<span class="dot"></span>Paused';
  b.title=RUNNING?'Watched + Trending check X in the background. Click to pause them.':'Watched + Trending are paused (no searches, no cost). Click to start them.'}
async function loadJobs(){try{RUNNING=(await api('/api/jobs')).running}catch(e){RUNNING=null}renderJobs()}
$('#jobs').onclick=async()=>{const want=!RUNNING;RUNNING=want;renderJobs();try{RUNNING=(await api('/api/jobs?run='+(want?1:0))).running}catch(e){}renderJobs();if(TAB==='watched'||TAB==='trending')load()};
loadJobs();setInterval(loadJobs,60000);

// ---------- filters (gear) ----------
function closeFilters(){$('#filters').hidden=true;$('#list').hidden=false;$('#gear').classList.remove('on')}
async function openFilters(){
  $('#list').hidden=true;$('#filters').hidden=false;$('#gear').classList.add('on');
  if(TAB==='watched'){const w=await api('/api/items?tab=watched').catch(()=>({handles:[]}));
    $('#filters').innerHTML=`<h3>Accounts you watch</h3><div class="kchips">${(w.handles||[]).map(x=>`<span class="kchip">@${esc(x)}<button data-rmh="${esc(x)}" title="remove">×</button></span>`).join('')||'<span class="muted">No accounts yet.</span>'}</div>
     <div class="kadd"><input id="nh" placeholder="Add a handle and press Enter (e.g. sama)"></div><p class="muted" style="margin-top:10px">Only their own posts, no replies or reposts. New accounts show up on the next check.</p>`;
    $('#filters').querySelectorAll('[data-rmh]').forEach(b=>b.onclick=async()=>{await api('/api/watch?remove='+encodeURIComponent(b.dataset.rmh));openFilters()});
    $('#nh').onkeydown=async e=>{if(e.key==='Enter'&&e.target.value.trim()){await api('/api/watch?add='+encodeURIComponent(e.target.value.trim()));openFilters()}};return}
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
// replies I posted since local midnight (this computer's timezone)
async function myReplies(){const b=$('#myrep');b.textContent='💬 …';
  const d=new Date();d.setHours(0,0,0,0);
  try{const r=await api('/api/my-replies?since='+Math.floor(d/1000));b.textContent=`💬 ${r.count} today`}catch(e){b.textContent='💬 ?'}}
$('#myrep').onclick=myReplies;myReplies();setInterval(myReplies,5*60000);
store.get(['tab','topic','mtag'],async s=>{TAB=s.tab||'rising';TOPIC=s.topic||'all';MTAG=s.mtag||'all';
  try{TOPICS=await api('/api/topics')}catch(e){}
  if(TOPIC!=='all'&&!TOPICS.find(t=>t.id===TOPIC))TOPIC='all';
  renderHeader();load()});
