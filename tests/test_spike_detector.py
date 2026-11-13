"""Spike Detector All Spikes behavior and trusted module integration."""
import pytest\nimport time
from modules import technical, indicator_profiles
from modules.execution import run_module
from test_account_chat_api import client, create_accounts, auth


def candles(price_move=4.0, volume=50):
    rows=[]
    stamp=int(time.time())//60*60-20*60
    for index in range(20):
        rows.append({'time':stamp+index*60,'open':100.0,'high':101.0,'low':99.0,'close':100.0,'tick_volume':10})
    rows.append({'time':stamp+20*60,'open':100.0,'high':100.0+price_move+1,'low':99.0,'close':100.0+price_move,'tick_volume':volume,'is_open':False})
    return rows


def config(**changes):
    return {'baseline_period':20,'price_change_percent':2.0,'volume_multiplier':2.0,
            'combined_price_change_percent':3.0,'combined_volume_multiplier':4.0,
            **changes}


def test_combined_spike_emits_one_combined_event():
    result=run_module('spike-detector',{'candles':candles(),'now':candles()[-1]['time']+1,'settings':config()})
    assert result['status']=='ok'
    assert result['event_count']==3
    assert {event['event_type'] for event in result['events']}=={'price-spike','volume-spike','combined-spike'}
    event=next(event for event in result['events'] if event['event_type']=='combined-spike')
    assert event['direction']=='bullish'
    assert event['price_change_percent']==4.0
    assert event['volume_ratio']==5.0
    assert event['severity']=='high'
    assert event['status']=='confirmed'


def test_independent_modes_emit_price_and_volume_separately():
    result=technical.run('spike-detector',{'candles':candles(),'now':candles()[-1]['time']+1,
        'settings':config(combined_enabled=False)})
    assert {event['event_type'] for event in result['events']}=={'price-spike','volume-spike'}


@pytest.mark.parametrize('settings',[
    {'baseline_period':1},{'price_change_percent':0},{'volume_multiplier':1},
    {'price_enabled':1},{'price_color':'red'},
])
def test_invalid_spike_settings_rejected(settings):
    with pytest.raises(ValueError):
        technical.settings('spike-detector',settings)


def test_module_is_owner_scoped_via_indicator_profiles(client):
    (alice,a),(bob,b),_=create_accounts(client)
    from market_data.data import connect\n    rows=candles()\n    db=connect()\n    with db:\n        for row in rows:\n            db.execute('INSERT OR REPLACE INTO candles(time,open,high,low,close,tick_volume,is_open) VALUES(?,?,?,?,?,?,?)',(row['time'],row['open'],row['high'],row['low'],row['close'],row['tick_volume'],int(row.get('is_open',False))))\n    db.close()\n    profile=client.post('/api/upstreams/indicator-profiles',headers=auth(a),json={
        'name':'Spike All','type':'spike-detector','parameters':config(),'enabled':True})
    assert profile.status_code==200,profile.text
    payload=client.get('/api/upstreams/market/candles?include_indicators=true&limit=100',headers=auth(a))
    assert payload.status_code==200
    overlays=payload.json()['payload']['technical_overlays']
    assert any(item['type']=='spike-detector' and item['result']['status']=='ok' for item in overlays)
    other=client.get('/api/upstreams/market/candles?include_indicators=true&limit=100',headers=auth(b))
    assert not any(item['type']=='spike-detector' for item in other.json()['payload']['technical_overlays'])
    assert client.post('/api/modules/spike-detector/run',json={'candles':candles()}).status_code in (401,403,404)
