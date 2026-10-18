# Watched tab: checks a short list of big accounts every ~30s and pings you (Mac notification + sound) the minute one posts.
# Unlike the other tabs this one runs by itself: being first under a big post is the whole point.
import json,subprocess,time,os,threading
import config as CFG,jobs
OUT='watched.json'; SEEN='watch_seen.json'
DEFAULT={'handles':['OpenAI','sama','OpenAIDevs'],'every_sec':30,'hours':6,'sound':'Glass','replies':False}
STATE={'last':0,'busy':False,'err':''}
def cfg():
  c=dict(DEFAULT); c.update(CFG.load().get('watch') or {}); return c
def _jl(p,d):
  try: return json.load(open(p))
  except Exception: return d
def search(handles,since,replies):
  q='('+' OR '.join('from:'+h for h in handles)+f') since_time:{since} -filter:nativeretweets'+('' if replies else ' -filter:replies')
  for _ in range(3):
    r=subprocess.run(['treg','call','anyapi.x.search.posts','--method','POST','--data',json.dumps({'query':q,'limit':50,'queryType':'Latest'})],capture_output=True,text=True).stdout
    try: return json.JSONDecoder().raw_decode(r[r.index('{'):])[0]['output']['data'].get('items',[])
    except Exception: time.sleep(3)
  raise RuntimeError('search failed')
def ping_set(c):
  ph=[h.lstrip('@').lower() for h in (c.get('ping_handles') or []) if h.strip()]
  return set(ph)
def is_ping(handle,c):
  ps=ping_set(c); return (not ps) or (handle or '').lower() in ps   # no ping_handles = every watched handle pings
def notify(it,c):
  # macOS blocks pop-ups from background scripts, so the pop-up comes from the Comet extension (background.js).
  # Here we only play the chime, which always works.
  subprocess.Popen(['afplay',f"/System/Library/Sounds/{c['sound']}.aiff"])
def check():
  c=cfg(); hs=[h.lstrip('@') for h in c['handles'] if h.strip()]
  now=time.time(); since=int(now-c['hours']*3600); found={}
  for i in range(0,len(hs),18):
    for it in search(hs[i:i+18],since,c['replies']):
      if (it.get('authorUsername') or '').lower() in {h.lower() for h in hs}: found[it['id']]=it
  seen=_jl(SEEN,None); first=seen is None; seen=set(seen or [])
  for it in sorted(found.values(),key=lambda x:x['createdUtc']):
    if it['id'] in seen: continue
    seen.add(it['id'])
    if not first and now-it['createdUtc']<30*60 and is_ping(it.get('authorUsername'),c): notify(it,c)   # first run only records what's already out
  json.dump(sorted(seen)[-2000:],open(SEEN,'w'))
  items=[dict(id=it['id'],url=f"https://x.com/{it['authorUsername']}/status/{it['id']}",handle=it['authorUsername'],name=it.get('authorName') or '',avatar=it.get('authorImage') or '',
    followers=it.get('authorFollowers') or 0,age=int((now-it['createdUtc'])/60),created=it['createdUtc'],views=it.get('viewCount') or 0,replies=it.get('replyCount') or 0,likes=it.get('likeCount') or 0,
    vpm=int((it.get('viewCount') or 0)/max((now-it['createdUtc'])/60,1)),text=(it.get('text') or '')[:400],verdict='',topic='watched',ping=is_ping(it.get('authorUsername'),c)) for it in sorted(found.values(),key=lambda x:-x['createdUtc'])]
  json.dump({'built':now,'items':items[:60],'handles':hs},open(OUT,'w'))
def loop():
  while True:
    c=cfg()
    if c['handles'] and jobs.running():
      STATE['busy']=True
      try: check(); STATE['err']=''
      except Exception as e: STATE['err']=str(e); print('watch err',e,flush=True)
      STATE['busy']=False; STATE['last']=time.time()
    time.sleep(max(15,int(c['every_sec'])))
def start(): threading.Thread(target=loop,daemon=True).start()
if __name__=='__main__':
  os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data')); check()
  for i in _jl(OUT,{}).get('items',[])[:8]: print(i['age'],'m @'+i['handle'],i['views'],'|',i['text'][:70].replace('\n',' '))
