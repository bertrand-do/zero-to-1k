# Followers tab: latest original posts (no replies, no reposts) from people who follow Bertrand, newest first.
import json,subprocess,time,datetime,os,html,concurrent.futures as cf
from common import page as _page,IC,k
import config as CFG
FCACHE='followers_list.json'
def follower_list():
  if os.path.exists(FCACHE):
    c=json.load(open(FCACHE))
    if time.time()-c['t']<6*3600: return c['users']
  users=[];cur=None
  for _ in range(40):
    q=['treg','call','tikhub.x.twitter-web-fetch-user-followers','--query','screen_name='+CFG.load()['handle']]+(['--query','cursor='+cur] if cur else [])
    t=subprocess.run(q,capture_output=True,text=True).stdout
    try: d=json.loads(t[t.index('{'):])['data']
    except Exception: break
    users+=[{'h':u['screen_name'],'f':u.get('followers_count') or 0,'av':u.get('profile_image') or ''} for u in d.get('followers') or [] if u.get('screen_name')]
    cur=d.get('next_cursor')
    if not d.get('followers') or not cur or not d.get('more_users'): break
  seen={};[seen.setdefault(u['h'],u) for u in users]; users=list(seen.values())
  json.dump({'t':time.time(),'users':users},open(FCACHE,'w')); return users
def search(handles,since):
  q='('+' OR '.join('from:'+h for h in handles)+f') since_time:{since} -filter:replies -filter:nativeretweets'
  r=subprocess.run(['treg','call','anyapi.x.search.posts','--method','POST','--data',json.dumps({'query':q,'limit':50,'queryType':'Latest'})],capture_output=True,text=True).stdout
  try: return json.loads(r[r.index('{'):])['output']['data'].get('items',[])
  except Exception: return []
def run(hours=None):
  fc=CFG.load()['followers']; hours=hours or fc['hours']
  now=time.time(); since=int(now-hours*3600)
  users=follower_list(); F={u['h'].lower():u for u in users}
  batches=[[u['h'] for u in users[i:i+18]] for i in range(0,len(users),18)]
  posts={}
  with cf.ThreadPoolExecutor(8) as ex:
    for items in ex.map(lambda b:search(b,since),batches):
      for it in items:
        if it.get('isReply') or (it.get('authorUsername') or '').lower() not in F: continue
        posts[it['id']]=it
  per={};rows=[]
  for x in sorted(posts.values(),key=lambda x:-x['createdUtc']):
    if (x.get('lang') or 'en') not in fc['languages']: continue      # English (or media-only) posts
    h=x['authorUsername'].lower(); per[h]=per.get(h,0)+1
    if per[h]>fc['max_per_person']: continue                                                   # max 2 latest posts per follower
    rows.append(x)
  rows=rows[:80]
  items=[dict(id=it['id'],url=f"https://x.com/{it['authorUsername']}/status/{it['id']}",handle=it['authorUsername'],name=it.get('authorName') or '',avatar=it.get('authorImage') or '',followers=it.get('authorFollowers') or 0,age=int((now-it['createdUtc'])/60),views=it.get('viewCount') or 0,replies=it.get('replyCount') or 0,likes=it.get('likeCount') or 0,vpm=int((it.get('viewCount') or 0)/max((now-it['createdUtc'])/60,1)),text=(it.get('text') or '')[:400],verdict='',why='follows you') for it in rows]
  json.dump({'built':now,'items':items},open('followers.json','w'))
  t=datetime.datetime.now().strftime('%H:%M')
  def ag(m): return f"{m}m ago" if m<60 else f"{m//60}h ago"
  cards=''.join(f"""<article class="c" data-id="{i['id']}"><label class="chk"><input type="checkbox" onchange="tog(this)"><span></span></label>
<img class="av" src="{html.escape(i['avatar'])}" alt=""><div class="body"><a class="lnk" href="{i['url']}" target="_blank" onclick="done(this)">
<div class="hd"><b>{html.escape(i['name'])}</b><span>@{html.escape(i['handle'])} · {ag(i['age'])} · {k(i['followers'])} followers</span></div>
<p>{html.escape(i['text'])}</p><div class="st"><span>{IC['rep']}{i['replies']}</span><span>{IC['like']}{k(i['likes'])}</span><span>{IC['view']}{k(i['views'])}</span><button class="skipb" onclick="event.preventDefault();event.stopPropagation();openSkip(this)">Skip</button></div></a></div></article>""" for i in items)
  open('followers.html','w').write(_page('followers','Followers',f"Updated {t} · {len(items)} posts from {len(users)} followers in the last {hours}h · newest first",cards))
  print(t,'followers',len(users),'batches',len(batches),'posts',len(items),flush=True)
  return items
if __name__=='__main__':
  os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data'))
  for i in run()[:10]: print(i['age'],'m @'+i['handle'],'|',i['text'][:60].replace('\n',' '))
