import html
CSS='''
:root{--bg:#f4f4f3;--card:#fff;--ink:#0f1419;--mut:#536471;--line:#e6e6e4;--go:#16a34a;--watch:#d97706;--blue:#1d9bf0}
@media (prefers-color-scheme:dark){:root{--bg:#0b0b0b;--card:#16181c;--ink:#e7e9ea;--mut:#8b98a5;--line:#2f3336}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.45 -apple-system,BlinkMacSystemFont,"Helvetica Neue",sans-serif}
main{max-width:720px;margin:0 auto;padding:20px 16px 80px}h1{font-size:26px;margin:6px 0 0}.sub{color:var(--mut);font-size:14px;margin:6px 0 16px}
nav.tabs{display:flex;gap:6px;border-bottom:1px solid var(--line);margin-bottom:10px}nav.tabs a{padding:10px 14px;color:var(--mut);text-decoration:none;font-weight:600;border-bottom:3px solid transparent}nav.tabs a.on{color:var(--ink);border-color:var(--blue)}
nav.tabs .dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#999;margin-left:6px;vertical-align:middle}nav.tabs .dot.run{background:var(--go)}
.c{display:flex;gap:14px;background:var(--card);border:1px solid var(--line);border-radius:18px;padding:18px 20px;margin-bottom:12px;transition:opacity .2s}
.c.is-done{opacity:.38}.c.is-done p{text-decoration:line-through;text-decoration-color:var(--mut)}
.av{width:48px;height:48px;border-radius:50%;flex:none;background:var(--line);object-fit:cover}
.body{flex:1;min-width:0}.lnk{color:inherit;text-decoration:none;display:block}
.hd{display:flex;gap:6px;align-items:baseline;flex-wrap:wrap;font-size:15px}.hd span{color:var(--mut)}
.pill{margin-left:auto;font-style:normal;font-size:12px;font-weight:700;border-radius:99px;padding:2px 10px;color:#fff;background:var(--go)}.watch .pill{background:var(--watch)}
p{margin:6px 0 12px;white-space:pre-wrap;word-wrap:break-word}.bio{color:var(--mut);font-size:15px;margin:2px 0 8px}
.st{display:flex;gap:28px;color:var(--mut);font-size:15px;flex-wrap:wrap}.st span{display:flex;align-items:center;gap:6px}.st svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linejoin:round;stroke-linecap:round}.fast{color:var(--go);font-weight:600}
.ctx{font-size:14px;color:var(--mut);border-left:3px solid var(--line);padding-left:10px;margin:8px 0}
.acts{display:flex;gap:10px;margin-top:4px}.acts a{font-size:14px;font-weight:600;color:var(--blue);text-decoration:none;border:1px solid var(--line);border-radius:99px;padding:4px 12px}
.skipb{margin-left:auto;font-size:13px;font-weight:600;color:var(--mut);background:none;border:1px solid var(--line);border-radius:99px;padding:3px 12px;cursor:pointer}
.skipbox{display:none;margin-top:10px}.skipbox.on{display:block}.skipbox input{width:100%;font:inherit;font-size:16px;padding:8px 12px;border:1px solid var(--line);border-radius:10px;background:var(--bg);color:var(--ink)}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}.chips button{font:inherit;font-size:13px;border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:99px;padding:4px 10px;cursor:pointer}
.chk{flex:none;padding-top:12px;cursor:pointer}.chk input{display:none}.chk span{display:block;width:22px;height:22px;border:2px solid var(--line);border-radius:6px}.chk input:checked+span{background:var(--go);border-color:var(--go);box-shadow:inset 0 0 0 3px var(--card)}
.bar{display:flex;gap:10px;align-items:center;margin-bottom:14px;font-size:14px;color:var(--mut);flex-wrap:wrap}.bar button{font:inherit;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:8px;padding:4px 12px;cursor:pointer}
.bar button.tg{font-weight:600}.bar button.tg.go{background:var(--ink);color:var(--bg);border-color:var(--ink);padding:6px 18px}.bar button.tg:disabled{opacity:.5}
'''
JS='''
const TAB=document.body.dataset.tab,KEY='done_'+TAB;
if(location.protocol==='file:'){location.replace('http://127.0.0.1:5191/'+TAB)}
function get(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){return {}}}
function save(d){try{localStorage.setItem(KEY,JSON.stringify(d))}catch(e){}}
function mark(c,on){c.classList.toggle('is-done',on);c.querySelector('input').checked=on;const d=get();if(on)d[c.dataset.id]=1;else delete d[c.dataset.id];save(d);fetch('/api/mark?tab='+TAB+'&id='+c.dataset.id+'&on='+(on?1:0)).catch(()=>{});hideDone()}
function tog(i){mark(i.closest('.c'),i.checked)}
function done(a){mark(a.closest('.c'),true)}
function hideDone(){const h=document.getElementById('hide').checked;try{localStorage.setItem('hide_'+TAB,h?'1':'')}catch(e){}document.querySelectorAll('.c.is-done').forEach(c=>c.style.display=h?'none':'')}
function applyDone(d){document.querySelectorAll('.c').forEach(c=>{if(d[c.dataset.id]){c.classList.add('is-done');c.querySelector('input').checked=true}});const mn=document.querySelector('main');document.querySelectorAll('.c.is-done').forEach(c=>mn.appendChild(c));hideDone()}
applyDone(get());
fetch('/api/done?tab='+TAB).then(r=>r.json()).then(s=>{const d=get();for(const k in s)d[k]=1;save(d);applyDone(d)}).catch(()=>{});
try{document.getElementById('hide').checked=!!localStorage.getItem('hide_'+TAB)}catch(e){}hideDone();
let BUSY=false,LAST=+(document.body.dataset.built||0),SEEN=0;
function ago(ts){const m=Math.round((Date.now()/1000-ts)/60);return m<1?'just now':m+' min ago'}
function status(){fetch('/api/status').then(r=>r.json()).then(s=>{const me=s[TAB];
 if(SEEN&&me.last>SEEN+1){try{sessionStorage.setItem('y_'+TAB,window.scrollY)}catch(e){}location.reload();return}
 SEEN=me.last;BUSY=me.busy;const el=document.getElementById('timer'),b=document.getElementById('tg');
 if(el)el.textContent=BUSY?'Fetching…':(me.last?'Last fetch '+ago(me.last):'Not fetched yet');
 if(b){b.disabled=BUSY;b.textContent=BUSY?'Fetching…':'Fetch'}
 setTimeout(status,BUSY?2000:30000)}).catch(()=>setTimeout(status,5000))}
function fetchNow(){fetch('/api/fetch?tab='+TAB).then(()=>{BUSY=true;const b=document.getElementById('tg');if(b){b.disabled=true;b.textContent='Fetching…'};const el=document.getElementById('timer');if(el)el.textContent='Fetching…';setTimeout(status,1500)})}
function clearPage(){const ids=[...document.querySelectorAll('.c')].map(c=>c.dataset.id);const d=get();ids.forEach(i=>d[i]=1);save(d);
 document.getElementById('hide').checked=true;try{localStorage.setItem('hide_'+TAB,'1')}catch(e){}
 document.querySelectorAll('.c').forEach(c=>{c.classList.add('is-done');c.style.display='none'});
 fetch('/api/mark-many?tab='+TAB+'&ids='+ids.join(','))}
const CHIPS=['no motion','off-topic','crypto / finance','politics','bot / spam','engagement bait','too big to be seen','nothing to add'];
function openSkip(btn){const c=btn.closest('.c');let b=c.querySelector('.skipbox');
 if(!b){b=document.createElement('div');b.className='skipbox';b.innerHTML='<div class=chips>'+CHIPS.map(x=>'<button type=button>'+x+'</button>').join('')+'</div><input placeholder="Why skip? (Enter to save)" enterkeyhint="done">';
  c.querySelector('.body').appendChild(b);b.querySelectorAll('.chips button').forEach(x=>x.onclick=e=>{e.preventDefault();sendSkip(c,x.textContent)});
  b.querySelector('input').onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();sendSkip(c,e.target.value.trim()||'no reason')}}}
 b.classList.toggle('on');if(b.classList.contains('on'))b.querySelector('input').focus()}
function sendSkip(c,reason){const q=s=>(c.querySelector(s)||{}).innerText||'';
 const body={tab:TAB,id:c.dataset.id,reason,author:q('.hd span'),name:q('.hd b'),text:q('p'),bio:q('.bio'),stats:q('.st'),thread:q('.ctx'),pill:q('.pill')};
 fetch('/api/skip',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).catch(()=>{});
 const d=get();d[c.dataset.id]=1;save(d);c.style.transition='opacity .2s';c.style.opacity='0';setTimeout(()=>c.remove(),200)}
function stopAll(){fetch('/api/stop-all').finally(()=>{document.body.innerHTML='<main><h1>Finder stopped</h1><p class=sub>All tabs are off. Nice work today.</p></main>'})}
status();
try{const y=sessionStorage.getItem('y_'+TAB);if(y)window.scrollTo(0,+y)}catch(e){}

'''
IC={'rep':'<svg viewBox="0 0 24 24"><path d="M4 5h16v11H8l-4 4z"/></svg>','like':'<svg viewBox="0 0 24 24"><path d="M12 20s-7-4.5-7-10a4 4 0 0 1 7-2.5A4 4 0 0 1 19 10c0 5.5-7 10-7 10z"/></svg>','view':'<svg viewBox="0 0 24 24"><path d="M5 20V10M10 20V4M15 20v-8M20 20v-5"/></svg>','fast':'<svg viewBox="0 0 24 24"><path d="M13 3 5 14h6l-1 7 8-11h-6z"/></svg>','user':'<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 20c1.5-4 5-5 8-5s6.5 1 8 5"/></svg>'}
def k(n): return f"{n/1e6:.1f}M".replace('.0M','M') if n>=1e6 else f"{n/1000:.1f}k".replace('.0k','k') if n>=1000 else str(n)
def page(tab,title,sub,cards):
  import config as CFG
  tabs=[(k,v['label']) for k,v in CFG.load()['topics'].items()]+[('followers','Followers'),('connect',"Let's connect")]
  nav='<nav class="tabs">'+''.join(f'<a href="/{k}" class="{"on" if tab==k else ""}">{l}</a>' for k,l in tabs)+'<a href="/filters?tab='+tab+'">Filters</a></nav>'
  bar='<div class="bar"><b id="timer" style="color:var(--ink)">…</b><button id="tg" class="tg go" onclick="fetchNow()">Fetch</button><label><input type="checkbox" id="hide" onchange="hideDone()"> Hide done</label><button onclick="localStorage.removeItem(\'done_\'+document.body.dataset.tab);fetch(\'/api/clear?tab=\'+document.body.dataset.tab).finally(()=>location.reload())">Clear checks</button><button onclick="clearPage()">Clear page</button></div>'
  return f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>{CSS}</style></head><body data-tab="{tab}" data-built="{int(__import__('time').time())}"><main>{nav}<h1>{html.escape(title)}</h1><div class="sub">{sub}</div>{bar}{cards or "<p>Nothing passes right now.</p>"}</main><script>{JS}</script></body></html>'
