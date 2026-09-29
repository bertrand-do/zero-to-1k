# xreplies server: serves the tabs on http://127.0.0.1:5191 and runs a search only when you press Fetch.
import threading,time,http.server,os,json,urllib.parse,sys,base64
APP=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,APP)
DATA=os.path.join(APP,'..','data'); os.makedirs(DATA,exist_ok=True); os.chdir(DATA)
import config as CFG,rising,connect,followers
PW=os.environ.get('XREPLIES_PASSWORD','')
EXT=os.path.join(APP,'..','extension')   # only needed if you expose the page beyond your own machine
TABS={}
def build_tabs():
  for k in CFG.load()['topics']:
    TABS.setdefault(k,{'fn':(lambda k=k:rising.run(k)),'pending':False,'last':0,'busy':False})
  TABS.setdefault('followers',{'fn':followers.run,'pending':False,'last':0,'busy':False})
  TABS.setdefault('connect',{'fn':connect.run,'pending':False,'last':0,'busy':False})
  for n in TABS:
    try: TABS[n]['last']=TABS[n]['last'] or os.path.getmtime(n+'.json')
    except OSError: pass
build_tabs()
def loop():
  while True:
    for n,t in list(TABS.items()):
      if t['pending']:
        t['pending']=False; t['busy']=True
        try: t['fn']()
        except Exception as e: print(n,'err',e,flush=True)
        t['last']=time.time(); t['busy']=False
    time.sleep(1)
threading.Thread(target=loop,daemon=True).start()
def jl(p,d):
  try: return json.load(open(p))
  except Exception: return d
class H(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*a): pass
  def j(self,o,code=200):
    b=json.dumps(o).encode(); self.send_response(code); self.send_header('Content-Type','application/json'); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers(); self.wfile.write(b)
  def authed(self):
    if not PW: return True
    if self.client_address[0]=='127.0.0.1' and not self.headers.get('CF-Connecting-IP') and not self.headers.get('Cf-Ray'): return True
    h=self.headers.get('Authorization','')
    ok=h.startswith('Basic ') and base64.b64decode(h[6:]).decode(errors='ignore').split(':',1)[-1]==PW
    ok=ok or ('xr='+PW) in (self.headers.get('Cookie') or '')
    qk=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('key',[''])[0]
    if qk==PW:
      self.send_response(302); self.send_header('Set-Cookie',f'xr={PW}; Max-Age=2592000; Path=/; HttpOnly; Secure; SameSite=Lax')
      self.send_header('Location',urllib.parse.urlparse(self.path).path or '/'); self.end_headers(); return False
    if not ok:
      self.send_response(401); self.send_header('WWW-Authenticate','Basic realm="xreplies"'); self.end_headers(); return False
    return True
  def do_OPTIONS(self):
    self.send_response(204); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Access-Control-Allow-Headers','Content-Type'); self.send_header('Access-Control-Allow-Methods','GET,POST'); self.end_headers()
  def do_POST(self):
    if not self.authed(): return
    u=urllib.parse.urlparse(self.path)
    if u.path=='/api/skip':
      n=int(self.headers.get('Content-Length') or 0); body=json.loads(self.rfile.read(n) or b'{}'); body['ts']=time.strftime('%Y-%m-%dT%H:%M:%S')
      with open('feedback.jsonl','a') as f: f.write(json.dumps(body,ensure_ascii=False)+'\n')
      D=jl('done.json',{}); D.setdefault(body.get('tab',''),{})[body.get('id','')]=int(time.time()); json.dump(D,open('done.json','w'))
      return self.j({'ok':True})
    self.send_response(404); self.end_headers()
  def do_GET(self):
    if not self.authed(): return
    u=urllib.parse.urlparse(self.path); q=urllib.parse.parse_qs(u.query); g=lambda k,d='':q.get(k,[d])[0]
    if u.path=='/api/tabs':
      c=CFG.load(); return self.j([{'id':k,'label':v['label']} for k,v in c['topics'].items()]+[{'id':'followers','label':'Followers'},{'id':'connect','label':'Connect'}])
    if u.path=='/api/status': return self.j({k:{'busy':v['busy'] or v['pending'],'last':v['last']} for k,v in TABS.items()})
    if u.path in ('/api/fetch','/api/run-now'):
      n=g('tab'); build_tabs()
      for x in (list(CFG.load()['topics']) if n=='all' else [n]):
        if x in TABS and not TABS[x]['busy']: TABS[x]['pending']=True
      return self.j({'ok':True})
    if u.path=='/api/topics':
      return self.j([{'id':k,'label':v['label']} for k,v in CFG.load()['topics'].items()])
    if u.path=='/api/topic':   # ?add=Label -> new empty topic
      import re as _re
      label=g('add').strip()[:40]
      if not label: return self.j({'error':'name needed'},400)
      c=CFG.load(); tid=_re.sub(r'[^a-z0-9]+','-',label.lower()).strip('-') or 'topic'
      while tid in c['topics'] or tid in ('all','followers','connect','filters'): tid+='-2'
      loc=jl(CFG.LOCAL,{}); loc.setdefault('topics',{})[tid]={'label':label,'keywords':[]}; CFG.save_local(loc); build_tabs()
      return self.j({'id':tid,'label':label})
    if u.path=='/api/counts':
      D=jl('done.json',{}); out={}
      def n_new(tab): return sum(1 for i in jl(tab+'.json',{}).get('items',[]) if i['id'] not in D.get(tab,{}))
      out['rising']=sum(n_new(k) for k in CFG.load()['topics']); out['followers']=n_new('followers'); out['connect']=n_new('connect')
      return self.j(out)
    if u.path=='/api/items' and g('tab')=='all':
      c=CFG.load(); D=jl('done.json',{}); items=[]; done={}; busy=False; last=0
      for tid in c['topics']:
        d=jl(tid+'.json',{}); items+=d.get('items',[]); done.update(D.get(tid,{}))
        if tid in TABS: busy=busy or TABS[tid]['busy'] or TABS[tid]['pending']; last=max(last,TABS[tid]['last'])
      seen=set(); items=[i for i in sorted(items,key=lambda i:(i.get('verdict')!='GO',-i.get('vpm',0))) if not (i['id'] in seen or seen.add(i['id']))]
      return self.j({'items':items,'done':done,'busy':busy,'last':last})
    if u.path=='/api/items':
      n=g('tab','rising'); data=jl(n+'.json',{'built':0,'items':[]})
      data['done']=jl('done.json',{}).get(n,{}); data['busy']=(TABS[n]['busy'] or TABS[n]['pending']) if n in TABS else False; data['last']=TABS.get(n,{}).get('last',0)
      return self.j(data)
    if u.path=='/api/filters':
      n=g('tab','rising'); c=CFG.load()
      if n not in c['topics']: return self.j({'topic':n,'note':'This tab has no keyword filters. Its settings live in config (followers / connect).','settings':c.get(n,{})})
      f=jl(n+'.json',{}).get('filters') or {}
      labels=rising.rule_labels(c); drop={x['id']:x['dropped'] for x in f.get('rules',[])}
      return self.j({'topic':n,'label':c['topics'][n]['label'],'keywords':c['topics'][n]['keywords'],'searched':f.get('searched'),'kept':f.get('kept'),
        'rules':[{'id':k,'text':labels[k],'on':(c['rules_on'].get(k,True) if k not in ('too_old','too_few_views') else True),'locked':k in ('too_old','too_few_views'),'dropped':drop.get(k)} for k in rising.RULE_TEXT]})
    if u.path=='/api/keyword':   # ?tab=rising&add=... or &remove=...
      c=CFG.load(); n=g('tab'); loc=jl(CFG.LOCAL,{})
      kw=list(c['topics'][n]['keywords'])
      if g('add').strip() and g('add').strip() not in kw: kw.append(g('add').strip())
      if g('remove') in kw: kw.remove(g('remove'))
      loc.setdefault('topics',{}).setdefault(n,{})['keywords']=kw; CFG.save_local(loc); return self.j({'keywords':kw})
    if u.path=='/api/rule':      # ?id=flop&on=0
      loc=jl(CFG.LOCAL,{}); loc.setdefault('rules_on',{})[g('id')]=g('on')=='1'; CFG.save_local(loc); return self.j({'ok':True})
    if u.path in ('/api/mark','/api/done','/api/clear','/api/mark-many'):
      D=jl('done.json',{}); tab=g('tab'); D.setdefault(tab,{})
      if u.path=='/api/mark':
        if g('on','1')=='1': D[tab][g('id')]=int(time.time())
        else: D[tab].pop(g('id'),None)
      if u.path=='/api/mark-many':   # Clear page: hidden for good
        for i in g('ids').split(','):
          if i: D[tab][i]=-1
      if u.path=='/api/clear': D[tab]={}
      json.dump(D,open('done.json','w')); return self.j(D[tab])
    if u.path in ('/','/app','/rising','/followers','/connect'):
      return self._file(os.path.join(EXT,'panel.html'),'text/html')
    if u.path in ('/panel.css','/panel.js'):
      return self._file(os.path.join(EXT,u.path.strip('/')),'text/css' if u.path.endswith('.css') else 'application/javascript')
    if u.path=='/filters': self.path='/filters.html'; return super().do_GET() if os.path.exists('filters.html') or self._copy_filters() else None
    name=u.path.strip('/') or next(iter(CFG.load()['topics']))
    if name in TABS and os.path.exists(name+'.html'): self.path='/'+name+'.html'; return super().do_GET()
    if name in TABS: self.send_response(200); self.send_header('Content-Type','text/html'); self.end_headers(); self.wfile.write(f'<meta http-equiv=refresh content="3"><body style="font:16px -apple-system;padding:40px;background:#111;color:#eee">Fetching {name}… <script>fetch("/api/fetch?tab={name}")</script>'.encode()); return
    self.send_response(404); self.end_headers()
  def _file(self,path,ctype):
    b=open(path,'rb').read(); self.send_response(200); self.send_header('Content-Type',ctype+'; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(b)
  def _copy_filters(self):
    import shutil; shutil.copy(os.path.join(APP,'filters.html'),'filters.html'); return True
print('xreplies on http://127.0.0.1:5191',flush=True)
http.server.ThreadingHTTPServer(('127.0.0.1',5191),H).serve_forever()
