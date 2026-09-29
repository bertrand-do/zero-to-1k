# Run after tracker.py prints DONE. Answers: given a post's age and views NOW, how likely is it to reach 10k views?
import json
d=json.load(open('tracked.json'))
def at(obs,m):  # views at or just before minute m
  c=[o for o in obs if o[0]<=m]; return c[-1][1] if c else None
final={i:max(o[1] for o in v['obs']) for i,v in d.items() if v['obs']}
for age in (30,60,120,180):
  print(f'\n== post age ~{age} min: views now -> share that reached 10k by end of tracking ==')
  for lo,hi in [(0,300),(300,1000),(1000,3000),(3000,10000),(10000,10**9)]:
    ids=[i for i,v in d.items() if v['obs'] and (x:=at(v['obs'],age)) is not None and lo<=x<hi and v['obs'][-1][0]>=age+240]
    if ids: print(f'  {lo:>6}-{hi if hi<10**9 else "∞":<6} n={len(ids):3}  reached 10k: {sum(final[i]>=10000 for i in ids):3} ({100*sum(final[i]>=10000 for i in ids)/len(ids):.0f}%)  median final={sorted(final[i] for i in ids)[len(ids)//2]}')

# Motion check: at 15-60 min, do early likes/replies predict reaching 10k?
import statistics as st
rows=[]
for i,v in d.items():
  o=v['obs']; e=[x for x in o if 15<=x[0]<=60]
  if not e or o[-1][0]-e[0][0]<240: continue
  e=e[0]; rows.append(dict(views=e[1],rep=e[2] or 0,likes=e[3] or 0,final=final[i]))
def show(l,g):
  if g: print(f'  {l:32} n={len(g):3} reached 10k: {sum(r["final"]>=10000 for r in g)}/{len(g)}')
print('\n== motion at 15-60 min (posts with >=500 views then) ==')
g=[r for r in rows if r['views']>=500]
show('likes <1% of views, <3 replies',[r for r in g if r['likes']<0.01*r['views'] and r['rep']<3])
show('likes >=1% of views or 3+ replies',[r for r in g if not (r['likes']<0.01*r['views'] and r['rep']<3)])
for lo,hi in [(0,.005),(.005,.01),(.01,.02),(.02,1)]: show(f'likes/views {lo}-{hi}',[r for r in g if lo<=r['likes']/max(r['views'],1)<hi])
