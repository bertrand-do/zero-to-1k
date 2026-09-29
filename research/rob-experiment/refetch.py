# Re-download the full posts behind the IDs in this folder, with YOUR treg key.
# Why IDs only: X's terms let people share post IDs, not copies of other people's posts.
# Cost: about $0.001 per post via treg (≈ $0.90 for everything). Run: python3 refetch.py [--rob-only]
import csv,json,subprocess,sys,concurrent.futures as cf,os
HERE=os.path.dirname(os.path.abspath(__file__))
ids=set()
for r in csv.DictReader(open(os.path.join(HERE,'rob-posts.csv'))): ids.add(r['tweet_id'])
if '--rob-only' not in sys.argv:
  for r in csv.DictReader(open(os.path.join(HERE,'rob-replies-days-1-2.csv'))): ids.add(r['parent_id'])
out_path=os.path.join(HERE,'rehydrated.json'); out=json.load(open(out_path)) if os.path.exists(out_path) else {}
todo=[i for i in ids if i and i not in out]
print(f'{len(todo)} posts to fetch (≈ ${len(todo)*0.001:.2f})')
def get(i):
  r=subprocess.run(['treg','call','tikhub.x.twitter-web-fetch-tweet-detail','--query','tweet_id='+i],capture_output=True,text=True).stdout
  try: d=json.loads(r[r.index('{'):])['data']; return i,{'text':d.get('text'),'author':(d.get('author') or {}).get('screen_name'),'created_at':d.get('created_at'),'views':d.get('views'),'likes':d.get('likes'),'replies':d.get('replies')}
  except Exception: return i,None
with cf.ThreadPoolExecutor(10) as ex:
  for n,(i,v) in enumerate(ex.map(get,todo)):
    if v: out[i]=v
    if n%50==0: json.dump(out,open(out_path,'w'))
json.dump(out,open(out_path,'w'),ensure_ascii=False,indent=1); print('saved',len(out),'posts to',out_path)
