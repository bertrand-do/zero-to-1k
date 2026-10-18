# Trending tab: spots a NEW or SPIKING term (a tool, model, hashtag) in the niches within an hour or two.
# Runs by itself every trending.every_min minutes (like Watched). No sound, no notification.
# Score = distinct authors mentioning a term in the last 3h vs its per-3h average over the prior 48h.
import json,subprocess,time,os,re,threading
import config as CFG,jobs
OUT='trending.json'; HIST='trending_history.json'
DEFAULT={'every_min':30,'window_hours':3,'baseline_hours':48,'keep_hours':72,'limit':50,'max_searches':3,'learning_hours':6,
 'spike_ratio':3,'spike_min_authors':4,'new_min_authors':3,'min_authors':2,'top':25,
 'queries':['(LLM OR ChatGPT OR OpenAI OR Claude OR Anthropic OR Gemini OR "AI agent" OR "AI model") min_faves:100 -filter:replies lang:en',
  '(vibe coding OR vibecoding OR cursor OR claude code OR codex) min_faves:50 -filter:replies lang:en',
  '(founder OR startup OR indie hacker OR saas OR buildinpublic) min_faves:100 -filter:replies lang:en']}
STATE={'last':0,'busy':False,'err':'','cost':0.0}
def cfg():
  c=dict(DEFAULT); c.update(CFG.load().get('trending') or {}); return c
def _jl(p,d):
  try: return json.load(open(p))
  except Exception: return d
STOP=set('''a about above after again all also am an and any are as at be because been before being below between both but by can could did do does doing down during each few for from further had has have having he her here hers him his how i if in into is it its just me more most my no nor not now of off on once only or other our out over own same she should so some such than that the their them then there these they this those through to too under until up very was we were what when where which while who whom why will with would you your yours
i'm i've i'll i'd it's don't doesn't didn't can't won't isn't aren't that's there's here's what's let's you're they're we're he's she's
yes yeah ok okay lol lmao thanks thank please hey hello hi gm gn wow omg
monday tuesday wednesday thursday friday saturday sunday january february march april may june july august september october november december today tomorrow yesterday tonight week weekend month year years day days time times hour hours minute minutes
ai llm llms ml model models app apps people today new just build building built builds make making made makes use using used uses one two three first last next best better good great bad real thing things way ways lot lots many much really actually still even ever never always every something anything everything nothing someone everyone anyone
get got getting go going gone see say said says know think thought want need needs like love look looks looking try trying tried take takes took give gives gave come comes came work works working worked help helps start started starting stop run running ship shipped shipping launch launched launching post posts posted read write wrote writing learn learned
user users team teams company companies product products tool tools agent agents code coding data tech software system systems project projects idea ideas problem problems user's founder founders startup startups saas business money free paid job jobs market
big small high low long short old human humans world life news story video image images text content open source api apis feature features update updates version release released released
twitter x thread link links reply replies follow followers like likes share retweet rt vs via per etc
also let will would could should must might may need
if when what why how who this that these those there here
dm bio link thread pro max check lead computer safety enterprise
usd us uk eu
end search morning fam labs night evening guys folks gang team crew family wait hours'''.split())
def terms(text):
  t=re.sub(r'https?://\S+','',text or ''); out=set()
  for m in re.finditer(r'\$[A-Za-z]{2,10}\b',t): out.add(m.group(0).lower())
  for m in re.finditer(r'(?<![\w&])#\w{2,30}',t): out.add(m.group(0).lower())
  for m in re.finditer(r'(?<![\w@])@\w{2,20}',t): out.add(m.group(0).lower())
  t2=re.sub(r'[@#$]\w+','',t)
  # capitalised phrases, optionally ending in a version number: "Nano Banana 2.1", "GPT-6.1", "Claude Code"
  for m in re.finditer(r'\b(?:[A-Z][A-Za-z0-9]*(?:[-.][A-Za-z0-9]+)*)(?:[ ](?:[A-Z][A-Za-z0-9]*(?:[-.][A-Za-z0-9]+)*|v?\d+(?:\.\d+)*)){0,3}',t2):
    p=m.group(0).strip(); ws=p.split(' ')
    while ws and ws[-1].lower() in STOP: ws.pop()
    while ws and ws[0].lower() in STOP: ws.pop(0)
    if not ws: continue
    p=' '.join(ws)
    if len(ws)>1: out.add(p.lower())
    # single tokens: only product-like ones (caps+digit/hyphen, camel, all-caps >=3) or capitalised non-stopwords mid-sentence
    for w in ws:
      lw=w.lower()
      if lw in STOP or len(w)<3 or re.fullmatch(r'[\d.\-]+',w): continue
      if re.search(r'\d',w) or '-' in w or re.search(r'[a-z][A-Z]',w) or (w.isupper() and len(w)>=3) or w[0].isupper(): out.add(lw)
  return {x for x in out if x.strip('#@$').lower() not in STOP and len(x)>=3}

# A post only counts if it is really about AI / building / startups, and not politics or news.
STRONG=re.compile(r"\b(llms?|gpt[-\d.]*|chatgpt|openai|claude|anthropic|gemini|grok|mistral|deepseek|cursor|codex|copilot|vibe ?cod\w*|saas|mrr|arr|indie ?hack\w*|buildinpublic|founders?|startups?|github|open[- ]source|api|sdk|n8n|no-?code|prompt\w*|fine-?tun\w*|rag|mcp|agentic|hugging ?face|nano banana|midjourney|sora|veo|kling|runway|y ?combinator|yc)\b",re.I)
WEAK=re.compile(r"\b(ai|model|models|agent|agents|code|coding|developers?|devs?|launch\w*|ship\w*|product|automation|app|apps|users|tool|tools|workflow|startup)\b",re.I)
NEWS=re.compile(r"\b(police|party|parties|minister|election\w*|government|govt|parliament|bjp|congress|modi|trump|biden|delhi|mumbai|india|pakistan|china|army|war|killed|murder|arrest\w*|court|protest\w*|gaza|israel|ukraine|russia|airport|flight|cricket|football|ipl|bollywood|celebrity|actor|actress|religio\w*|temple|mosque|church|riot\w*|crypto\w*|usdt|usdc|token|tokens|airdrop\w*|memecoin\w*|nft\w*|web3|staking|stake|bnb|solana|\$sol|pump\w*|degen\w*|presale|giveaway|wagmi|gm fam)\b",re.I)
def niche_ok(text):
  t=text or ''
  if NEWS.search(t) or re.search(r'(?<!\w)\$[A-Za-z]{2,8}\b',t): return False   # news, politics, crypto cashtags
  return bool(STRONG.search(t)) or len({m.group(0).lower() for m in WEAK.finditer(t)})>=2
def treg_search(q,since,limit):
  data={'query':f'{q} since_time:{since}','limit':limit,'queryType':'Latest'}
  p=subprocess.run(['treg','call','anyapi.x.search.posts','--method','POST','--data',json.dumps(data)],capture_output=True,text=True)
  m=re.search(r'charged \$([\d.]+)',p.stderr+p.stdout); cost=float(m.group(1)) if m else 0.0
  print(f'treg trending search ${cost:.4f}',flush=True)
  r=p.stdout
  try: return json.JSONDecoder().raw_decode(r[r.index('{'):])[0]['output']['data'].get('items',[]),cost
  except Exception: return [],cost
def check():
  c=cfg(); now=time.time(); since=int(now-c['window_hours']*3600)
  H=_jl(HIST,{'first_run':now,'posts':{}}); H.setdefault('first_run',now); P=H.setdefault('posts',{})
  cost=0.0; got=0
  for q in c['queries'][:int(c['max_searches'])]:
    items,cc=treg_search(q,since,int(c['limit'])); cost+=cc
    for it in items:
      if not it.get('id') or not it.get('createdUtc'): continue
      P[it['id']]={'t':it['createdUtc'],'a':(it.get('authorUsername') or '').lower(),'v':it.get('viewCount') or 0,'l':it.get('likeCount') or 0,
        'x':(it.get('text') or '')[:400],'h':it.get('authorUsername') or '','k':sorted(terms(it.get('text')))}; got+=1
  STATE['cost']=round(STATE['cost']+cost,4)
  cut=now-c['keep_hours']*3600; H['posts']={i:p for i,p in P.items() if p['t']>=cut}; P=H['posts']
  json.dump(H,open(HIST,'w'))
  W=c['window_hours']*3600; cur={}; base={}   # base[term][bucket]=set(authors)
  oldest=min([p['t'] for p in P.values()]+[H['first_run']])
  span_h=(now-min(oldest,H['first_run']))/3600
  learning=(now-H['first_run'])/3600<c['learning_hours']
  nb=max(1,min(int(c['baseline_hours']/c['window_hours']),int(max(0,span_h-c['window_hours'])//c['window_hours'])))
  for pid,p in P.items():
    if not niche_ok(p.get('x')): continue
    p=dict(p,k=sorted(terms(p.get('x'))))   # recompute so stop-word changes apply to old history too
    age=now-p['t']
    if age<=W:
      for k in p['k']: cur.setdefault(k,[]).append((pid,p))
    elif age<=W+nb*W:
      b=int((age-W)//W)
      for k in p['k']: base.setdefault(k,{}).setdefault(b,set()).add(p['a'])
  rows=[]
  for k,ps in cur.items():
    au={p['a'] for _,p in ps}
    if len(au)<c['min_authors']: continue
    bk=base.get(k,{}); avg=sum(len(v) for v in bk.values())/nb
    ratio=round(len(au)/max(avg,0.5),1) if bk else None
    if learning: flag='LEARNING'
    elif not bk and len(au)>=c['new_min_authors']: flag='NEW'
    elif ratio is not None and ratio>=c['spike_ratio'] and len(au)>=c['spike_min_authors']: flag='SPIKING'
    else: flag=''
    ex=sorted(ps,key=lambda x:-x[1]['v'])[:3]
    rows.append({'term':k,'authors':len(au),'views':sum(p['v'] for _,p in ps),'posts':len(ps),'ratio':ratio,'baseline':round(avg,2),'flag':flag,
      'examples':[{'url':f"https://x.com/{p['h']}/status/{i}",'handle':p['h'],'views':p['v'],'text':p['x'][:160]} for i,p in ex]})
  # drop sub-phrases that add nothing over their longer phrase (e.g. "nano" vs "nano banana") when author counts match
  rank={'SPIKING':0,'NEW':1,'LEARNING':2,'':3}
  rows.sort(key=lambda r:(rank[r['flag']],-(r['ratio'] or 0) if r['flag'] in('SPIKING','NEW') else 0,-r['authors'],-r['views']))
  keep=[]
  for r in rows:
    if any(r['term']!=o['term'] and r['term'] in o['term'].split(' ') and o['authors']>=r['authors']*0.9 and o['term'].count(' ')>=1 for o in rows[:120]): continue
    keep.append(r)
  keep=keep[:int(c['top'])]
  json.dump({'built':now,'learning':learning,'learning_hours':c['learning_hours'],'history_hours':round(span_h,1),'items':keep,'posts_seen':len(P),'run_cost':round(cost,4)},open(OUT,'w'))
  return keep
def loop():
  while True:
    c=cfg()
    if jobs.running():
      STATE['busy']=True
      try: check(); STATE['err']=''
      except Exception as e: STATE['err']=str(e); print('trending err',e,flush=True)
      STATE['busy']=False; STATE['last']=time.time()
      time.sleep(max(300,int(c['every_min'])*60))
    else: time.sleep(20)
def start(): threading.Thread(target=loop,daemon=True).start()
if __name__=='__main__':
  os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data')); check()
  d=_jl(OUT,{}); print('learning' if d.get('learning') else 'live','| posts seen',d.get('posts_seen'),'| run cost $',d.get('run_cost'))
  for r in d.get('items',[])[:15]: print(f"{r['flag'] or '-':8} {r['term']:28} authors={r['authors']:<3} views={r['views']:<9} ratio={r['ratio']}")
