"""Read-only Forex Factory weekly events, via its public JSON calendar feed."""
from datetime import datetime
import json
from pathlib import Path
import os
import time
import threading
from urllib.request import HTTPRedirectHandler,build_opener,Request
from urllib.error import URLError

LOCK=threading.Lock()
FEED='https://nfs.faireconomy.media/ff_calendar_thisweek.json'


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


def settings(raw=None):
    cfg={'currencies':[],'impacts':['High','Medium'],'limit':20,'include_past':False}
    if raw is None:raw={}
    if not isinstance(raw,dict) or set(raw)-set(cfg):raise ValueError('Invalid calendar settings')
    cfg.update(raw)
    if type(cfg['limit']) is not int or not 1<=cfg['limit']<=100 or type(cfg['include_past']) is not bool:raise ValueError('Invalid calendar limit')
    if not isinstance(cfg['currencies'],list) or len(cfg['currencies'])>20 or any(not isinstance(c,str) or not c.isascii() or not c.isalpha() or not 2<=len(c)<=5 for c in cfg['currencies']):raise ValueError('Invalid currencies')
    if not isinstance(cfg['impacts'],list) or any(c not in ('High','Medium','Low','Holiday') for c in cfg['impacts']):raise ValueError('Invalid impacts')
    return cfg


def parse(rows):
    if not isinstance(rows,list) or len(rows)>2000:raise ValueError('Invalid calendar feed')
    result=[]
    for row in rows:
        if not isinstance(row,dict):continue
        try:
            dt=datetime.fromisoformat(row['date'].replace('Z','+00:00'))
            if dt.tzinfo is None:continue
            event={'time':int(dt.timestamp())}
        except (KeyError,TypeError,ValueError,AttributeError):continue
        for key in ('title','country','impact','forecast','previous'):
            value=row.get(key,'');event[key]=str(value)[:300] if isinstance(value,(str,int,float)) else ''
        result.append(event)
    return sorted(result,key=lambda row:row['time'])


def _run(data):
    if set(data)-{'settings'}:raise ValueError('Unknown calendar input')
    cfg=settings(data.get('settings'));now=time.time()
    root=Path(os.environ.get('DASHBOARD_MODULE_STATE_DIR','/var/lib/30na/dashboard'))/'calendar'
    root.mkdir(parents=True,exist_ok=True,mode=0o700)
    cache=root/'events.json';cached=None
    if cache.is_symlink():raise ValueError('Invalid cache path')
    if cache.exists():
        try:
            if cache.stat().st_size<=1048576:cached=json.loads(cache.read_text())
        except (OSError,ValueError):cached=None
    stale=not cached or now-max(cached.get('fetched_at',0),cached.get('attempted_at',0))>900;error=bool((cached or {}).get('error',False))
    if stale:
        try:
            with build_opener(NoRedirect()).open(Request(FEED,headers={'User-Agent':'30na-EconomicCalendar/1.0','Accept':'application/json'}),timeout=5) as response:
                raw=response.read(1048577)
            if len(raw)>1048576:raise ValueError('Feed too large')
            current={'fetched_at':now,'events':parse(json.loads(raw))}
            temp=root/('events-'+os.urandom(8).hex()+'.tmp')
            try:
                with temp.open('x',encoding='utf8') as stream:json.dump(current,stream)
                temp.replace(cache)
            finally:temp.unlink(missing_ok=True)
            cached=current;stale=False
        except (OSError,URLError,ValueError,TypeError):
            error=True;cached={**(cached or {'fetched_at':0,'events':[]}),'attempted_at':now,'error':True}
            temp=root/('failure-'+os.urandom(8).hex()+'.tmp')
            try:
                with temp.open('x',encoding='utf8') as stream:json.dump(cached,stream)
                temp.replace(cache)
            finally:temp.unlink(missing_ok=True)
    events=[event for event in (cached or {}).get('events',[]) if (cfg['include_past'] or event['time']>=now) and (not cfg['currencies'] or event['country'] in cfg['currencies']) and (not cfg['impacts'] or event['impact'] in cfg['impacts'])]
    return {'status':'stale' if cached and cached.get('fetched_at') and error else 'unavailable' if not cached or not cached.get('fetched_at') else 'ok','events':events[:cfg['limit']],
            'source':'Forex Factory','source_url':'https://www.forexfactory.com/calendar','fetched_at':(cached or {}).get('fetched_at'),
            'settings':cfg,'message':'Calendar feed unavailable' if error else ''}


def run(data):
    with LOCK:
        return _run(data)
