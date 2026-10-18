# On/off switch for the background jobs (Watched + Trending), remembered across restarts in data/jobs.json.
import json
F='jobs.json'
def running():
  try: return bool(json.load(open(F)).get('running',True))
  except Exception: return True
def set_running(on): json.dump({'running':bool(on)},open(F,'w'))
