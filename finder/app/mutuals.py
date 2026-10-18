# Mutuals tab: a "who do I owe" queue. People who commented on your posts in the last 48h,
# most recent commenter first; anyone you've replied to on their own posts since then drops off until they comment again.
import json,subprocess,time,os,sys,datetime
import config as CFG,followers
def _q(d):
  t=subprocess.run(['treg','call','anyapi.x.search.posts','--method','POST','--data',json.dumps(d)],capture_output=True,text=True).stdout
  try: return json.loads(t[t.index('{'):])['output']['data']
  except Exception: return {}
def _pages(query,n):
  out={}; cur=None
  for _ in range(n):
    d={'query':query,'limit':50,'queryType':'Latest'}
    if cur: d['cursor']=cur
    x=_q(d); new=[i for i in x.get('items') or [] if i['id'] not in out]
    for i in new: out[i['id']]=i
    cur=x.get('nextCursor')
    if not new or not cur: break
  return list(out.values())
HF='mutuals_history.json'
def _hist():
  try: return json.load(open(HF)),False
  except Exception: return {'comments':{},'replies':{}},True
def _day(t): return datetime.datetime.fromtimestamp(t).date().isoformat()
def update_history(me):
  H,first=_hist(); now=time.time(); hours=168 if first else 48; since=int(now-hours*3600); cap=60 if first else 30
  # my own original posts (last 7 days): a reply whose conversation starts at one of them was made ON my post
  mine={i['id'] for i in _pages(f'from:{me} -filter:replies since_time:{int(now-7*86400)}',10)}
  for i in _pages(f'to:{me} since_time:{since}',cap):
    h=i.get('authorUsername') or ''
    if h and h.lower()!=me.lower(): H['comments'][i['id']]={'id':i['id'],'h':h.lower(),'d':h,'ts':i['createdUtc'],'on':i.get('conversationId') in mine}
  for i in _pages(f'from:{me} filter:replies since_time:{since}',cap):
    t=(i.get('text') or '').split()   # first @mention = who I answered
    H['replies'][i['id']]={'id':i['id'],'ts':i['createdUtc'],'t':t[0][1:].lower() if t and t[0].startswith('@') else '','c':i.get('conversationId'),'on':i.get('conversationId') in mine}
  cut=now-30*86400
  for k in ('comments','replies'): H[k]={a:b for a,b in H[k].items() if b['ts']>=cut}
  json.dump(H,open(HF,'w')); return H
def regulars(H,now):
  D={}
  for c in H['comments'].values():
    if c['on'] and c['ts']>=now-30*86400: D.setdefault(c['h'],set()).add(_day(c['ts']))
  return {h for h,d in D.items() if len(d)>=5}
def oneway(H,now):
  n14=now-14*86400; out={}; heard={c['h'] for c in H['comments'].values() if c['ts']>=n14}
  for r in H['replies'].values():
    if not r['on'] and r['t'] and r['ts']>=n14: out[r['t']]=out.get(r['t'],0)+1
  return sorted(h for h,n in out.items() if n>=3 and h not in heard)
def stats(H,now):
  C={}
  for c in H['comments'].values():
    if c['on']: C.setdefault(c['h'],[]).append(c['ts'])
  n=m=0
  for r in H['replies'].values():
    if r['on'] or not r['t'] or r['ts']>now-72*3600: continue
    ts=C.get(r['t'],[])
    if not any(r['ts']-48*3600<=t<r['ts'] for t in ts): continue   # a payback = I answered someone who commented on my posts in the 48h before
    n+=1; m+=any(r['ts']<t<=r['ts']+72*3600 for t in ts)
  return {'paybacks':n,'came_back':m,'rate':m/n if n else 0}
def repliers(H,hours=48):
  me=CFG.load()['handle']; now=time.time(); since=now-hours*3600; R={}
  for c in H['comments'].values():
    if c['ts']<since: continue
    r=R.setdefault(c['h'],{'h':c['d'],'post':0,'other':0,'lp':0,'lo':0,'paid':0})
    k='post' if c['on'] else 'other'; r[k]+=1; r['lp' if c['on'] else 'lo']=max(r['lp' if c['on'] else 'lo'],c['ts'])
  # green people: time of their last comment ON MY POSTS (their answers to my replies don't count); grey: their last answer
  for r in R.values(): r['last']=r['lp'] or r['lo']
  done=set()
  for r in H['replies'].values():
    if r['on']: continue
    if r['ts']>=since: done.add(r['c'])
    if r['t'] in R: R[r['t']]['paid']=max(R[r['t']]['paid'],r['ts'])
  # green: they commented on my posts after my last reply on theirs. grey: their answers always follow my reply, so
  # that is not a debt; they only come back when I haven't been on their posts for 24h (keep the conversation alive)
  for r in R.values(): r['owed']=r['paid']<r['lp'] if r['lp'] else r['paid']<now-24*3600
  return list(R.values()),done
def balance(H,now,days=30):
  # their comments on my posts minus my replies on their posts, last 30 days: >0 = I owe them
  B={}
  for c in H['comments'].values():
    if c['on'] and c['ts']>=now-days*86400: B[c['h']]=B.get(c['h'],0)+1
  for r in H['replies'].values():
    if not r['on'] and r['t'] and r['ts']>=now-days*86400: B[r['t']]=B.get(r['t'],0)-1
  return B
def owe(n): return f"you owe {n}" if n>0 else 'even' if n==0 else f"they owe you {-n}"
def ago(t):
  m=int((time.time()-t)/60)
  return f"{m}m ago" if m<60 else f"{m//60}h ago"
def label(r):
  if r['post']: return f"commented on your posts {r['post']}x · {ago(r['last'])}"
  return f"answered your reply {r['other']}x · {ago(r['last'])}"
def run(hours=48):
  fc=CFG.load()['followers']; now=time.time(); since=int(now-24*3600)   # their posts: last 24h only
  H=update_history(CFG.load()['handle']); REG=regulars(H,now); OW=oneway(H,now); ST=stats(H,now)
  json.dump({'built':now,'handles':OW},open('oneway.json','w'))
  R,done=repliers(H,hours); repaid=[r['h'] for r in R if not r['owed']]; R=[r for r in R if r['owed']]
  BAL=balance(H,now)
  for r in R: r['reg']=r['h'].lower() in REG; r['bal']=BAL.get(r['h'].lower(),0)
  N={r['h'].lower():r for r in R}
  batches=[[r['h'] for r in R[i:i+6]] for i in range(0,len(R),6)]   # small batches: one search returns max 50 posts, busy posters crowded others out
  import concurrent.futures as cf
  posts={}
  with cf.ThreadPoolExecutor(8) as ex:
    for items in ex.map(lambda b:followers.search(b,since),batches):
      for it in items:
        if it.get('isReply') or (it.get('authorUsername') or '').lower() not in N or it['id'] in done: continue
        posts[it['id']]=it
  per={}; rows=[]
  for x in sorted(posts.values(),key=lambda x:-x['createdUtc']):
    if (x.get('lang') or 'en') not in fc['languages']: continue
    h=x['authorUsername'].lower(); per[h]=per.get(h,0)+1
    if per[h]>1: continue   # one post per person (their newest), so the queue shows more people
    rows.append(x)
  # green people with no post in 24h: look back 3 days; still nothing -> a card that opens their profile
  miss=[r['h'] for r in R if r['post'] and r['h'].lower() not in per]
  with cf.ThreadPoolExecutor(8) as ex:
    for items in ex.map(lambda b:followers.search(b,int(now-72*3600)),[miss[i:i+6] for i in range(0,len(miss),6)]):
      for x in sorted(items,key=lambda x:-x['createdUtc']):
        h=(x.get('authorUsername') or '').lower()
        if x.get('isReply') or h not in N or h in per or x['id'] in done: continue
        per[h]=1; rows.append(x)
  for h in miss:
    if h.lower() not in per: rows.append({'id':'p-'+h,'authorUsername':h,'createdUtc':N[h.lower()]['lp'],'text':'No post of their own in the last 3 days. Open their profile and reply to something recent.','profile':1})
  # green (commented on my posts) before grey, regulars first within each, then post under 12h, then most recent commenter
  rows.sort(key=lambda x:(lambda r:(r['post']==0,not r['reg'],now-x['createdUtc']>12*3600,-r['last']))(N[x['authorUsername'].lower()]))
  items=[dict(id=it['id'],url=f"https://x.com/{it['authorUsername']}"+('' if it.get('profile') else f"/status/{it['id']}"),handle=it['authorUsername'],name=it.get('authorName') or '',avatar=it.get('authorImage') or '',followers=it.get('authorFollowers') or 0,age=int((now-it['createdUtc'])/60),views=it.get('viewCount') or 0,replies=it.get('replyCount') or 0,likes=it.get('likeCount') or 0,vpm=0,text=(it.get('text') or '')[:400],verdict=('⭐ ' if N[it['authorUsername'].lower()]['reg'] else '')+label(N[it['authorUsername'].lower()]),tier=1 if N[it['authorUsername'].lower()]['post'] else 2,bal=N[it['authorUsername'].lower()]['bal'],owe=owe(N[it['authorUsername'].lower()]['bal']),why='replied to you') for it in rows[:100]]
  json.dump({'built':now,'stats':ST,'items':items,'repliers':len(R),'repaid':repaid,'silent':[r['h'] for r in R if r['h'].lower() not in per or N[r['h'].lower()].get('nop')][:40]},open('mutuals.json','w'))
  print(time.strftime('%H:%M'),'history comments',len(H['comments']),'my replies',len(H['replies']),'regulars',len(REG),'oneway',len(OW),'stats',ST,flush=True)
  print(time.strftime('%H:%M'),'mutuals owed',len(R),'repaid',len(repaid),'on my posts',sum(1 for r in R if r['post']),'posts',len(items),flush=True)
  return items
if __name__=='__main__':
  os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data'))
  for i in run()[:10]: print(i['verdict'],'@'+i['handle'],i['age'],'m |',i['text'][:60].replace('\n',' '))
