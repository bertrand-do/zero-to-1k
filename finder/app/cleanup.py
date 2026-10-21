# Cleanup tab: people you follow who don't follow you back, silent unfollowers first. Read-only:
# it never unfollows anyone, you do that by hand on X. ~40 treg calls per Fetch (both lists, fresh).
import json,os,glob,time,datetime
import followers
SNAP='follower-snapshots'; BIG=10000
def run():
  now=time.time(); today=datetime.date.today().isoformat()
  fol=followers.follower_list('followers',fresh=True); ing=followers.follower_list('following',fresh=True)
  if not fol or not ing: print('cleanup: empty list from the provider, kept the last result',flush=True); return []   # never judge on a failed fetch
  os.makedirs(SNAP,exist_ok=True); json.dump({'t':now,'users':fol},open(f'{SNAP}/{today}-followers.json','w'))
  F={u['h'].lower() for u in fol}
  seen={}   # handle -> most recent older snapshot they appeared in
  for f in sorted(glob.glob(f'{SNAP}/*-followers.json')):
    d=os.path.basename(f)[:10]
    if d>=today: continue
    for u in json.load(open(f))['users']: seen[u['h'].lower()]=d
  talk={}
  try:
    for c in json.load(open('mutuals_history.json'))['comments'].values():
      if c.get('on') and c['ts']>=now-30*86400: talk[c['h']]=talk.get(c['h'],0)+1
  except Exception: pass
  nofb=sorted([u for u in ing if u['h'].lower() not in F],key=lambda u:-u['f'])
  grp=lambda u:'silent' if u['h'].lower() in seen else 'small' if u['f']<BIG else 'big'
  rows=[u for g in ('silent','small','big') for u in nofb if grp(u)==g]
  items=[dict(id='u-'+u['h'].lower(),url='https://x.com/'+u['h'],handle=u['h'],name=u.get('name') or '',avatar=u.get('av') or '',followers=u['f'],age=0,views=0,replies=0,likes=0,vpm=0,
    text=u.get('desc') or u.get('bio') or '',group=grp(u),seen=seen.get(u['h'].lower(),''),talk=talk.get(u['h'].lower(),0),verdict='') for u in rows]
  n={g:sum(1 for i in items if i['group']==g) for g in ('silent','small','big')}
  json.dump({'built':now,'items':items,'n_followers':len(fol),'n_following':len(ing),'groups':n},open('cleanup.json','w'))
  print(time.strftime('%H:%M'),'cleanup followers',len(fol),'following',len(ing),'not following back',len(items),n,flush=True)
  return items
if __name__=='__main__':
  os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data'))
  for i in run(): print(i['group'],'@'+i['handle'],i['followers'],i['seen'],i['talk'] or '')
