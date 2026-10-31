"""Paper-broker accounting, ownership, order execution and replay boundaries."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
import json
import sqlite3
import time
import pytest
from modules import demo_trading as demo
from modules import demo_components,slots,slot_workers
from test_account_chat_api import client,create_accounts,auth


@pytest.fixture
def market(tmp_path,monkeypatch):
    monkeypatch.setenv('DASHBOARD_MODULE_STATE_DIR',str(tmp_path))
    values={'bid':100,'now':time.time()}
    def quote(cfg):return {'bid':str(values['bid']),'ask':str(demo.dec(values['bid'])+cfg['spread_points']*demo.tick(cfg)),'time':values['now'],'source':'fixture'}
    monkeypatch.setattr(demo,'observed_quote',quote)
    return values


def new(owner='alice',settings=None):return demo.create_account(owner,'Test',1000,'0123',settings)
def trade(**extra):return {'side':'buy','sl':90,'tp':120,'request_id':'request-0001',**extra}


def test_buy_spread_margin_commission_and_close_ledger(market):
    a=new(settings={'commission_per_lot':4})
    result=demo.submit('alice',trade(),source_slot='trade-slot')['trade']
    assert result['entry_fill']==100.2 and result['volume']==.01 and result['status']=='open'
    state=demo.state('alice');assert state['metrics']['balance']==999.98 and state['metrics']['equity']==999.78 and state['metrics']['used_margin']==1
    market['bid']=110
    closed=demo.alter_order('alice',result['id'],'close')
    assert closed['profit']==9.76 and closed['commission']==.04
    assert demo.state('alice')['metrics']['balance']==1009.76
    report=demo.report('alice');assert report['net_profit']==9.76 and report['wins']==1 and report['win_rate']==100 and report['profit_factor'] is None
    with demo.database() as db:assert db.execute('SELECT sum(amount_cents) FROM demo_deals WHERE account_id=?',(a['id'],)).fetchone()[0]==976


def test_sell_and_both_bot_contracts(market):
    new()
    sell=demo.submit('alice',{'ACTION':'SELL','sl':110,'tp':90,'tradePIN':'0123','request_id':'market-bot-1'},'bot')['trade']
    assert sell['entry_fill']==100 and sell['side']=='sell' and sell['status']=='open'
    market['bid']=95
    assert demo.alter_order('alice',sell['id'],'close')['profit']==4.8
    pending=demo_components.run('demo-bot',{'_state_owner':'alice','price':90,'sl':80,'tp':110,'tradePIN':'0123','request_id':'price-bot-1'})['trade']
    assert pending['status']=='pending' and pending['order_type']=='buy_limit'
    market['bid']=89.5
    state=demo.state('alice');filled=next(o for o in state['orders'] if o['id']==pending['id'])
    assert filled['status']=='open' and filled['entry_fill']==89.7


def test_pending_sell_stop_triggers_and_stop_loss_uses_observed_gap_price(market):
    new()
    p=demo.submit('alice',{'price':95,'sl':105,'tp':80,'tradePIN':'0123'},'bot')['trade'];assert p['order_type']=='sell_stop'
    market['bid']=94
    assert next(o for o in demo.state('alice')['orders'] if o['id']==p['id'])['entry_fill']==94
    market['bid']=107
    closed=next(o for o in demo.state('alice')['orders'] if o['id']==p['id'])
    assert closed['status']=='closed' and closed['close_reason']=='stop_loss' and closed['close_price']==107.2


def test_take_profit_and_invalid_pending_gap(market):
    new();a=demo.submit('alice',trade())['trade'];market['bid']=121
    closed=next(o for o in demo.state('alice')['orders'] if o['id']==a['id']);assert closed['close_reason']=='take_profit' and closed['close_price']==121
    p=demo.submit('alice',{'price':100,'sl':95,'tp':110,'tradePIN':'0123'},'bot')['trade'];market['bid']=90
    assert next(o for o in demo.state('alice')['orders'] if o['id']==p['id'])['status']=='rejected'


def test_ownership_idempotency_slot_uniqueness_and_settings_lock(market):
    a=new();b=new('bob');result=demo.submit('alice',trade(account_id=a['id']),source_slot='slot-a')
    assert demo.submit('alice',trade(account_id=a['id']),source_slot='slot-a')['trade']['id']==result['trade']['id']
    with pytest.raises(demo.Conflict):demo.submit('alice',trade(account_id=a['id'],tp=130),source_slot='slot-a')
    with pytest.raises(demo.Conflict):demo.submit('alice',trade(request_id='different-id',account_id=a['id']),source_slot='slot-a')
    with pytest.raises(LookupError):demo.alter_order('bob',result['trade']['id'],'close')
    with pytest.raises(LookupError):demo.state('bob',a['id'])
    with pytest.raises(demo.Conflict):demo.update_settings('alice',a['id'],{'lots':1})
    assert demo.state('bob',b['id'])['orders']==[]


def test_parallel_replay_creates_one_order(market):
    new()
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(lambda _:demo.submit('alice',trade()),range(4)))
    assert len({r['trade']['id'] for r in results})==1 and len(demo.state('alice')['orders'])==1


def test_pin_hash_rate_limit_and_no_secret_in_public_results(market):
    a=new();assert 'pin_hash' not in a and 'pin_salt' not in a
    for _ in range(5):
        with pytest.raises(PermissionError):demo.submit('alice',{'price':95,'sl':90,'tp':110,'tradePIN':'9999'},'bot')
    with pytest.raises(demo.RateLimited):demo.submit('alice',{'price':95,'sl':90,'tp':110,'tradePIN':'0123'},'bot')
    with demo.database() as db:
        row=db.execute('SELECT pin_hash,pin_salt,pin_attempts FROM demo_accounts WHERE id=?',(a['id'],)).fetchone();assert row['pin_hash']!=b'0123' and row['pin_attempts']==5
    demo.set_pin('alice',a['id'],'0456')
    result=demo.submit('alice',{'ACTION':'BUY','sl':90,'tp':110,'tradePIN':'0456'},'bot');assert 'tradePIN' not in json.dumps(result) and 'pin_hash' not in json.dumps(result)


def test_insufficient_margin_rolls_back_and_stop_out_liquidates(market):
    a=new(settings={'lots':1,'leverage':1})
    with pytest.raises(demo.Conflict):demo.submit('alice',trade())
    assert demo.state('alice')['orders']==[] and demo.state('alice')['metrics']['balance']==1000
    demo.update_settings('alice',a['id'],{'lots':1,'leverage':20,'spread_points':0})
    opened=demo.submit('alice',trade(sl=1,tp=200))['trade'];market['bid']=92
    closed=next(o for o in demo.state('alice')['orders'] if o['id']==opened['id']);assert closed['close_reason']=='stop_out' and closed['status']=='closed'


def test_swap_triple_day_and_repeated_reads_are_not_double_charged(market,monkeypatch):
    t=datetime(2026,10,27,12,tzinfo=timezone.utc).timestamp();monkeypatch.setattr(demo.time,'time',lambda:t)
    new(settings={'swap_long_per_lot':-2});demo.submit('alice',trade())
    t+=86400;demo.state('alice');first=demo.state('alice')['metrics']['balance'];assert first==999.94
    assert demo.state('alice')['metrics']['balance']==first


def test_stale_quotes_block_mutation_without_fabricated_execution(market,monkeypatch):
    a=new();demo.submit('alice',trade())
    monkeypatch.setattr(demo,'observed_quote',lambda cfg:(_ for _ in ()).throw(demo.Unavailable('offline')))
    with pytest.raises(demo.Unavailable):demo.submit('alice',trade(request_id='another-key'))
    with pytest.raises(demo.Unavailable):demo.alter_order('alice',demo.state('alice')['orders'][0]['id'],'close')
    state=demo.state('alice');assert state['quote']['stale'] and not state['metrics']['quote_available'] and state['orders'][0]['status']=='open'


@pytest.mark.parametrize('data',[{'side':'buy','sl':110,'tp':90},{'side':'buy','sl':float('nan'),'tp':110},{'side':'buy','sl':90.001,'tp':110}])
def test_invalid_price_directions_and_precision(market,data):
    new()
    with pytest.raises(ValueError):demo.submit('alice',data)


def test_api_bot_aliases_owner_scope_csv_and_scheduler_secret_policy(client,monkeypatch):
    (alice,a),(bob,b),_=create_accounts(client)
    monkeypatch.setattr(demo,'observed_quote',lambda cfg:{'bid':'100','ask':'100.2','time':time.time()})
    response=client.post('/api/upstreams/demo/accounts',headers=auth(a),json={'name':'Alice demo','initial_balance':3000,'tradePIN':'0123'})
    assert response.status_code==200,response.text
    account=response.json()['payload']['account'];assert account['balance']==3000 and 'pin_hash' not in account
    sid=slots.create(alice['id'])['slot'];slots.bind_active(alice['id'],sid,'demo-trade',{})
    response=client.post('/api/upstreams/demo/trades',headers=auth(a),json={'side':'buy','sl':90,'tp':110,'slot_id':sid,'request_id':'api-request-1'})
    assert response.status_code==200,response.text
    trade_id=response.json()['payload']['trade']['id']
    assert client.post('/api/upstreams/demo/trades/'+trade_id+'/close',headers=auth(b),json={}).status_code==404
    bot=client.post('/api/upstreams/demo/bot',headers=auth(a),json={'price':95,'sl':90,'tp':110,'tradePIN':'0123'})
    assert bot.status_code==200 and bot.json()['payload']['trade']['status']=='pending'
    assert client.get('/api/upstreams/demo/state?account_id='+account['id'],headers=auth(b)).status_code==404
    assert client.get('/api/upstreams/demo/state').status_code==401
    assert client.post('/api/upstreams/slots/'+sid+'/read',headers=auth(b),json={'module_id':'demo-trade'}).status_code==404
    assert client.post('/api/upstreams/demo/trades/'+trade_id+'/close',headers=auth(a),json={}).status_code==200
    csv=client.get('/api/upstreams/demo/report.csv',headers=auth(a));assert csv.status_code==200 and trade_id in csv.text and 'tradePIN' not in csv.text and 'pin_hash' not in csv.text
    assert client.get('/api/upstreams/demo/report.csv',headers=auth(b)).status_code==404
    bot_slot=slots.create(alice['id'])['slot'];slots.bind_active(alice['id'],bot_slot,'demo-bot',{})
    with pytest.raises(ValueError):slot_workers.configure(alice['id'],bot_slot,{'enabled':True,'kind':'task','interval_seconds':60,'input':{'price':95,'sl':90,'tp':110,'tradePIN':'0123'}})


def test_worker_result_bridge_uses_owner_credential_and_refuses_pin_in_output(tmp_path,monkeypatch):
    import hashlib
    from fastapi.testclient import TestClient
    from dashboard.app import create_app
    from public_api import ConsumerAPIError
    monkeypatch.setenv('DASHBOARD_MODULE_STATE_DIR',str(tmp_path))
    monkeypatch.setattr(demo,'observed_quote',lambda cfg:{'bid':'100','ask':'100.2','time':time.time()})
    creds=tmp_path/'credentials.json';creds.write_text(json.dumps({hashlib.sha256(b'fixture-a').hexdigest():'alice',hashlib.sha256(b'fixture-b').hexdigest():'bob'}))
    job={'status':'succeeded','result':{'status':'succeeded','result':{'demo_trade':{'ACTION':'BUY','sl':90,'tp':110}}}}
    seen=[]
    class Adapter:
        def __init__(self,owner):self.owner=owner
        def get(self,path):
            if self.owner!='alice':raise ConsumerAPIError('NOT_FOUND','Not found',404)
            return job
    def factory(owner,token):seen.append((owner,token));return {'worker-manager':Adapter(owner)}
    c=TestClient(create_app(credential_path=creds,upstream_factory=factory));new('alice');new('bob')
    payload={'execution_id':'11111111-1111-4111-8111-111111111111','tradePIN':'0123'}
    response=c.post('/api/upstreams/demo/from-execution',headers=auth('fixture-a'),json=payload)
    assert response.status_code==200,response.text
    assert response.json()['payload']['trade']['source']=='worker' and seen[-1]==('alice','fixture-a')
    replay=c.post('/api/upstreams/demo/from-execution',headers=auth('fixture-a'),json=payload)
    assert replay.json()['payload']['replayed']
    assert c.post('/api/upstreams/demo/from-execution',headers=auth('fixture-b'),json=payload).status_code==404
    job['result']['result']['demo_trade']['tradePIN']='0123'
    assert c.post('/api/upstreams/demo/from-execution',headers=auth('fixture-a'),json=payload).status_code==422


def test_quote_adapter_requires_current_collector_and_prices(tmp_path,monkeypatch):
    monkeypatch.setenv('DASHBOARD_MODULE_STATE_DIR',str(tmp_path))
    from market_data.data import connect
    db=connect();now=time.time()
    with db:
        db.execute('INSERT INTO candles(time,open,high,low,close,is_open) VALUES(?,?,?,?,?,?)',(int(now)//60*60,2000,2000,2000,2000,1))
        db.execute("INSERT OR REPLACE INTO collector_status VALUES('last_success',?)",(str(now),))
    db.close();quote=demo.observed_quote(demo.configuration());assert quote['bid']=='2000.00' and quote['ask']=='2000.20'
    db=connect()
    with db:db.execute("UPDATE collector_status SET value=? WHERE key='last_success'",(str(now-31),))
    db.close()
    with pytest.raises(demo.Unavailable):demo.observed_quote(demo.configuration())


def test_archived_prototypes_are_not_in_new_module_catalog():
    from modules.registry import list_modules,get_module
    names={module['id'] for module in list_modules()}
    assert {'demo-trade','demo-bot','demo-account','demo-positions','demo-reports'}<=names
    assert not {'calculator','counter','dice-roller','theme-summary','dashboard-health','empty'}&names
    assert get_module('counter') is not None  # Existing saved slots stay readable.


def test_replay_stays_bound_to_original_account_after_selection_change(market):
    first=new();request=trade();created=demo.submit('alice',request)['trade']
    second=demo.create_account('alice','Second',3000,'0123')
    replay=demo.submit('alice',request)
    assert replay['replayed'] and replay['trade']['id']==created['id'] and replay['trade']['account_id']==first['id']
    assert demo.state('alice',second['id'])['orders']==[]
    with pytest.raises(demo.Conflict):demo.submit('alice',dict(request,account_id=second['id']))


def test_long_lived_active_position_survives_history_window(market):
    new();opened=demo.submit('alice',trade())['trade']
    # Use fixture ledger records only, to verify visibility without 500 fills.
    with demo.database() as db:
        original=dict(db.execute('SELECT * FROM demo_orders WHERE id=?',(opened['id'],)).fetchone())
        for index in range(501):
            row={**original,'id':'history-'+str(index),'status':'cancelled','created_at':original['created_at']+index+1,'request_id':'history-request-'+str(index),'source_slot':None}
            db.execute('INSERT INTO demo_orders('+','.join(row)+') VALUES('+','.join('?' for _ in row)+')',tuple(row.values()))
    data=demo.state('alice');assert data['history_truncated'] and any(order['id']==opened['id'] for order in data['orders'])


def test_account_quota_and_ownership_are_checked_before_expensive_pin_hash(market,monkeypatch):
    calls=[];original=demo.pin_hash
    def measured(pin,salt):calls.append(True);return original(pin,salt)
    monkeypatch.setattr(demo,'pin_hash',measured)
    for index in range(10):demo.create_account('alice','Account '+str(index),1000,'0123')
    assert len(calls)==10
    with pytest.raises(demo.Conflict):demo.create_account('alice','Over limit',1000,'0123')
    assert len(calls)==10
    with pytest.raises(LookupError):demo.set_pin('bob','not-owned','0123')
    assert len(calls)==10


def test_quote_diagnostics_distinguish_closed_or_delayed_market_from_collector_failure(tmp_path,monkeypatch):
    monkeypatch.setenv('DASHBOARD_MODULE_STATE_DIR',str(tmp_path))
    from market_data.data import connect
    db=connect();now=time.time()
    with pytest.raises(demo.Unavailable,match='No market data received yet'):demo.observed_quote(demo.configuration())
    with db:
        db.execute('INSERT INTO candles(time,open,high,low,close,is_open) VALUES(?,?,?,?,?,?)',(int(now)//60*60-86400,2000,2000,2000,2000,0))
        db.execute("INSERT OR REPLACE INTO collector_status VALUES('last_success',?)",(str(now),))
    with pytest.raises(demo.Unavailable,match='market may be closed or the feed delayed'):demo.observed_quote(demo.configuration())
    with db:db.execute("INSERT OR REPLACE INTO collector_status VALUES('error','upstream unavailable')")
    with pytest.raises(demo.Unavailable,match='collector could not fetch'):demo.observed_quote(demo.configuration())
    db.close()
