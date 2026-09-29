# Rising posts: fresh posts on your keywords that are climbing fast enough to be worth a reply.
# Every rule and threshold comes from config (see docs/FRAMEWORK.md for the evidence behind each).
import json,subprocess,time,datetime,html,concurrent.futures as cf,os,re,statistics as st
import config as CFG
ACACHE='authors.json'
RULE_TEXT={
 'too_old':'Older than {max_age_min} min',
 'too_few_views':'Not enough views yet ({watch_min_views}+ under 15 min, {go_min_views}+ after)',
 'author_size':'Author has under {min_author_followers} followers',
 'flop':'Flopping for its account size (views < {flop_pct}% of followers, accounts {flop_min_followers}+)',
 'motion':'No motion (likes < {motion_pct}% of views and < {motion_min_replies} replies)',
 'author_history':'Author\'s last 5 posts get under {author_min_median_replies} replies',
 'like_pod':'Like-pod pattern ({likepod_min_likes}+ likes, 0 replies)',
 'politics':'Politics or religion',
 'finance':'Tickers / trading talk',
 'crypto_names':'Crypto account name',
 'grok_summons':'Summons @grok ("@grok is this true")',
 'spam':'Hashtag or emoji spam',
}
def rule_labels(c):
  r=dict(c['rules']); r['flop_pct']=round(r['flop_views_ratio']*100,1); r['motion_pct']=round(r['motion_like_ratio']*100,1)
  return {k:v.format(**r) for k,v in RULE_TEXT.items()}
def treg(endpoint,data):
  r=subprocess.run(['treg','call',endpoint,'--method','POST','--data',json.dumps(data)],capture_output=True,text=True).stdout
  return json.loads(r[r.index('{'):])
def author_ok(h,c):
  cache=json.load(open(ACACHE)) if os.path.exists(ACACHE) else {}
  e=cache.get(h)
  if e and time.time()-e['t']<86400 and 'med' in e: med=e['med']
  else:
    try:
      items=treg('anyapi.x.user.posts',{'handle':h,'limit':20})['output']['data'].get('tweets') or []
      own=[x for x in items if not x.get('isReply') and (x.get('views') or 0)>=200][:5]
      med=st.median([(x.get('replies') or 0) for x in own]) if len(own)>=3 else None
    except Exception: med=None
    cache[h]={'t':time.time(),'med':med}; json.dump(cache,open(ACACHE,'w'))
  return med is None or med>=c['rules']['author_min_median_replies']
def search(q,since):
  try: return treg('anyapi.x.search.posts',{'query':f'{q} since_time:{since} min_faves:5 -filter:replies lang:en','limit':50,'queryType':'Latest'})['output']['data'].get('items',[])
  except Exception: return []
def verdict(age,views,c):
  r=c['rules']
  if age<15: return ('WATCH','too new, check again in 10 min') if views>=r['watch_min_views'] else None
  if age<r['max_age_min']: return ('GO','climbing: on track for 10k+') if views>=r['go_min_views'] else None
  return None
def run(topic='rising'):
  c=CFG.load(); r=c['rules']; on=c['rules_on']; bl={k:re.compile(v) for k,v in c['blocklists'].items()}
  KW=c['topics'][topic]['keywords']
  now=time.time(); since=int(now-r['max_age_min']*60)
  seen={}
  with cf.ThreadPoolExecutor(8) as ex:
    for items in ex.map(lambda q:search(q,since),KW):
      for it in items: seen[it['id']]=it
  drop={k:0 for k in RULE_TEXT}; rows=[]
  for it in seen.values():
    age=(now-it['createdUtc'])/60; v=it.get('viewCount') or 0; rp=it.get('replyCount') or 0
    lk=it.get('likeCount') or 0; f=it.get('authorFollowers') or 0; tx=it.get('text') or ''
    name=(it.get('authorName') or ''); hnd=(it.get('authorUsername') or '')
    def d(k): drop[k]+=1; return True
    if age>=r['max_age_min'] and d('too_old'): continue
    if on.get('author_size') and f<r['min_author_followers'] and d('author_size'): continue
    if on.get('flop') and f>=r['flop_min_followers'] and v<r['flop_views_ratio']*f and d('flop'): continue
    if on.get('motion') and age>=15 and lk<r['motion_like_ratio']*v and rp<r['motion_min_replies'] and d('motion'): continue
    if on.get('like_pod') and rp==0 and lk>=r['likepod_min_likes'] and age>=15 and d('like_pod'): continue
    if on.get('politics') and bl['politics'].search(tx) and d('politics'): continue
    if on.get('finance') and bl['finance'].search(tx+' '+name) and d('finance'): continue
    if on.get('crypto_names') and (bl['crypto_names'].search(hnd) or bl['crypto_names'].search(name)) and d('crypto_names'): continue
    if on.get('grok_summons') and re.search(r'@grok\b|\bask (grok|@grok)',tx,re.I) and d('grok_summons'): continue
    if on.get('spam') and (len(re.findall(r'#\w+',tx))>=3 or re.search(r'(\W)\1{5,}|(🔥|💥){4,}',tx)) and d('spam'): continue
    vd=verdict(age,v,c)
    if not vd: drop['too_few_views']+=1; continue
    rows.append((v/max(age,1),age,v,rp,it,vd))
  kept=[]
  for row in sorted(rows,key=lambda x:(x[5][0]!='GO',-x[0])):
    if on.get('author_history') and not author_ok(row[4]['authorUsername'],c): drop['author_history']+=1; continue
    kept.append(row)
  items=[dict(id=it['id'],url=f"https://x.com/{it['authorUsername']}/status/{it['id']}",handle=it['authorUsername'],name=it.get('authorName') or '',avatar=it.get('authorImage') or '',followers=it.get('authorFollowers') or 0,age=int(age),views=v,replies=rp,likes=it.get('likeCount') or 0,vpm=int(vpm),text=(it.get('text') or '')[:400],verdict=vd[0],why=vd[1]) for vpm,age,v,rp,it,vd in kept[:40]]
  labels=rule_labels(c)
  filters=dict(topic=topic,label=c['topics'][topic]['label'],keywords=KW,searched=len(seen),kept=len(items),
               rules=[dict(id=k,text=labels[k],on=on.get(k,True) if k not in ('too_old','too_few_views') else True,locked=k in ('too_old','too_few_views'),dropped=drop[k]) for k in RULE_TEXT])
  json.dump({'built':now,'items':items,'filters':filters},open(topic+'.json','w'))
  _html(topic,c,items,filters)
  print(datetime.datetime.now().strftime('%H:%M'),topic,'found',len(seen),'kept',len(items),'dropped',{k:v for k,v in drop.items() if v},flush=True)
  return items
def _html(topic,c,items,filters):
  from common import page as _page,IC,k
  cards=''
  for i in items:
    cards+=f"""<article class="c {i['verdict'].lower()}" data-id="{i['id']}"><label class="chk"><input type="checkbox" onchange="tog(this)"><span></span></label>
<img class="av" src="{html.escape(i['avatar'])}" alt=""><div class="body"><a class="lnk" href="{i['url']}" target="_blank" onclick="done(this)">
<div class="hd"><b>{html.escape(i['name'])}</b><span>@{html.escape(i['handle'])} · {i['age']}m ago · {k(i['followers'])} followers</span><em class="pill">{i['verdict']}</em></div>
<p>{html.escape(i['text'][:280])}</p>
<div class="st"><span>{IC['rep']}{i['replies']}</span><span>{IC['like']}{k(i['likes'])}</span><span>{IC['view']}{k(i['views'])}</span><span class="fast">{IC['fast']}{i['vpm']}/min</span><button class="skipb" onclick="event.preventDefault();event.stopPropagation();openSkip(this)">Skip</button></div></a></div></article>"""
  t=datetime.datetime.now().strftime('%H:%M')
  open(topic+'.html','w').write(_page(topic,filters['label'],f"Updated {t} · {len(items)} of {filters['searched']} posts passed · <a href='/filters?tab={topic}'>see filters</a>",cards))
if __name__=='__main__':
  os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data'))
  for i in run()[:10]: print(i['verdict'],i['age'],'m @'+i['handle'])
