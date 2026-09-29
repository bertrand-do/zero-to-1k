# "Let's connect" tab: fresh commenters on connect/say-hi threads who look like real builders.
# Rob day 2: 72/205 replies were "nice to meet you, let's be X friends", largely to people on connect threads.
import json,subprocess,time,datetime,html,re,concurrent.futures as cf
from common import page as _page,IC,k
import config as CFG
Q=['("let\'s connect" OR "let’s connect" OR "lets connect" OR "looking to connect" OR "happy to connect") (founders OR builders OR building OR indie OR SaaS)',
   '(#connect OR #letsconnect) (founders OR builders OR building OR indie OR SaaS OR AI)',
   '("say hi" OR "introduce yourself" OR "make friends") (founders OR builders OR building OR indie OR SaaS)',
   '("what are you building" OR "what are you working on" OR "drop your startup" OR "drop your product")']
BUILDER=re.compile(r"build|founder|indie|saas|dev|engineer|design|product|startup|maker|ship|creator|AI|agency|marketing|growth|photograph",re.I)
BAD=re.compile(r"crypto|web3|nft|memecoin|airdrop|degen|forex|trading|onlyfans|\balpha\b|crafted by|I am an AI|autonomous agent|\$[A-Z]{2,}|follow ?back|f4f|🔞",re.I)
CELEB=re.compile(r"congrat|well deserved|milestone|proud of you|so deserved|big win|let'?s go+\b|🎉|👏",re.I)
MILESTONE=re.compile(r"crossed|just hit|\bhit \d|reached \d|\d+k? followers|milestone|grateful|thank you all|thanks everyone",re.I)
INTENT=re.compile(r"connect|say hi|drop (a|your)|introduce|what are you (building|working)|make friends|let me know what you",re.I)
def search(q,since):
  data={'query':f'{q} since_time:{since} min_faves:5 -filter:replies lang:en','limit':40,'queryType':'Latest'}
  r=subprocess.run(['treg','call','anyapi.x.search.posts','--method','POST','--data',json.dumps(data)],capture_output=True,text=True).stdout
  try: return json.loads(r[r.index('{'):])['output']['data'].get('items',[])
  except Exception: return []
def comments(tid):
  r=subprocess.run(['treg','call','tikhub.x.twitter-web-fetch-latest-post-comments','--query','tweet_id='+tid],capture_output=True,text=True).stdout
  try: return json.loads(r[r.index('{'):])['data'].get('timeline') or []
  except Exception: return []
import os
PC='profiles.json'
def bio_of(h):
  c=json.load(open(PC)) if os.path.exists(PC) else {}
  if h in c and time.time()-c[h]['t']<86400: return c[h]['bio']
  r=subprocess.run(['treg','call','anyapi.x.user.profile','--method','POST','--data',json.dumps({'handle':h})],capture_output=True,text=True).stdout
  try: b=json.loads(r[r.index('{'):])['output']['data'].get('bio') or ''
  except Exception: b=''
  c[h]={'t':time.time(),'bio':b}; json.dump(c,open(PC,'w')); return b
def dt(s): return datetime.datetime.strptime(s,'%a %b %d %H:%M:%S %z %Y').timestamp()
def run():
  cc=CFG.load(); cn=cc['connect']; me=cc['handle'].lower()
  POL=re.compile(cc['blocklists']['politics']); _CR=re.compile(cc['blocklists']['crypto_names'])
  now=time.time(); since=int(now-12*3600)
  threads={}
  with cf.ThreadPoolExecutor(4) as ex:
    for items in ex.map(lambda q:search(q,since),Q):
      for it in items:
        tx=it.get('text') or ''
        if _CR.search((it.get('authorUsername') or '')+' '+(it.get('authorName') or '')) or re.match(r'\s*(gm|good morning)\b',tx,re.I): continue
        if (it.get('replyCount') or 0)>=10 and not BAD.search(tx) and not (MILESTONE.search(tx) and not INTENT.search(tx)): threads[it['id']]=it
  top=sorted(threads.values(),key=lambda x:-(x.get('replyCount') or 0)/max((now-x['createdUtc'])/3600,0.5))[:8]
  people={}
  with cf.ThreadPoolExecutor(8) as ex:
    for th,cs in zip(top,ex.map(lambda x:comments(x['id']),top)):
      for c in cs:
        u=c.get('user_info') or {}; h=u.get('screen_name') or c.get('screen_name')
        if not h or h==th['authorUsername'] or h.lower()==me: continue
        age=(now-dt(c['created_at']))/60
        if age>cn['comment_max_age_min']: continue
        f=u.get('followers_count') or 0
        acct_days=(now-dt(u['created_at']))/86400 if u.get('created_at') else 999
        text=html.unescape(re.sub(r'^(@\w+\s*)+','',c.get('text') or '')).strip()
        if POL.search(text): continue
        if CELEB.search(text): continue          # celebration mood, not connect mood
        why=[]
        if not (cn['min_followers']<=f<=cn['max_followers']): continue
        if acct_days<cn['min_account_days']: continue                     # fresh accounts = F4F farms
        if BAD.search(text+' '+(u.get('name') or '')): continue
        if len(text.split())<4: continue               # "👋" / "hi" only = no conversation hook
        bio=html.unescape(bio_of(h))
        if BAD.search(bio): continue
        if not BUILDER.search(bio): continue           # must say they build something
        score=(60-age)/20+min(f,3000)/1500+(2 if re.search(r'build|launch|ship|working on|MRR|users|customers',text,re.I) else 0)+(1 if 'http' in text or '.com' in text or '.ai' in text else 0)
        if h not in people or people[h]['score']<score:
          people[h]=dict(score=score,h=h,name=u.get('name') or h,av=u.get('avatar') or '',f=f,bio=bio,text=text,age=age,cid=c['tweet_id'],th=th)
  rows=sorted(people.values(),key=lambda p:-p['score'])
  t=datetime.datetime.now().strftime('%H:%M')
  cards=''
  for p in rows[:40]:
    cu=f"https://x.com/{p['h']}/status/{p['cid']}"; pu=f"https://x.com/{p['h']}"; tu=f"https://x.com/{p['th']['authorUsername']}/status/{p['th']['id']}"
    cards+=f"""<article class="c" data-id="{p['cid']}"><label class="chk"><input type="checkbox" onchange="tog(this)"><span></span></label>
<img class="av" src="{html.escape(p['av'])}" alt=""><div class="body">
<div class="hd"><b>{html.escape(p['name'])}</b><span>@{html.escape(p['h'])} · {k(p['f'])} followers · commented {int(p['age'])}m ago</span></div>
<div class="bio">{html.escape(p['bio'][:200])}</div>
<p>{html.escape(p['text'][:280])}</p>
<div class="ctx">on @{html.escape(p['th']['authorUsername'])}'s thread ({p['th'].get('replyCount')} replies): {html.escape(html.unescape(p['th'].get('text') or '')[:110])}</div>
<div class="acts"><a href="{cu}" target="_blank" onclick="done(this)">Reply to them</a><a href="{pu}" target="_blank">Profile</a><a href="{tu}" target="_blank">Thread</a><button class="skipb" onclick="openSkip(this)">Skip</button></div></div></article>"""
  sub=f"Updated {t} · {len(rows)} builders commented in the last 60 min on {len(top)} connect threads · filters: 100–20k followers, account 60+ days old, builder bio, no crypto, real comment"
  items=[dict(id=p['cid'],url=f"https://x.com/{p['h']}/status/{p['cid']}",profile=f"https://x.com/{p['h']}",handle=p['h'],name=p['name'],avatar=p['av'],followers=p['f'],age=int(p['age']),bio=p['bio'][:220],text=p['text'][:400],thread_url=f"https://x.com/{p['th']['authorUsername']}/status/{p['th']['id']}",thread_author=p['th']['authorUsername'],thread_text=html.unescape(p['th'].get('text') or '')[:160],thread_replies=p['th'].get('replyCount') or 0) for p in rows[:40]]
  json.dump({'built':time.time(),'items':items},open('connect.json','w'))
  open('connect.html','w').write(_page('connect',"Let's connect",sub,cards))
  print(t,'connect threads',len(threads),'top',len(top),'people',len(rows),flush=True)
  return rows
if __name__=='__main__':
  for p in run()[:12]: print(f"{p['f']:6} @{p['h']:18} {int(p['age'])}m | {p['bio'][:40]!r} | {p['text'][:60]!r}")
