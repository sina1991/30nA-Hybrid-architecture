"""Owner-scoped chart profile wiring, using disposable market history."""
from datetime import datetime,timezone
import pytest
from modules import technical,indicator_profiles,chart_overlays,signal_rules
from test_account_chat_api import client,create_accounts,auth


def seed():
    from market_data.data import connect
    now=int(datetime.now(timezone.utc).timestamp())//60*60
    db=connect()
    with db:
        for offset in (-86400,0):
            for minute in range(60):
                db.execute('INSERT OR REPLACE INTO candles(time,open,high,low,close,is_open) VALUES(?,?,?,?,?,?)',(now+offset-minute*60,100,110,90,105,0))
    db.close()
    return now


def test_all_profiles_render_through_authenticated_market_api(client):
    (alice,a),(bob,b),_=create_accounts(client);now=seed()
    cfg={'winter_utc_minutes':0,'windows':[{'name':'All day test','start':'00:00','end':'00:00','grade':'A'}],'points':[{'time':'12:00'}]}
    ids=[]
    for kind in technical.KINDS:
        parameters=cfg if kind.startswith('session-') else {'session_start':'00:00','session_end':'00:00'} if kind=='previous-day-session-levels' else {}
        response=client.post('/api/upstreams/indicator-profiles',headers=auth(a),json={'name':kind,'type':kind,'parameters':parameters,'enabled':True})
        assert response.status_code==200,response.text
        ids.append(response.json()['payload']['profile']['id'])
    path='/api/upstreams/market/candles?include_indicators=true&limit=100'
    data=client.get(path,headers=auth(a)).json()['payload']
    overlays=data['technical_overlays']
    assert {item['type'] for item in overlays}==set(technical.KINDS)
    assert all(item['result']['status']=='ok' for item in overlays)
    assert any(item['result'].get('days') for item in overlays)
    assert next(item for item in overlays if item['type']=='session-windows')['result']['chart_windows']
    assert not client.get(path,headers=auth(b)).json()['payload']['technical_overlays']
    target=overlays[0]
    assert client.put('/api/upstreams/indicator-profiles/'+target['id'],headers=auth(b),json={key:target[key] for key in ('name','type','parameters','enabled')}).status_code==404
    update={key:target[key] for key in ('name','type','parameters','enabled')};update['enabled']=False
    assert client.put('/api/upstreams/indicator-profiles/'+target['id'],headers=auth(a),json=update).status_code==200
    assert target['id'] not in [item['id'] for item in client.get(path,headers=auth(a)).json()['payload']['technical_overlays']]
    assert client.get(path).status_code==401


def test_signal_rules_reject_chart_only_profile_without_breaking_existing_rules(tmp_path,monkeypatch):
    monkeypatch.setenv('DASHBOARD_MODULE_STATE_DIR',str(tmp_path))
    p=indicator_profiles.save('alice',dict(name='Round',type='round-levels',parameters={},enabled=True))
    rule=dict(name='Invalid chart condition',interval='1m',enabled=True,signal='BUY',conditions=[dict(left=p['id'],field='value',op='gt',right_kind='number',right=0,right_field='')])
    with pytest.raises(ValueError):signal_rules.save('alice',rule)


def test_old_empty_session_profile_can_load_supplied_preset(client):
    (_,token),_,_=create_accounts(client)
    path='/api/upstreams/indicator-profiles'
    created=client.post(path,headers=auth(token),json=dict(name='Old clock',type='session-clock',enabled=False,parameters={'winter_utc_minutes':None,'windows':[],'points':[]})).json()['payload']['profile']
    assert created['parameters']['windows']==[]
    presets=client.get('/api/upstreams/indicator-presets',headers=auth(token)).json()['payload']['presets']
    assert len(presets['session-clock']['windows'])==11 and len(presets['session-windows']['points'])==15
    response=client.put(path+'/'+created['id'],headers=auth(token),json=dict(name=created['name'],type=created['type'],enabled=True,parameters=presets['session-clock']))
    assert response.status_code==200 and response.json()['payload']['profile']['parameters']['windows'][10]['end']=='00:00'
    assert client.get('/api/upstreams/indicator-presets').status_code==401
