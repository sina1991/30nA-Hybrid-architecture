"""Behavioral examples from supplied documentation and boundary regressions."""
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
import pytest
from modules import technical, slots
from modules.execution import run_module
from test_account_chat_api import client, create_accounts, auth


def ts(value): return int(datetime.fromisoformat(value.replace('Z','+00:00')).timestamp())


def bar(stamp,op=100,high=110,low=90,close=105,**extra):
    return dict(time=ts(stamp),open=op,high=high,low=low,close=close,**extra)


@pytest.mark.parametrize('price,step',[(4000,20),(1.1,0.005),(46000,250)])
def test_documented_auto_examples(price,step):
    result=run_module('round-levels',{'price':price})
    assert result['step']==step
    assert all(abs(v/step-round(v/step))<1e-8 for v in result['levels'])


def test_spacing_stability_and_recalculation():
    first=run_module('round-levels',{'price':4000})
    zoom=run_module('round-levels',{'price':4500,'visible_low':1,'visible_high':100000,'spacing_state':first['spacing_state']})
    assert zoom['step']==20 and len(zoom['levels'])==300 and zoom['capped']
    moved=run_module('round-levels',{'price':6000,'spacing_state':first['spacing_state']})
    assert moved['step']==25 and moved['spacing_state']['anchor']==6000
    manual=run_module('round-levels',{'price':1.1,'settings':{'auto':False,'manual_step':0.0025},'visible_low':1.095,'visible_high':1.105})
    assert manual['levels']==[1.095,1.0975,1.1,1.1025,1.105]
    switched=run_module('round-levels',{'price':4000,'spacing_state':manual['spacing_state']})
    assert switched['step']==20


def test_previous_trading_day_friday_to_monday():
    candles=[bar('2026-10-23T10:00:00Z',op=2630,high=2650,low=2620,close=2640),bar('2026-10-26T10:00:00Z')]
    result=run_module('previous-day-levels',{'candles':candles,'now':ts('2026-10-26T12:00:00Z')})
    monday=result['days'][0]
    assert monday['source_date']=='2026-10-23' and monday['date']=='2026-10-26'
    assert monday['levels']==dict(high=2650,low=2620,mid=2635,open=2630,close=2640)
    assert monday['start']==ts('2026-10-26T00:00:00Z') and monday['end']==ts('2026-10-27T00:00:00Z')
    assert all(day['date'] not in ('2026-10-24','2026-10-25') for day in result['days'])


def test_session_only_scan_open_and_end_exclusion():
    candles=[bar('2026-10-26T10:00:00Z',high=999),bar('2026-10-26T16:30:00Z',op=100,high=120,low=90,close=110),
             bar('2026-10-26T22:59:00Z',op=110,high=125,low=95,close=115),bar('2026-10-26T23:00:00Z',high=900),bar('2026-10-27T09:00:00Z')]
    result=run_module('previous-day-session-levels',{'candles':candles,'now':ts('2026-10-27T12:00:00Z')})
    assert result['days'][0]['levels']==dict(high=125,low=90,mid=107.5,open=100,close=115)
    assert result['styles']['open']['style']=='dash-dot'


def test_overnight_session_is_provisional_until_end():
    candles=[bar('2026-10-26T22:00:00Z',high=120),bar('2026-10-27T00:00:00Z',high=130)]
    data=dict(candles=candles,settings=dict(session_start='22:00',session_end='02:00'),now=ts('2026-10-27T01:00:00Z'))
    result=run_module('previous-day-session-levels',data)
    assert result['days'][0]['levels']['high']==130
    assert result['days'][0]['provisional'] is True
    data['now']=ts('2026-10-27T03:00:00Z')
    assert run_module('previous-day-session-levels',data)['days'][0]['provisional'] is False
    data['settings']['allow_wrap']=False
    with pytest.raises(ValueError): run_module('previous-day-session-levels',data)


def test_no_fallback_from_missing_sunday_session():
    candles=[bar('2026-10-23T17:00:00Z'),bar('2026-10-25T23:00:00Z'),bar('2026-10-26T09:00:00Z')]
    result=run_module('previous-day-session-levels',dict(candles=candles,now=ts('2026-10-26T12:00:00Z')))
    assert '2026-10-26' in result['missing_days']
    assert all(day['date']!='2026-10-26' for day in result['days'])


def test_dst_rules_at_real_transition_instants():
    assert technical.dst_seconds(ts('2026-03-08T06:59:59Z'),'USA')==0
    assert technical.dst_seconds(ts('2026-03-08T07:00:00Z'),'USA')==3600
    assert technical.dst_seconds(ts('2026-03-15T12:00:00Z'),'Europe')==0
    assert technical.dst_seconds(ts('2026-03-29T00:59:59Z'),'Europe')==0
    assert technical.dst_seconds(ts('2026-03-29T01:00:00Z'),'Europe')==3600
    assert technical.dst_seconds(ts('2026-10-25T01:00:00Z'),'Europe')==0
    assert technical.dst_seconds(ts('2026-10-25T01:00:00Z'),'USA')==3600


def schedule(**updates):
    return dict(winter_utc_minutes=120,clock_change='Europe',reference_timezone='America/New_York',
                windows=[dict(name='Example NY open',start='09:30',end='10:00',grade='A',views=['New York start'])],
                points=[dict(time='09:30',views=['New York start']),dict(time='10:00',views=['New York start'])],**updates)


def test_clock_uses_reference_dst_independent_of_broker():
    data=dict(settings=schedule(),now=ts('2026-03-16T13:45:00Z'))
    result=run_module('session-clock',data)
    assert result['wall_time']=='2026-03-16T15:45:00'
    assert result['windows'][0]['start']=='15:30'
    assert result['active_windows'][0]['grade']=='A'
    assert result['remaining_seconds']==900 and result['next_point']['time']=='16:00'
    assert result['time_verified'] is False
    end=run_module('session-clock',dict(data,now=ts('2026-03-16T14:00:00Z')))
    assert end['active_windows']==[]


def test_windows_and_clock_share_the_same_schedule_and_only_traded_dates():
    data=dict(settings=schedule(),now=ts('2026-03-16T13:45:00Z'),candles=[bar('2026-03-16T13:30:00Z')])
    clock=run_module('session-clock',data)
    windows=run_module('session-windows',data)
    for key in ('active_windows','next_point','remaining_seconds','windows'): assert clock[key]==windows[key]
    assert len(windows['chart_windows'])==1 and len(windows['chart_lines'])==2
    assert windows['chart_windows'][0]['start_timestamp']==ts('2026-03-16T13:30:00Z')
    data['settings']['teaching_view']='Points only'
    windows=run_module('session-windows',data)
    assert not windows['chart_windows'] and windows['chart_lines']


def test_missing_original_schedule_is_explicit():
    assert run_module('session-clock',{})['status']=='needs_configuration'
    assert run_module('session-windows',{})['status']=='needs_configuration'
    assert run_module('session-clock',{'settings':{'winter_utc_minutes':120}})['status']=='needs_configuration'


def test_nonexistent_dst_wall_time_is_not_invented():
    cfg=technical.settings('session-clock',{'winter_utc_minutes':120,'clock_change':'Europe'})
    assert technical.epoch(datetime(2026,3,29,3,30),cfg) is None
    assert technical.epoch(datetime(2026,10,25,3,30),cfg)==ts('2026-10-25T00:30:00Z')


def test_persistent_settings_and_spacing_are_owner_and_slot_scoped(client):
    (_,a),(_,b),_=create_accounts(client)
    slot=client.post('/api/upstreams/slots',headers=auth(a),json={'type':'standard'}).json()['payload']['slot']['slot']
    path='/api/upstreams/slots/'+slot
    assert client.post(path+'/binding',headers=auth(a),json={'module_id':'round-levels','context':{}}).status_code==200
    body={'technical_settings':{'round-levels':{'auto':False,'manual_step':10}}}
    assert client.post(path+'/appearance',headers=auth(b),json=body).status_code==404
    assert client.post(path+'/appearance',headers=auth(a),json=body).status_code==200
    result=client.post(path+'/execute',headers=auth(a),json={'module_id':'round-levels','input':{'price':4000}})
    assert result.status_code==200 and result.json()['payload']['result']['step']==10
    override=client.post(path+'/execute',headers=auth(a),json={'module_id':'round-levels','input':{'price':4000,'settings':{'show_labels':False}}})
    assert override.status_code==200 and override.json()['payload']['result']['step']==10
    assert client.post(path+'/read',headers=auth(b),json={'module_id':'round-levels'}).status_code==404
    body={'technical_settings':{'session-clock':schedule()}}
    assert client.post(path+'/appearance',headers=auth(a),json=body).status_code==200
    active=client.get('/api/upstreams/slots/active',headers=auth(a)).json()['payload']['slots'][0]
    assert active['technical_settings']['round-levels']['manual_step']==10
    assert active['technical_settings']['session-clock']['reference_timezone']=='America/New_York'
    assert client.post(path+'/appearance',headers=auth(a),json={'technical_settings':{'session-clock':{'points':[{'time':'25:00'}]}}}).status_code==422


@pytest.mark.parametrize('kind',technical.KINDS)
def test_standalone_cli(kind,tmp_path):
    data={'price':4000} if kind=='round-levels' else {'candles':[],'now':ts('2026-10-31T12:00:00Z')} if 'previous-day' in kind else {}
    root=Path(__file__).resolve().parents[1]
    result=subprocess.run([sys.executable,str(root/'modules'/kind/'module.py'),'--input',json.dumps(data)],text=True,capture_output=True)
    assert result.returncode==0,result.stderr
    assert isinstance(json.loads(result.stdout),dict)


@pytest.mark.parametrize('kind,data',[
    ('round-levels',{'price':True}),('round-levels',{'price':float('nan')}),
    ('previous-day-levels',{'candles':[bar('2026-10-26T10:00:00Z'),bar('2026-10-26T10:00:00Z')]}),
    ('session-clock',{'settings':{'points':['09:30']}}),('session-windows',{'settings':{'window_shape':'script'}}),
])
def test_rejects_invalid_inputs(kind,data):
    with pytest.raises(ValueError):run_module(kind,data)


def test_authenticated_module_api_and_reserved_fields(client):
    (_,token),_,_=create_accounts(client)
    for kind in technical.KINDS:
        path='/api/upstreams/modules/'+kind+'/run'
        data={'price':4000} if kind=='round-levels' else {'candles':[]}
        assert client.post(path,json={'input':data}).status_code==401
        assert client.post(path,headers=auth(token),json={'input':dict(data,_state_owner='other')}).status_code==422
        assert client.post(path,headers=auth(token),json={'input':data}).status_code==200
        assert client.post('/api/modules/'+kind+'/run',json=data).status_code in (401,403,404)


def test_broker_day_duration_respects_dst():
    cfg=technical.settings('previous-day-levels',dict(winter_utc_minutes=120,clock_change='Europe'))
    begin=technical.epoch(datetime(2026,3,29),cfg)
    end=technical.epoch(datetime(2026,3,30),cfg)
    assert end-begin==23*3600
    begin=technical.epoch(datetime(2026,10,25),cfg)
    end=technical.epoch(datetime(2026,10,26),cfg)
    assert end-begin==25*3600


def test_local_market_data_and_owner_scoped_round_anchor(tmp_path,monkeypatch):
    monkeypatch.setenv('DASHBOARD_MODULE_STATE_DIR',str(tmp_path))
    from market_data.data import connect
    now=ts('2026-10-27T12:00:00Z')
    db=connect()
    with db:
        for row in [bar('2026-10-26T16:30:00Z',op=3990,high=4020,low=3980,close=4000),bar('2026-10-27T09:00:00Z',op=3990,high=4020,low=3980,close=4000)]:
            db.execute('INSERT INTO candles(time,open,high,low,close,is_open) VALUES(?,?,?,?,?,0)',tuple(row[k] for k in ('time','open','high','low','close')))
    db.close()
    slot=slots.create('alice')['slot'];slots.bind_active('alice',slot,'round-levels',{})
    assert slots.read('alice',slot)['result']['step']==20
    assert slots.execute('alice',slot,{'price':4600})['result']['step']==20
    other=slots.create('bob')['slot'];slots.bind_active('bob',other,'round-levels',{})
    assert slots.execute('bob',other,{'price':4600})['result']['step']==25
    result=run_module('previous-day-session-levels',{'now':now})
    assert result['days'][0]['levels']['high']==4020 and result['source']=='local_XAUUSD_M1'
    duplicate=slots.duplicate('alice',slot)['slot']
    assert slots.execute('alice',duplicate,{'price':4600})['result']['step']==25
    slots.delete('alice',slot)
