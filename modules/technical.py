"""Trusted, browser-independent session clocks and price-level calculations.

UTC epoch seconds are the data contract; broker wall dates are explicit.
No executable MT5 payload, remote source, or caller-selected file is loaded.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import calendar
import math
import re
import time
from zoneinfo import ZoneInfo
from .module_state import change

KINDS = ('session-windows', 'session-clock', 'round-levels', 'previous-day-levels', 'previous-day-session-levels')
DEFAULTS = {
    'session-clock': {'winter_utc_minutes':None,'clock_change':'none','windows':[], 'points':[], 'teaching_view':'all',
                      'reference_timezone':None,'schedule_shift_minutes':0,'chart_minutes':15,'clock_size':360,'points_on_clock':True,'show_seconds':True,'highlight_minutes':5,
                      'chart_point_lines':False,'days':10,'position':{'x':1.0,'y':1.0},'font':'system',
                      'text_color':'#e7edf7','point_color':'#fbbf24','background_color':'#121c2e'},
    'round-levels': {'auto':True,'auto_percent':0.5,'manual_step':250,'max_lines':300,'show_labels':True,
                     'color':'#94a3b8','style':'dotted','width':1,'label_color':'#94a3b8','font_size':11},
    'previous-day-levels': {'winter_utc_minutes':0,'clock_change':'none','days':10,'draw_today':True,'draw_past':True,
                            'show_high':True,'show_low':True,'show_mid':True,'show_open':True,'show_close':True,'styles':{}},
    'previous-day-session-levels': {'winter_utc_minutes':0,'clock_change':'none','days':10,'draw_today':True,'draw_past':True,
                                    'show_high':True,'show_low':True,'show_mid':True,'show_open':True,'show_close':True,'styles':{},
                                    'session_start':'16:30','session_end':'23:00','scan_minutes':15,'allow_wrap':True},
}
DEFAULTS['session-windows'] = {**DEFAULTS['session-clock'], 'window_labels':True,'time_points':True,'countdown_panel':True,'day_start_lines':True,'window_shape':'both'}

LEVEL_STYLES = {
    'high':{'color':'#c4b5fd','style':'solid','width':1}, 'low':{'color':'#c4b5fd','style':'solid','width':1},
    'mid':{'color':'#c4b5fd','style':'dotted','width':1}, 'open':{'color':'#a78bfa','style':'dashed','width':1},
    'close':{'color':'#e879f9','style':'dashed','width':1},
}


def number(value, low, high, name):
    if type(value) not in (int,float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError('invalid ' + name)
    return value


def integer(value, low, high, name):
    if type(value) is not int: raise ValueError('invalid ' + name)
    return number(value, low, high, name)


def minute(value):
    if not isinstance(value,str) or not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]',value):
        raise ValueError('time must be HH:MM')
    h,m = value.split(':')
    return int(h)*60+int(m)


def color(value):
    if not isinstance(value,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',value): raise ValueError('invalid color')


def line_style(value):
    if not isinstance(value,dict) or set(value)-{'color','style','width'}: raise ValueError('invalid line style')
    if 'color' in value: color(value['color'])
    if value.get('style','solid') not in ('solid','dashed','dotted','dash-dot'): raise ValueError('invalid line style')
    integer(value.get('width',1),1,5,'line width')


def settings(kind, raw=None):
    if kind not in KINDS or not isinstance(raw or {},dict): raise ValueError('invalid indicator settings')
    raw = {} if raw is None else raw
    if not isinstance(raw,dict) or set(raw)-set(DEFAULTS[kind]): raise ValueError('unknown indicator setting')
    cfg = {**DEFAULTS[kind],**raw}
    for key, default in DEFAULTS[kind].items():
        if type(default) is bool and type(cfg[key]) is not bool: raise ValueError('invalid '+key)
    if 'winter_utc_minutes' in cfg:
        offset = cfg['winter_utc_minutes']
        if offset is not None: integer(offset,-720,840,'winter UTC offset')
        if offset is None and kind not in ('session-clock','session-windows'): raise ValueError('broker offset required')
        if cfg['clock_change'] not in ('none','Europe','USA'): raise ValueError('invalid clock change')
    if 'days' in cfg: integer(cfg['days'],1,1000,'days')
    if kind in ('session-clock','session-windows'):
        if cfg['reference_timezone'] is not None:
            if not isinstance(cfg['reference_timezone'],str) or len(cfg['reference_timezone'])>100: raise ValueError('invalid reference timezone')
            try: ZoneInfo(cfg['reference_timezone'])
            except (KeyError, ValueError): raise ValueError('unknown reference timezone') from None
        integer(cfg['schedule_shift_minutes'],-1440,1440,'schedule shift')
        integer(cfg['chart_minutes'],1,1440,'chart timeframe')
        if 1440 % cfg['chart_minutes']: raise ValueError('chart minutes must divide 1440')
        if kind=='session-windows' and cfg['window_shape'] not in ('filled','border','both'): raise ValueError('invalid window shape')
        integer(cfg['clock_size'],120,420,'clock size'); integer(cfg['highlight_minutes'],0,120,'highlight minutes')
        if cfg['font'] not in ('system','mono','serif'): raise ValueError('invalid font')
        for key in ('text_color','point_color','background_color'): color(cfg[key])
        if not isinstance(cfg['position'],dict) or set(cfg['position']) != {'x','y'}: raise ValueError('invalid position')
        for value in cfg['position'].values(): number(value,0,1,'position')
        if not isinstance(cfg['teaching_view'],str) or not re.fullmatch(r'[A-Za-z0-9 _-]{1,40}',cfg['teaching_view']): raise ValueError('invalid teaching view')
        if not isinstance(cfg['windows'],list) or len(cfg['windows'])>100: raise ValueError('invalid windows')
        if not isinstance(cfg['points'],list) or len(cfg['points'])>200: raise ValueError('invalid points')
        for window in cfg['windows']:
            if not isinstance(window,dict) or set(window)-{'name','start','end','grade','color','views'} or not {'name','start','end','grade'} <= set(window): raise ValueError('invalid window')
            if not isinstance(window['name'],str) or not 1<=len(window['name'])<=60: raise ValueError('invalid window name')
            minute(window['start']); minute(window['end'])
            if window['grade'] not in ('A','B','C'): raise ValueError('invalid window grade')
            color(window.get('color','#60a5fa'))
            views=window.get('views',[])
            if not isinstance(views,list) or len(views)>20 or any(not isinstance(v,str) or not re.fullmatch(r'[A-Za-z0-9 _-]{1,40}',v) for v in views): raise ValueError('invalid views')
        for point in cfg['points']:
            if not isinstance(point,dict) or set(point)-{'time','views'} or 'time' not in point: raise ValueError('invalid point')
            minute(point['time'])
            views=point.get('views',[])
            if not isinstance(views,list) or len(views)>20 or any(not isinstance(v,str) or not re.fullmatch(r'[A-Za-z0-9 _-]{1,40}',v) for v in views): raise ValueError('invalid views')
    elif kind == 'round-levels':
        number(cfg['auto_percent'],0.001,100,'auto percent');number(cfg['manual_step'],1e-12,1e12,'manual step')
        integer(cfg['max_lines'],1,300,'max lines');color(cfg['color']);color(cfg['label_color'])
        line_style({k:cfg[k] for k in ('color','style','width')});integer(cfg['font_size'],8,32,'font size')
    else:
        if not isinstance(cfg['styles'],dict) or set(cfg['styles'])-set(LEVEL_STYLES): raise ValueError('invalid level styles')
        for style in cfg['styles'].values(): line_style(style)
        if kind == 'previous-day-session-levels':
            start,end = minute(cfg['session_start']),minute(cfg['session_end'])
            integer(cfg['scan_minutes'],1,60,'scan minutes')
            if 60 % cfg['scan_minutes']: raise ValueError('scan minutes must divide 60')
            if end<=start and not cfg['allow_wrap']: raise ValueError('session crosses midnight')
    return cfg


def dst_seconds(stamp, rule):
    if rule == 'none': return 0
    if rule == 'USA': return int(bool(datetime.fromtimestamp(stamp,ZoneInfo('America/New_York')).dst()))*3600
    year = datetime.fromtimestamp(stamp,timezone.utc).year
    def last_sunday(month):
        last=calendar.monthrange(year,month)[1]
        day=last-(datetime(year,month,last).weekday()+1)%7
        return datetime(year,month,day,1,tzinfo=timezone.utc).timestamp()
    return 3600 if last_sunday(3)<=stamp<last_sunday(10) else 0


def wall(stamp,cfg):
    return datetime.fromtimestamp(stamp+cfg['winter_utc_minutes']*60+dst_seconds(stamp,cfg['clock_change']),timezone.utc).replace(tzinfo=None)


def epoch(local,cfg):
    # Resolve wall time against both possible offsets. Ambiguous times use the
    # first occurrence; nonexistent spring times are omitted, never invented.
    naive=local.replace(tzinfo=timezone.utc).timestamp()
    candidates=[naive-cfg['winter_utc_minutes']*60-shift for shift in (0,3600)]
    valid=[s for s in candidates if wall(s,cfg)==local]
    return min(valid) if valid else None


def timestamp(value):
    return number(value,0,32503680000,'UTC timestamp')


def reference_wall(stamp,cfg):
    return datetime.fromtimestamp(stamp,ZoneInfo(cfg['reference_timezone'])).replace(tzinfo=None) if cfg['reference_timezone'] else wall(stamp,cfg)


def scheduled(day, minutes, cfg):
    local=datetime.combine(day,datetime.min.time())+timedelta(minutes=minutes)
    if cfg['reference_timezone']:
        zone=ZoneInfo(cfg['reference_timezone'])
        candidate=local.replace(tzinfo=zone,fold=0).timestamp()
        if datetime.fromtimestamp(candidate,zone).replace(tzinfo=None)!=local: return None
    else: candidate=epoch(local,cfg)
    return None if candidate is None else candidate+cfg['schedule_shift_minutes']*60


def selected(item,cfg):
    # Point-only is a rendering mode; countdown retains all configured points.
    return cfg['teaching_view'] in ('all','Full map','Points only') or cfg['teaching_view'] in item.get('views',[])


def occurrences(cfg,day):
    windows=[];points=[]
    for w in cfg['windows']:
        if not selected(w,cfg): continue
        start,end=minute(w['start']),minute(w['end'])
        begin=scheduled(day,start,cfg);finish=scheduled(day,end+(1440 if end<=start else 0),cfg)
        if begin is None or finish is None: continue
        windows.append({**w,'start':wall(begin,cfg).strftime('%H:%M'),'end':wall(finish,cfg).strftime('%H:%M'),'start_timestamp':begin,'end_timestamp':finish})
    for p in cfg['points']:
        if selected(p,cfg):
            stamp=scheduled(day,minute(p['time']),cfg)
            if stamp is not None: points.append({'time':wall(stamp,cfg).strftime('%H:%M'),'timestamp':stamp})
    return windows,points


def clock_result(cfg,now):
    if cfg['winter_utc_minutes'] is None:
        return {'status':'needs_configuration','message':'Set broker winter UTC offset and clock change rule.', 'now':now,'settings':cfg,'time_verified':False}
    local=wall(now,cfg);reference_day=reference_wall(now,cfg).date()
    windows,points=occurrences(cfg,reference_day)
    nearby=[occurrences(cfg,reference_day+timedelta(days=i)) for i in (-1,0,1,2)]
    active=[w for ws,_ in nearby for w in ws if w['start_timestamp']<=now<w['end_timestamp']]
    future=[p for _,ps in nearby for p in ps if p['timestamp']>now]
    nxt=min(future,key=lambda p:p['timestamp']) if future else None
    remaining=max(0,math.ceil(nxt['timestamp']-now)) if nxt else None
    transitions=sorted({stamp for ws,ps in nearby for stamp in [*[w['start_timestamp'] for w in ws],*[w['end_timestamp'] for w in ws],*[p['timestamp'] for p in ps]] if stamp>now})
    initial_offset=dst_seconds(now,cfg['clock_change'])
    for hours in range(4,49,4):
        probe=int(now)+hours*3600
        if dst_seconds(probe,cfg['clock_change'])!=initial_offset:
            left=int(now);right=probe
            while right-left>1:
                mid=(left+right)//2
                if dst_seconds(mid,cfg['clock_change'])==initial_offset: left=mid
                else: right=mid
            transitions=sorted([*transitions,right]);break

    ready=bool(cfg['windows'] and cfg['points'])
    return {'status':'ok' if ready else 'needs_configuration','message':'' if ready else 'Configure the original windows and time points; no proprietary schedule is assumed.',
            'now':now,'wall_time':local.isoformat(),'seconds_of_day':local.hour*3600+local.minute*60+local.second,
            'utc_offset_minutes':cfg['winter_utc_minutes']+dst_seconds(now,cfg['clock_change'])//60,
            'active_windows':active,'windows':[] if cfg['teaching_view']=='Points only' else windows,'points':sorted({p['time'] for p in points}),
            'next_point':nxt,'next_transition':transitions[0] if transitions else None,
            'remaining_seconds':remaining,'highlight':remaining is not None and remaining<=cfg['highlight_minutes']*60,
            'settings':cfg,'time_verified':False,'time_basis':'server_utc_plus_configured_broker_rule'}


def session_chart(cfg,data,now):
    chart={};trading=set();broker_dates=set();stamp_opens=set()
    for row in bars(data,now,cfg['days']):
        bucket=int(row['time']//(cfg['chart_minutes']*60)*cfg['chart_minutes']*60)
        stamp_opens.add(bucket);trading.add(reference_wall(row['time'],cfg).date());broker_dates.add(wall(row['time'],cfg).date())
        chart[bucket]=merge(chart.get(bucket),row)
        if len(chart)>4000: del chart[next(iter(chart))]
    windows=[];points=[];day_lines=[]
    import bisect
    opens=sorted(stamp_opens)
    for day in sorted(trading)[-cfg['days']:]:
        ws,ps=occurrences(cfg,day)
        for window in ws:
            pos=bisect.bisect_left(opens,window['start_timestamp'])
            if pos<len(opens) and opens[pos]<window['end_timestamp']: windows.append(window)
        points.extend({'time':p['timestamp'],'label':p['time']} for p in ps)
    for day in sorted(broker_dates)[-cfg['days']:] :
        stamp=epoch(datetime.combine(day,datetime.min.time()),cfg)
        if stamp is not None: day_lines.append(stamp)
    return {'chart_windows':[] if cfg['teaching_view']=='Points only' else windows,'chart_lines':points if cfg['chart_minutes']<=60 else [],
            'day_lines':day_lines,'candles':[dict(v,time=k) for k,v in chart.items()], 'coverage':'available_history_only'}


def round_result(cfg,price,low,high,previous=None):
    number(price,1e-12,1e12,'price');number(low,0,1e12,'visible low');number(high,low,1e12,'visible high')
    anchor=price;step=cfg['manual_step']
    if cfg['auto']:
        if isinstance(previous,dict) and previous.get('auto') is True and previous.get('auto_percent')==cfg['auto_percent']:
            anchor=number(previous.get('anchor'),1e-12,1e12,'anchor')
            if abs(Decimal(str(price))/Decimal(str(anchor))-1)<Decimal('0.2'): step=number(previous.get('step'),1e-24,1e12,'step')
            else: anchor=price
        if anchor==price:
            target=price*cfg['auto_percent']/100
            exponent=math.floor(math.log10(target))
            candidates=[n*10**power for power in (exponent-1,exponent,exponent+1) for n in (1,2,2.5,5)]
            step=min(candidates,key=lambda n:(abs(n-target),n))
    spacing=Decimal(str(step)); left=int((Decimal(str(low))/spacing).to_integral_value(rounding=ROUND_CEILING));right=int((Decimal(str(high))/spacing).to_integral_value(rounding=ROUND_FLOOR))
    total=max(0,right-left+1); count=min(total,cfg['max_lines'])
    first=left+(total-count)//2
    levels=[float(Decimal(i)*spacing) for i in range(first,first+count)]
    return {'status':'ok','price':price,'step':step,'levels':levels,'capped':total>count,'settings':cfg,
            'spacing_state':{'auto':cfg['auto'],'anchor':anchor,'step':step,'auto_percent':cfg['auto_percent']}}


def candle(raw):
    if not isinstance(raw,dict): raise ValueError('invalid candle')
    stamp=integer(raw.get('time'),0,32503680000,'candle time')
    vals={key:number(raw.get(key),1e-12,1e12,'candle '+key) for key in ('open','high','low','close')}
    if vals['low']>min(vals['open'],vals['close']) or vals['high']<max(vals['open'],vals['close']) or vals['low']>vals['high']: raise ValueError('inconsistent OHLC')
    opened=raw.get('is_open',False)
    if type(opened) not in (bool,int) or opened not in (0,1): raise ValueError('invalid candle state')
    return {'time':stamp,**vals,'is_open':bool(opened)}


def bars(data,now,days):
    if 'candles' in data:
        rows=data['candles']
        if not isinstance(rows,list) or len(rows)>10000: raise ValueError('at most 10000 input candles')
        previous=-1
        for raw in rows:
            row=candle(raw)
            if row['time']<=previous or row['time']>now: raise ValueError('candles must be unique, ordered, and not in the future')
            previous=row['time'];yield row
    else:
        if data.get('symbol','XAUUSD')!='XAUUSD': raise ValueError('Other symbols require explicit candles')
        from market_data.data import connect
        db=connect()
        try:
            for raw in db.execute('SELECT time,open,high,low,close,is_open FROM candles WHERE time>=? AND time<=? ORDER BY time',(max(0,int(now)-(days+8)*86400),int(now))): yield candle(dict(raw))
        finally: db.close()


def merge(aggregate,row):
    if aggregate is None: return dict(row, count=1)
    aggregate['high']=max(aggregate['high'],row['high']);aggregate['low']=min(aggregate['low'],row['low']);aggregate['close']=row['close']
    aggregate['is_open']=aggregate['is_open'] or row['is_open'];aggregate['count']+=1
    return aggregate


def previous_result(kind,cfg,data,now):
    today=wall(now,cfg).date(); daily={}; sessions={}; chart={};total=0
    scan=cfg.get('scan_minutes',1)
    start=minute(cfg.get('session_start','00:00'));end=minute(cfg.get('session_end','00:00'))
    for row in bars(data,now,cfg['days']):
        local=wall(row['time'],cfg); day=local.date()
        daily[day]=merge(daily.get(day),row);total+=1
        # MT5 membership is determined by scan candle OPEN, not its overlap.
        block=local.replace(minute=(local.minute//scan)*scan,second=0,microsecond=0)
        m=block.hour*60+block.minute
        session_day=day
        inside=start<=m<end if end>start else m>=start or m<end
        if end<=start and m<end: session_day-=timedelta(days=1)
        if inside: sessions[session_day]=merge(sessions.get(session_day),row)
        key=row['time']//900*900
        chart[key]=merge(chart.get(key),row)
        if len(chart)>1500: del chart[next(iter(chart))]
    dates=sorted(d for d in daily if d<=today)
    # A day is a broker D1 date present in supplied history. Never assume a
    # missing Sunday/session was traded; previous trading date follows D1 data.
    targets=[d for d in dates if (d==today and cfg['draw_today']) or (d<today and cfg['draw_past'])][-cfg['days']:]
    result=[];missing=[]
    for target in targets:
        index=dates.index(target)
        if index==0: missing.append(target.isoformat());continue
        source_day=dates[index-1]
        source=(sessions if kind=='previous-day-session-levels' else daily).get(source_day)
        if source is None: missing.append(target.isoformat());continue
        begin=epoch(datetime.combine(target,datetime.min.time()),cfg)
        finish=epoch(datetime.combine(target+timedelta(days=1),datetime.min.time()),cfg)
        if begin is None or finish is None: missing.append(target.isoformat());continue
        values={key:source[key] for key in ('high','low','open','close')};values['mid']=(values['high']+values['low'])/2
        session_end=None
        if kind=='previous-day-session-levels':
            session_end=epoch(datetime.combine(source_day,datetime.min.time())+timedelta(minutes=end+(1440 if end<=start else 0)),cfg)
        result.append({'date':target.isoformat(),'source_date':source_day.isoformat(),'start':begin,'end':finish,
                       'provisional':bool(source['is_open'] or (session_end is not None and session_end>now)),
                       'sample_count':source['count'],'levels':{key:value for key,value in values.items() if cfg['show_'+key]}})
    return {'status':'ok' if result else 'insufficient_data','settings':cfg,'days':result,'missing_days':missing,
            'candles':[dict(v,time=k) for k,v in chart.items()], 'source':'provided_candles' if 'candles' in data else 'local_XAUUSD_M1',
            'source_candles':total,'coverage':'available_history_only','complete_history_verified':False,'styles':{key:{**value,**({'color':'#c4b5fd','style':'dash-dot' if key=='open' else value['style']} if kind=='previous-day-session-levels' else {}),**cfg['styles'].get(key,{})} for key,value in LEVEL_STYLES.items()}}


def run(kind,data):
    common={'settings','now','_state_owner','_state_slot'}
    extra={'price','visible_low','visible_high','spacing_state','symbol'} if kind=='round-levels' else {'candles','symbol'}
    if set(data)-common-extra: raise ValueError('unknown indicator input')
    cfg=settings(kind,data.get('settings'));now=timestamp(data.get('now',time.time()))
    if kind in ('session-clock','session-windows'):
        result=clock_result(cfg,now)
        if cfg['winter_utc_minutes'] is not None and (kind=='session-windows' or cfg['chart_point_lines']):
            result.update(session_chart(cfg,data,now))
        return result
    if kind=='round-levels':
        price=data.get('price')
        if price is None:
            from market_data.data import connect
            if data.get('symbol','XAUUSD')!='XAUUSD': raise ValueError('Other symbols require price')
            db=connect()
            try: row=db.execute('SELECT close,low,high FROM candles WHERE time<=? ORDER BY time DESC LIMIT 1',(now,)).fetchone()
            finally: db.close()
            if row is None: return {'status':'insufficient_data','settings':cfg,'levels':[]}
            price=row['close']
        number(price,1e-12,1e12,'price')
        calculate=lambda previous: round_result(cfg,price,data.get('visible_low',price*.97),data.get('visible_high',price*1.03),previous)
        owner,slot=data.get('_state_owner'),data.get('_state_slot')
        if owner and slot:
            result=[]
            def update(old):
                current=calculate(old);result.append(current)
                return current['spacing_state'], current['spacing_state']!=old
            change(owner,'round-spacing',slot,None,update)
            return result[0]
        return calculate(data.get('spacing_state'))
    return previous_result(kind,cfg,data,now)
