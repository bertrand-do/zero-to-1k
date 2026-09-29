import json,subprocess,time,datetime,os,concurrent.futures as cf
Q=['"opus 5.5"','claude code','"gpt-6"','astra openai','codex','"vibe coding"','"AI agents"','cursor ai','muse meta ai','"build in public"','MRR','"AI image"']
DB='tracked.json'
db=json.load(open(DB)) if os.path.exists(DB) else {}
def now(): return datetime.datetime.now(datetime.timezone.utc)
def search(q):
  r=subprocess.run(['treg','call','anyapi.x.search.posts','--method','POST','--data',json.dumps({'query':q+' -filter:replies lang:en min_faves:2','limit':30,'queryType':'Latest'})],capture_output=True,text=True).stdout
  try: return json.loads(r[r.index('{'):])['output']['data'].get('items',[])
  except Exception: return []
def detail(i):
  o=subprocess.run(['treg','call','tikhub.x.twitter-web-fetch-tweet-detail','--query','tweet_id='+i],capture_output=True,text=True).stdout
  try:
    p=json.loads(o[o.index('{'):])['data']; return i,int(p.get('views') or 0),p.get('replies'),p.get('likes')
  except Exception: return i,None,None,None
end=time.time()+8.5*3600
rnd=0
while time.time()<end:
  t=now()
  if rnd<4 and len(db)<90:  # recruit during first 2h
    with cf.ThreadPoolExecutor(6) as ex:
      for items in ex.map(search,Q):
        for it in items:
          age=(t.timestamp()-it['createdUtc'])/60
          if it['id'] not in db and age<=40 and len(db)<90:
            db[it['id']]={'created':it['createdUtc'],'author':it.get('authorUsername'),'followers':it.get('authorFollowers'),'text':(it.get('text') or '')[:120],'obs':[]}
  with cf.ThreadPoolExecutor(10) as ex:
    for i,v,rp,lk in ex.map(detail,list(db)):
      if v is not None: db[i]['obs'].append([round((t.timestamp()-db[i]['created'])/60,1),v,rp,lk])
  json.dump(db,open(DB,'w'))
  print(t.strftime('%H:%M'),'round',rnd,'tracked',len(db),flush=True)
  rnd+=1; time.sleep(1800)
print('DONE',flush=True)
