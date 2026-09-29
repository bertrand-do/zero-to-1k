# Config: defaults live in config.example.json (shipped). Your edits go to config.local.json (never shipped).
import json,os,copy
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
EX=os.path.join(ROOT,'config.example.json'); LOCAL=os.path.join(ROOT,'config.local.json')
def _merge(a,b):
  for k,v in b.items():
    if isinstance(v,dict) and isinstance(a.get(k),dict): _merge(a[k],v)
    else: a[k]=v
  return a
def load():
  c=json.load(open(EX))
  if os.path.exists(LOCAL): _merge(c,json.load(open(LOCAL)))
  return c
def save_local(c):
  json.dump(c,open(LOCAL,'w'),indent=2,ensure_ascii=False)
