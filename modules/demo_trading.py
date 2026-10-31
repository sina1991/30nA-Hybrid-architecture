"""Transactional USD/XAUUSD paper broker; no real-money or executable input.

Prices are observed M1 closes interpreted as Bid with an explicitly simulated
spread. No unseen intra-bar tick sequence or broker execution is invented.
"""
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import threading
import time
from uuid import uuid4

DEFAULTS={'symbol':'XAUUSD','currency':'USD','position_mode':'hedging','leverage':100,'lots':0.01,
          'contract_size':100,'digits':2,'spread_points':20,'stop_level_points':0,'commission_per_lot':0,
          'swap_long_per_lot':0,'swap_short_per_lot':0,'swap_triple_day':2,'rollover_hour_utc':0,
          'margin_call_percent':100,'stop_out_percent':50}
ACTIVE=('pending','open')


class Conflict(ValueError):pass
class Unavailable(ValueError):pass
class RateLimited(PermissionError):pass


def dec(value,minimum=None,maximum=None):
    if type(value) not in (int,float,str,Decimal) or isinstance(value,bool):raise ValueError('Invalid number')
    try:number=Decimal(str(value))
    except InvalidOperation:raise ValueError('Invalid number') from None
    if not number.is_finite() or (minimum is not None and number<Decimal(str(minimum))) or (maximum is not None and number>Decimal(str(maximum))):raise ValueError('Number outside allowed range')
    return number


def cents(value):return int((dec(value)*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
def dollars(value):return float(Decimal(value)/100)
def tick(cfg):return Decimal(10)**(-cfg['digits'])


def configuration(raw=None):
    if raw is None:raw={}
    if not isinstance(raw,dict) or set(raw)-set(DEFAULTS):raise ValueError('Invalid demo settings')
    cfg={**DEFAULTS,**raw}
    if cfg['symbol']!='XAUUSD' or cfg['currency']!='USD' or cfg['position_mode']!='hedging':raise ValueError('Only XAUUSD / USD hedging is supported')
    for key,lo,hi in [('leverage',1,1000),('digits',2,5),('spread_points',0,10000),('stop_level_points',0,10000),('swap_triple_day',0,6),('rollover_hour_utc',0,23)]:
        if type(cfg[key]) is not int or not lo<=cfg[key]<=hi:raise ValueError('Invalid '+key)
    for key,lo,hi in [('lots',.01,100),('contract_size',1,100000),('commission_per_lot',0,1000),('swap_long_per_lot',-1000,1000),('swap_short_per_lot',-1000,1000),('margin_call_percent',1,1000),('stop_out_percent',1,1000)]:cfg[key]=float(dec(cfg[key],lo,hi))
    if dec(cfg['lots'])%Decimal('.01'):raise ValueError('Lot step is 0.01')
    if cfg['stop_out_percent']>cfg['margin_call_percent']:raise ValueError('Stop-out must not exceed margin call')
    return cfg


def owner_key(owner):
    if not isinstance(owner,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}',owner) or owner=='__legacy__':raise ValueError('Invalid owner')


@contextmanager
def database():
    root=Path(os.environ.get('DASHBOARD_MODULE_STATE_DIR','/var/lib/30na/dashboard')).resolve()
    checkout=Path(__file__).resolve().parents[1]
    if root==checkout or checkout in root.parents:raise OSError('Demo state must be outside checkout')
    root.mkdir(parents=True,exist_ok=True,mode=0o700);path=root/'demo-trading.sqlite3'
    if path.is_symlink():raise OSError('Invalid demo state')
    fd=os.open(path,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600);os.close(fd)
    db=sqlite3.connect(path,timeout=10,isolation_level=None);db.row_factory=sqlite3.Row
    try:
        db.execute('PRAGMA foreign_keys=ON')
        db.executescript('''CREATE TABLE IF NOT EXISTS demo_accounts (
          id TEXT PRIMARY KEY,owner TEXT NOT NULL,name TEXT NOT NULL,initial_cents INTEGER NOT NULL,balance_cents INTEGER NOT NULL,
          settings TEXT NOT NULL,pin_salt BLOB NOT NULL,pin_hash BLOB NOT NULL,pin_window REAL NOT NULL DEFAULT 0,pin_attempts INTEGER NOT NULL DEFAULT 0,
          created_at REAL NOT NULL,last_bid TEXT,last_quote_at REAL);
        CREATE INDEX IF NOT EXISTS demo_account_owner ON demo_accounts(owner);
        CREATE TABLE IF NOT EXISTS demo_preferences(owner TEXT PRIMARY KEY,active_account TEXT NOT NULL REFERENCES demo_accounts(id));
        CREATE TABLE IF NOT EXISTS demo_orders (
          id TEXT PRIMARY KEY,owner TEXT NOT NULL,account_id TEXT NOT NULL REFERENCES demo_accounts(id),side TEXT NOT NULL,status TEXT NOT NULL,
          order_type TEXT NOT NULL,entry_requested TEXT,entry_fill TEXT,sl TEXT NOT NULL,tp TEXT NOT NULL,volume TEXT NOT NULL,contract_size TEXT NOT NULL,
          leverage INTEGER NOT NULL,commission_rate TEXT NOT NULL,swap_rate TEXT NOT NULL,margin_cents INTEGER NOT NULL DEFAULT 0,
          commission_cents INTEGER NOT NULL DEFAULT 0,swap_cents INTEGER NOT NULL DEFAULT 0,profit_cents INTEGER NOT NULL DEFAULT 0,
          created_at REAL NOT NULL,opened_at REAL,closed_at REAL,close_price TEXT,close_reason TEXT,source TEXT NOT NULL,
          source_slot TEXT,show_on_chart INTEGER NOT NULL,request_id TEXT NOT NULL,signature TEXT NOT NULL,last_swap_day INTEGER,
          UNIQUE(owner,account_id,request_id));
        CREATE INDEX IF NOT EXISTS demo_order_scope ON demo_orders(owner,account_id,status);
        CREATE UNIQUE INDEX IF NOT EXISTS demo_request_owner ON demo_orders(owner,request_id);
        CREATE UNIQUE INDEX IF NOT EXISTS demo_active_slot ON demo_orders(owner,source_slot) WHERE source_slot IS NOT NULL AND status IN ('open','pending');
        CREATE TABLE IF NOT EXISTS demo_deals(id INTEGER PRIMARY KEY AUTOINCREMENT,owner TEXT NOT NULL,account_id TEXT NOT NULL,order_id TEXT,
          kind TEXT NOT NULL,amount_cents INTEGER NOT NULL,price TEXT,created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS demo_equity(owner TEXT NOT NULL,account_id TEXT NOT NULL,time INTEGER NOT NULL,equity_cents INTEGER NOT NULL,
          PRIMARY KEY(owner,account_id,time));''')
        db.execute('BEGIN IMMEDIATE');yield db;db.commit()
    finally:db.close()


def account(db,owner,ident=None):
    owner_key(owner)
    if ident is None:
        pref=db.execute('SELECT active_account FROM demo_preferences WHERE owner=?',(owner,)).fetchone()
        if not pref:raise LookupError('Create or select a demo account first')
        ident=pref[0]
    row=db.execute('SELECT * FROM demo_accounts WHERE id=? AND owner=?',(ident,owner)).fetchone()
    if not row:raise LookupError('Demo account not found')
    return dict(row)


def public_account(row):
    return {'id':row['id'],'name':row['name'],'initial_balance':dollars(row['initial_cents']),'balance':dollars(row['balance_cents']),
            'settings':json.loads(row['settings']),'created_at':row['created_at'],'trade_pin_set':True}


def pin_hash(pin,salt):return hashlib.scrypt(pin.encode(),salt=salt,n=16384,r=8,p=1,dklen=32)
def valid_pin(pin):return isinstance(pin,str) and re.fullmatch(r'[0-9]{4}',pin) is not None


def check_pin(db,row,pin):
    now=time.time();attempts=row['pin_attempts'] if now-row['pin_window']<900 else 0
    if attempts>=5:raise RateLimited('Trade PIN temporarily locked; try again after 15 minutes')
    if not valid_pin(pin) or not hmac.compare_digest(pin_hash(pin,row['pin_salt']),row['pin_hash']):
        db.execute('UPDATE demo_accounts SET pin_attempts=?,pin_window=? WHERE id=?',(attempts+1,row['pin_window'] if attempts else now,row['id']))
        db.commit();raise PermissionError('Invalid trade PIN')
    db.execute('UPDATE demo_accounts SET pin_attempts=0,pin_window=0 WHERE id=?',(row['id'],))


def create_account(owner,name,initial_balance,pin,settings=None):
    owner_key(owner)
    if not isinstance(name,str) or not name.strip() or len(name)>80 or any(ord(ch)<32 for ch in name):raise ValueError('Invalid demo account name')
    if type(initial_balance) is not int or initial_balance not in (1000,3000,5000):raise ValueError('Initial balance must be 1000, 3000 or 5000 USD')
    if not valid_pin(pin):raise ValueError('Trade PIN must contain four digits')
    cfg=configuration(settings)
    with database() as db:
        if db.execute('SELECT count(*) FROM demo_accounts WHERE owner=?',(owner,)).fetchone()[0]>=10:raise Conflict('Demo account limit reached')
        salt=secrets.token_bytes(16);digest=pin_hash(pin,salt)
        ident='demo-'+uuid4().hex
        db.execute('INSERT INTO demo_accounts(id,owner,name,initial_cents,balance_cents,settings,pin_salt,pin_hash,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(ident,owner,name.strip(),initial_balance*100,initial_balance*100,json.dumps(cfg),salt,digest,time.time()))
        db.execute('INSERT INTO demo_preferences VALUES(?,?) ON CONFLICT(owner) DO UPDATE SET active_account=excluded.active_account',(owner,ident))
        return public_account(account(db,owner,ident))


def select_account(owner,ident):
    with database() as db:
        row=account(db,owner,ident)
        db.execute('INSERT INTO demo_preferences VALUES(?,?) ON CONFLICT(owner) DO UPDATE SET active_account=excluded.active_account',(owner,ident))
        return public_account(row)


def update_settings(owner,ident,raw):
    cfg=configuration(raw)
    with database() as db:
        account(db,owner,ident)
        if db.execute("SELECT 1 FROM demo_orders WHERE owner=? AND account_id=? AND status IN ('open','pending')",(owner,ident)).fetchone():raise Conflict('Close positions and cancel pending orders before changing trading settings')
        db.execute('UPDATE demo_accounts SET settings=? WHERE owner=? AND id=?',(json.dumps(cfg),owner,ident))
        return public_account(account(db,owner,ident))


def set_pin(owner,ident,pin):
    if not valid_pin(pin):raise ValueError('Trade PIN must contain four digits')
    with database() as db:
        account(db,owner,ident)
        salt=secrets.token_bytes(16);digest=pin_hash(pin,salt)
        db.execute('UPDATE demo_accounts SET pin_salt=?,pin_hash=?,pin_attempts=0,pin_window=0 WHERE id=?',(salt,digest,ident))
    return {'updated':True}


def observed_quote(cfg):
    from market_data.data import connect
    db=connect()
    try:
        row=db.execute('SELECT time,close FROM candles ORDER BY time DESC LIMIT 1').fetchone()
        meta=dict(db.execute("SELECT key,value FROM collector_status WHERE key IN ('last_success','error')").fetchall())
    finally:db.close()
    now=time.time()
    if not row or not meta.get('last_success'):
        raise Unavailable('No market data received yet. Check the XAUUSD chart and Dashboard collector logs; no demo execution was performed.')
    if meta.get('error'):
        raise Unavailable('Market data collector could not fetch prices. Check Dashboard collector logs and upstream connectivity; no demo execution was performed.')
    try: fetched=float(meta['last_success']); candle_time=float(row['time'])
    except (ValueError,TypeError,OverflowError):
        raise Unavailable('Invalid market data timestamps; no demo execution was performed') from None
    if not -5<=now-fetched<=30:
        raise Unavailable('Market data collector is not current (30-second limit). Check Dashboard collector logs and server UTC clock; no demo execution was performed.')
    if not -5<=now-candle_time<=120:
        from datetime import datetime, timezone
        last=datetime.fromtimestamp(candle_time,timezone.utc).isoformat() if 0<=candle_time<=253402214400 else 'invalid timestamp'
        raise Unavailable(f'Latest XAUUSD candle: {last}; a candle within 120 seconds is required. The market may be closed or the feed delayed. Trading resumes automatically with fresh data; no demo execution was performed.')
    bid=dec(row['close'],.01,1000000000).quantize(tick(cfg),rounding=ROUND_HALF_UP);ask=bid+cfg['spread_points']*tick(cfg)
    return {'bid':str(bid),'ask':str(ask),'time':float(meta['last_success']),'source':'XAUUSD sampled candle close + simulated spread','simulated_spread':True}


def orders(db,row,status=None):
    query='SELECT * FROM demo_orders WHERE owner=? AND account_id=?';args=[row['owner'],row['id']]
    if status:query+=' AND status=?';args.append(status)
    return [dict(r) for r in db.execute(query+' ORDER BY created_at,id',args)]


def floating(order,quote):
    price=dec(quote['bid'] if order['side']=='buy' else quote['ask'])
    return cents((price-dec(order['entry_fill']))*(1 if order['side']=='buy' else -1)*dec(order['volume'])*dec(order['contract_size']))


def metrics(db,row,quote):
    opened=orders(db,row,'open');unrealized=sum(floating(order,quote) for order in opened) if quote else 0
    used=sum(o['margin_cents'] for o in opened);equity=row['balance_cents']+unrealized
    level=float(Decimal(equity)*100/used) if used else None;cfg=json.loads(row['settings'])
    return {'balance':dollars(row['balance_cents']),'equity':dollars(equity),'floating_pnl':dollars(unrealized),'used_margin':dollars(used),'free_margin':dollars(equity-used),
            'margin_level':level,'margin_call':level is not None and level<cfg['margin_call_percent'],'open_positions':len(opened),'quote_available':quote is not None and not quote.get('stale',False)}


def free_cents(db,row,quote):
    opened=orders(db,row,'open')
    return row['balance_cents']+sum(floating(order,quote) for order in opened)-sum(order['margin_cents'] for order in opened)


def deal(db,row,order,kind,amount,price=None):
    db.execute('INSERT INTO demo_deals(owner,account_id,order_id,kind,amount_cents,price,created_at) VALUES(?,?,?,?,?,?,?)',(row['owner'],row['id'],order['id'],kind,amount,price,time.time()))
    db.execute('UPDATE demo_accounts SET balance_cents=balance_cents+? WHERE id=?',(amount,row['id']));row['balance_cents']+=amount


def close_fill(db,row,order,quote,reason):
    price=quote['bid'] if order['side']=='buy' else quote['ask'];gross=floating(order,quote)
    total_fee=cents(dec(order['commission_rate'])*dec(order['volume']));fee=total_fee-order['commission_cents']
    profit=gross-total_fee+order['swap_cents']
    db.execute("UPDATE demo_orders SET status='closed',closed_at=?,close_price=?,close_reason=?,profit_cents=?,commission_cents=?,margin_cents=0 WHERE id=?",(time.time(),price,reason,profit,total_fee,order['id']))
    deal(db,row,order,'close',gross-fee,price)


def fill(db,row,order,quote):
    price=dec(quote['ask'] if order['side']=='buy' else quote['bid']);cfg=json.loads(row['settings'])
    margin=max(1,cents(price*dec(order['volume'])*dec(order['contract_size'])/order['leverage']))
    fee=cents(dec(order['commission_rate'])*dec(order['volume'])/2)
    spread_loss=cents((dec(quote['ask'])-dec(quote['bid']))*dec(order['volume'])*dec(order['contract_size']))
    free=free_cents(db,row,quote)
    if free<margin+fee+spread_loss:return False
    now=time.time();day=int((now-cfg['rollover_hour_utc']*3600)//86400)
    db.execute("UPDATE demo_orders SET status='open',entry_fill=?,opened_at=?,margin_cents=?,commission_cents=?,last_swap_day=? WHERE id=?",(str(price),now,margin,fee,day,order['id']))
    deal(db,row,order,'open',-fee,str(price));return True


def process(db,row,quote):
    cfg=json.loads(row['settings']);now=time.time();day=int((now-cfg['rollover_hour_utc']*3600)//86400)
    for order in orders(db,row,'open'):
        last=order['last_swap_day'] or day
        if day>last:
            # Charge weekdays; configured triple-rollover weekday contributes 3.
            weeks,remainder=divmod(day-last,7);weight=weeks*(7 if cfg['swap_triple_day']<5 else 5)
            for index in range(1,remainder+1):
                weekday=(last+index+3)%7
                weight+=0 if weekday>=5 else 3 if weekday==cfg['swap_triple_day'] else 1
            amount=cents(dec(order['swap_rate'])*dec(order['volume']))*weight
            db.execute('UPDATE demo_orders SET swap_cents=swap_cents+?,last_swap_day=? WHERE id=?',(amount,day,order['id']))
            if amount:deal(db,row,order,'swap',amount)
    for order in orders(db,row,'pending'):
        price=dec(quote['ask'] if order['side']=='buy' else quote['bid']);entry=dec(order['entry_requested'])
        trigger=price<=entry if order['order_type'] in ('buy_limit','sell_stop') else price>=entry
        if trigger:
            # Gap fills may no longer have sensible SL/TP brackets. Reject
            # rather than manufacture a fill at an unobserved entry price.
            sl,tp=dec(order['sl']),dec(order['tp'])
            valid=sl<price<tp if order['side']=='buy' else tp<price<sl
            if not valid or not fill(db,row,order,quote):db.execute("UPDATE demo_orders SET status='rejected',closed_at=?,close_reason=? WHERE id=?",(now,'price_gap_or_insufficient_margin',order['id']))
    for order in orders(db,row,'open'):
        price=dec(quote['bid'] if order['side']=='buy' else quote['ask']);sl,tp=dec(order['sl']),dec(order['tp'])
        stopped=price<=sl if order['side']=='buy' else price>=sl;taken=price>=tp if order['side']=='buy' else price<=tp
        if stopped or taken:close_fill(db,row,order,quote,'stop_loss' if stopped else 'take_profit')
    while True:
        opened=orders(db,row,'open');used=sum(order['margin_cents'] for order in opened)
        equity=row['balance_cents']+sum(floating(order,quote) for order in opened)
        if not used or Decimal(equity)*100>dec(cfg['stop_out_percent'])*used:break
        if not opened:break
        close_fill(db,row,min(opened,key=lambda o:floating(o,quote)),quote,'stop_out')
    db.execute('UPDATE demo_accounts SET last_bid=?,last_quote_at=? WHERE id=?',(quote['bid'],quote['time'],row['id']))
    current=metrics(db,row,quote)
    db.execute('INSERT INTO demo_equity VALUES(?,?,?,?) ON CONFLICT(owner,account_id,time) DO UPDATE SET equity_cents=excluded.equity_cents',(row['owner'],row['id'],int(now)//60*60,row['balance_cents']+sum(floating(order,quote) for order in orders(db,row,'open'))))


def price_value(value,cfg):
    number=dec(value,.01,1000000000)
    if number%tick(cfg):raise ValueError('Price does not match configured digits')
    return number


def public_order(row,quote=None):
    result={key:row[key] for key in ('id','account_id','side','status','order_type','created_at','opened_at','closed_at','close_reason','source','source_slot','show_on_chart','request_id')}
    for key in ('entry_requested','entry_fill','sl','tp','volume','close_price'):result[key]=float(dec(row[key])) if row[key] is not None else None
    result.update(profit=dollars(row['profit_cents']),commission=dollars(row['commission_cents']),swap=dollars(row['swap_cents']),margin=dollars(row['margin_cents']))
    result['floating_pnl']=dollars(floating(row,quote)) if row['status']=='open' and quote else None
    return result


def submit(owner,data,source='manual',source_slot=None):
    if not isinstance(data,dict):raise ValueError('Invalid demo trade')
    data=dict(data)
    for alias,target in [('price','entry'),('tradePIN','trade_pin'),('ACTION','action')]:
        if alias in data:
            if target in data:raise ValueError('Duplicate trade fields')
            data[target]=data.pop(alias)
    if 'action' in data:
        if 'entry' in data or 'side' in data or not isinstance(data['action'],str) or data['action'].lower() not in ('buy','sell'):raise ValueError('ACTION must be BUY or SELL, without price')
        data['action']=data['action'].lower()
    allowed={'account_id','entry','sl','tp','side','action','trade_pin','request_id','show_on_chart'}
    if not isinstance(data,dict) or set(data)-allowed or source not in ('manual','bot','worker'):raise ValueError('Invalid demo trade')
    key=data.get('request_id') or str(uuid4());data['request_id']=key
    if not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9._:-]{8,128}',key):raise ValueError('A unique request_id is required')
    if type(data.get('show_on_chart',True)) is not bool:raise ValueError('Invalid chart flag')
    if source_slot is not None and (not isinstance(source_slot,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}',source_slot)):raise ValueError('Invalid source slot')
    with database() as db:
        previous=db.execute('SELECT * FROM demo_orders WHERE owner=? AND request_id=?',(owner,key)).fetchone()
        row=account(db,owner,data.get('account_id') or (previous['account_id'] if previous else None));cfg=json.loads(row['settings'])
        data['account_id']=row['id'];data.setdefault('show_on_chart',True)
        if source in ('bot','worker'):check_pin(db,row,data.get('trade_pin'))
        signature=hashlib.sha256(json.dumps({**{k:v for k,v in data.items() if k!='trade_pin'},'_source':source,'_slot':source_slot},sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        existing=previous
        if existing:
            if existing['signature']!=signature:raise Conflict('request_id was already used with different trade parameters')
            return {'trade':public_order(dict(existing)),'request_id':key,'replayed':True}
        quote=observed_quote(cfg);process(db,row,quote)
        if source_slot and db.execute("SELECT 1 FROM demo_orders WHERE owner=? AND source_slot=? AND status IN ('open','pending')",(owner,source_slot)).fetchone():raise Conflict('This trade slot already has an active trade')
        if db.execute("SELECT count(*) FROM demo_orders WHERE account_id=? AND status IN ('open','pending')",(row['id'],)).fetchone()[0]>=100:raise Conflict('Active order limit reached')
        sl,tp=price_value(data.get('sl'),cfg),price_value(data.get('tp'),cfg)
        market=source=='manual' or 'action' in data
        if market:
            if 'entry' in data or (source=='manual' and 'trade_pin' in data):raise ValueError('Manual entry uses the current observed market price')
            side=data.get('action',data.get('side'))
            if side not in ('buy','sell'):raise ValueError('Side must be buy or sell')
            entry=dec(quote['ask'] if side=='buy' else quote['bid']);order_type='market'
        else:
            entry=price_value(data.get('entry'),cfg);side='buy' if sl<entry<tp else 'sell' if tp<entry<sl else None
            if side is None or data.get('side',side)!=side:raise ValueError('SL and TP must bracket entry and agree with side')
            current=dec(quote['ask'] if side=='buy' else quote['bid'])
            order_type=('buy_limit' if entry<current else 'buy_stop') if side=='buy' else ('sell_limit' if entry>current else 'sell_stop')
        if not (sl<entry<tp if side=='buy' else tp<entry<sl):raise ValueError('Invalid SL / TP direction')
        distance=cfg['stop_level_points']*tick(cfg)
        if min(abs(entry-sl),abs(entry-tp))<distance:raise ValueError('SL or TP is closer than Stop Level')
        if market:
            closing=dec(quote['bid'] if side=='buy' else quote['ask'])
            if (side=='buy' and sl>=closing) or (side=='sell' and sl<=closing) or min(abs(closing-sl),abs(closing-tp))<distance:raise ValueError('Stops violate the current closing-side quote or Stop Level')
        ident='trade-'+uuid4().hex
        db.execute('''INSERT INTO demo_orders(id,owner,account_id,side,status,order_type,entry_requested,sl,tp,volume,contract_size,leverage,commission_rate,swap_rate,created_at,source,source_slot,show_on_chart,request_id,signature)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(ident,owner,row['id'],side,'pending',order_type,str(entry),str(sl),str(tp),str(cfg['lots']),str(cfg['contract_size']),cfg['leverage'],str(cfg['commission_per_lot']),str(cfg['swap_long_per_lot'] if side=='buy' else cfg['swap_short_per_lot']),time.time(),source,source_slot,int(data.get('show_on_chart',True)),key,signature))
        order=dict(db.execute('SELECT * FROM demo_orders WHERE id=?',(ident,)).fetchone())
        if market:
            if not fill(db,row,order,quote):raise Conflict('Insufficient free margin')
        else:
            required=max(1,cents(entry*dec(order['volume'])*dec(order['contract_size'])/order['leverage']))
            if required>free_cents(db,row,quote):raise Conflict('Insufficient free margin for pending order')
        process(db,row,quote)
        result=dict(db.execute('SELECT * FROM demo_orders WHERE id=?',(ident,)).fetchone())
        return {'trade':public_order(result,quote),'request_id':key,'replayed':False}


def alter_order(owner,ident,action,value=None):
    if action not in ('close','cancel','chart'):raise ValueError('Invalid trade action')
    with database() as db:
        found=db.execute('SELECT * FROM demo_orders WHERE id=? AND owner=?',(ident,owner)).fetchone()
        if not found:raise LookupError('Trade not found')
        order=dict(found);row=account(db,owner,order['account_id'])
        if action=='chart':
            if type(value) is not bool:raise ValueError('Invalid chart flag')
            db.execute('UPDATE demo_orders SET show_on_chart=? WHERE id=?',(int(value),ident))
        elif order['status'] in ACTIVE:
            if action=='cancel':
                if order['status']!='pending':raise Conflict('Only pending orders can be cancelled')
                db.execute("UPDATE demo_orders SET status='cancelled',closed_at=?,close_reason='user_cancel' WHERE id=?",(time.time(),ident))
            else:
                quote=observed_quote(json.loads(row['settings']));process(db,row,quote)
                order=dict(db.execute('SELECT * FROM demo_orders WHERE id=?',(ident,)).fetchone())
                if order['status']=='pending':raise Conflict('Cancel a pending order instead')
                if order['status']=='open':close_fill(db,row,order,quote,'user_close')
        return public_order(dict(db.execute('SELECT * FROM demo_orders WHERE id=?',(ident,)).fetchone()))


def state(owner,account_id=None,source_slot=None):
    owner_key(owner)
    with database() as db:
        summaries=[public_account(dict(row)) for row in db.execute('SELECT * FROM demo_accounts WHERE owner=? ORDER BY created_at',(owner,))]
        if not summaries and account_id is not None:account(db,owner,account_id)
        if not summaries:return {'accounts':[],'account':None,'quote':None,'metrics':None,'orders':[],'model':'Sampled-price paper trading; no MT5 broker connection'}
        if source_slot and account_id is None:
            active=db.execute("SELECT account_id FROM demo_orders WHERE owner=? AND source_slot=? AND status IN ('open','pending') LIMIT 1",(owner,source_slot)).fetchone()
            if active:account_id=active[0]
        row=account(db,owner,account_id);cfg=json.loads(row['settings']);quote=None;message=''
        try:quote=observed_quote(cfg);process(db,row,quote)
        except Unavailable as exc:message=str(exc)
        if quote is None and row['last_bid']:
            quote={'bid':row['last_bid'],'ask':str(dec(row['last_bid'])+cfg['spread_points']*tick(cfg)),'time':row['last_quote_at'],'stale':True,'source':'Last observed demo quote','simulated_spread':True}
        items=orders(db,row)
        if source_slot:items=[order for order in items if order['source_slot']==source_slot]
        active_items=[order for order in items if order['status'] in ACTIVE]
        finished=[order for order in items if order['status'] not in ACTIVE]
        visible=sorted(active_items+finished[-500:],key=lambda order:(order['created_at'],order['id']))
        return {'history_truncated':len(finished)>500,'accounts':[public_account(row) if item['id']==row['id'] else item for item in summaries],'account':public_account(row),'quote':quote,'metrics':metrics(db,row,quote),'orders':[public_order(order,quote) for order in visible],
                'message':message,'model':'Sampled-price paper trading; synthetic spread; no unseen tick replay'}


def report(owner,account_id=None,since=0,until=None):
    since=float(dec(since,0,4102444800));until=float(dec(time.time() if until is None else until,since,4102444800))
    with database() as db:
        row=account(db,owner,account_id)
        closed=[dict(r) for r in db.execute("SELECT * FROM demo_orders WHERE owner=? AND account_id=? AND status='closed' AND closed_at>=? AND closed_at<=? ORDER BY closed_at",(owner,row['id'],since,until))]
        wins=[o['profit_cents'] for o in closed if o['profit_cents']>0];losses=[o['profit_cents'] for o in closed if o['profit_cents']<0]
        equity=[dict(r) for r in db.execute('SELECT time,equity_cents FROM demo_equity WHERE owner=? AND account_id=? AND time>=? AND time<=? ORDER BY time',(owner,row['id'],since,until))]
        peak=row['initial_cents'] if since<=row['created_at'] or not equity else equity[0]['equity_cents'];drawdown=0
        for point in equity:peak=max(peak,point['equity_cents']);drawdown=max(drawdown,peak-point['equity_cents'])
        daily={}
        for order in closed:
            day=time.strftime('%Y-%m-%d',time.gmtime(order['closed_at']));daily[day]=daily.get(day,0)+order['profit_cents']
        return {'account_id':row['id'],'since':since,'until':until,'trades':len(closed),'wins':len(wins),'losses':len(losses),'win_rate':len(wins)*100/len(closed) if closed else 0,
                'net_profit':dollars(sum(o['profit_cents'] for o in closed)),'gross_profit':dollars(sum(wins)),'gross_loss':dollars(sum(losses)),
                'profit_factor':sum(wins)/abs(sum(losses)) if losses else None,'average_win':dollars(sum(wins))/len(wins) if wins else 0,'average_loss':dollars(sum(losses))/len(losses) if losses else 0,
                'by_side':[{'side':side,'trades':sum(o['side']==side for o in closed),'profit':dollars(sum(o['profit_cents'] for o in closed if o['side']==side))} for side in ('buy','sell')],
                'by_source':[{'source':source,'trades':sum(o['source']==source for o in closed),'profit':dollars(sum(o['profit_cents'] for o in closed if o['source']==source))} for source in ('manual','bot','worker')],
                'expectancy':dollars(sum(o['profit_cents'] for o in closed))/len(closed) if closed else 0,
                'commissions':dollars(sum(o['commission_cents'] for o in closed)),'swap':dollars(sum(o['swap_cents'] for o in closed)),
                'max_drawdown':dollars(drawdown),'drawdown_basis':'Observed minute equity samples','daily':[{'date':day,'profit':dollars(value)} for day,value in sorted(daily.items())],
                'equity':[{'time':point['time'],'equity':dollars(point['equity_cents'])} for point in equity[-5000:]],'history_truncated':len(closed)>5000,'history':[public_order(o) for o in closed[-5000:]]}


class DemoScheduler:
    def __init__(self):self.stop_event=threading.Event();self.thread=None
    def start(self):
        if self.thread is None:self.thread=threading.Thread(target=self.loop,name='30na-demo-risk',daemon=True);self.thread.start()
    def stop(self):
        self.stop_event.set()
        if self.thread:self.thread.join(timeout=3)
    def loop(self):
        import logging
        while not self.stop_event.is_set():
            try:
                with database() as db:active=[tuple(r) for r in db.execute("SELECT DISTINCT owner,account_id FROM demo_orders WHERE status IN ('open','pending')")]
                for owner,ident in active:
                    if self.stop_event.is_set():break
                    try:
                        with database() as db:
                            row=account(db,owner,ident);quote=observed_quote(json.loads(row['settings']));process(db,row,quote)
                    except (Unavailable,sqlite3.Error,OSError):pass
            except (OSError,sqlite3.Error,ValueError):logging.getLogger(__name__).warning('Demo risk processing unavailable')
            self.stop_event.wait(1)
