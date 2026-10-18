# Reply counter: how many replies you posted since midnight in your PC's timezone (the panel sends that midnight).
import json,subprocess,time
import config as CFG
CACHE={}   # since -> (checked_at, count)
def count(since,max_pages=10):
  hit=CACHE.get(since)
  if hit and time.time()-hit[0]<90: return hit[1]
  q=f"from:{CFG.load()['handle']} filter:replies since_time:{since}"; ids=set(); cur=None
  for _ in range(max_pages):
    data={'query':q,'limit':50,'queryType':'Latest'}
    if cur: data['cursor']=cur
    t=subprocess.run(['treg','call','anyapi.x.search.posts','--method','POST','--data',json.dumps(data)],capture_output=True,text=True).stdout
    try: d=json.loads(t[t.index('{'):])['output']['data']
    except Exception: break
    it=[i for i in d.get('items') or [] if i.get('createdUtc',0)>=since]
    new={i['id'] for i in it}-ids; ids|=new
    cur=d.get('nextCursor')
    if not new or not cur: break
  CACHE.clear(); CACHE[since]=(time.time(),len(ids)); return len(ids)
