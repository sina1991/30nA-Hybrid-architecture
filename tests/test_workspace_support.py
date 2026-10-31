"""IP trust boundary, bounded calendar parsing/cache and chart-local visibility."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from urllib.error import URLError
from fastapi.testclient import TestClient
import pytest
from modules import client_ip,economic_calendar,slots,indicator_profiles
from modules.execution import run_module
from test_account_chat_api import client,create_accounts,auth


def test_ip_headers_only_from_explicitly_trusted_loopback(monkeypatch):
    request=lambda peer,headers:SimpleNamespace(client=SimpleNamespace(host=peer),headers=headers)
    headers={'x-forwarded-for':'8.8.8.8','x-30na-client-ip':'203.0.113.9'}
    monkeypatch.delenv('DASHBOARD_TRUST_LOCAL_PROXY',raising=False)
    assert client_ip.address(request('198.51.100.7',headers))=='198.51.100.7'
    assert client_ip.address(request('127.0.0.1',headers)) is None
    monkeypatch.setenv('DASHBOARD_TRUST_LOCAL_PROXY','1')
    assert client_ip.address(request('127.0.0.1',headers))=='203.0.113.9'
    assert client_ip.address(request('127.0.0.1',{'x-forwarded-for':'8.8.8.8'})) is None
    assert client_ip.address(request('127.0.0.1',{'x-30na-client-ip':'malformed'})) is None
    assert run_module('myip',{})['status']=='unavailable'


def test_myip_and_viewer_identity_use_the_http_request(client,monkeypatch):
    (alice,a),_,_=create_accounts(client)
    remote=TestClient(client.app,client=('198.51.100.7',12345))
    me=remote.get('/api/upstreams/account/me',headers=auth(a)).json()['payload']
    assert me['user']['username']=='alice' and me['client_ip']=='198.51.100.7'
    assert remote.get('/api/upstreams/myip',headers=auth(a)).json()['payload']['ip']=='198.51.100.7'
    sid=slots.create(alice['id'])['slot'];slots.bind_active(alice['id'],sid,'myip',{})
    assert remote.post('/api/upstreams/slots/'+sid+'/read',headers=auth(a),json={'module_id':'myip'}).json()['payload']['result']['ip']=='198.51.100.7'
    assert remote.post('/api/upstreams/slots/'+sid+'/execute',headers=auth(a),json={'module_id':'myip','input':{'_request_ip':'8.8.8.8'}}).status_code==422
    assert remote.get('/api/upstreams/myip').status_code==401


def test_indicators_can_be_enabled_only_on_one_owners_chart(client):
    from test_chart_overlays import seed
    (alice,a),(bob,b),_=create_accounts(client);seed()
    profile=indicator_profiles.save(alice['id'],dict(name='Local round',type='round-levels',parameters={},enabled=False))
    first=slots.create(alice['id'],'fix-chart')['slot'];second=slots.create(alice['id'],'chart')['slot']
    assert client.post('/api/upstreams/slots/'+first+'/appearance',headers=auth(a),json={'profile_visibility':{profile['id']:True}}).status_code==200
    path='/api/upstreams/market/candles?include_indicators=true&slot_id='
    assert profile['id'] in [p['id'] for p in client.get(path+first,headers=auth(a)).json()['payload']['technical_overlays']]
    assert not client.get(path+second,headers=auth(a)).json()['payload']['technical_overlays']
    assert client.get(path+first,headers=auth(b)).status_code==404
    assert client.post('/api/upstreams/slots/'+first+'/appearance',headers=auth(b),json={'profile_visibility':{profile['id']:True}}).status_code in (404,422)
    assert next(p for p in indicator_profiles.list_profiles(alice['id']) if p['id']==profile['id'])['enabled'] is False
    linear=slots.create(alice['id'],'linear')['slot'];assert slots.binding(alice['id'],linear)['module_id']=='economic-calendar'
    slots.update_appearance(alice['id'],linear,{'layout':{'x':0,'y':0,'w':12,'h':1}})


def test_calendar_parser_filters_and_failed_source_is_backed_off(tmp_path,monkeypatch):
    monkeypatch.setenv('DASHBOARD_MODULE_STATE_DIR',str(tmp_path));calls=[]
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,size):return json.dumps([{'title':'<script>event</script>','country':'USD','date':'2099-01-01T10:00:00+00:00','impact':'High','forecast':'2','previous':'1'}, {'title':'Invalid timezone','date':'2099-01-01T10:00:00'}]).encode()
    class Opener:
        def open(self,request,timeout):calls.append(request.full_url);return Response()
    monkeypatch.setattr(economic_calendar,'build_opener',lambda *args:Opener())
    result=economic_calendar.run({'settings':{'currencies':['USD']}})
    assert result['status']=='ok' and result['events'][0]['title']=='<script>event</script>'
    assert len(result['events'])==1 and calls==[economic_calendar.FEED]
    economic_calendar.run({});assert len(calls)==1
    cache=tmp_path/'calendar/events.json';cache.unlink()
    class Failed:
        def open(self,*args,**kwargs):calls.append('failed');raise URLError('offline')
    monkeypatch.setattr(economic_calendar,'build_opener',lambda *args:Failed())
    assert economic_calendar.run({})['status']=='unavailable'
    assert economic_calendar.run({})['status']=='unavailable' and calls.count('failed')==1
    with pytest.raises(ValueError):economic_calendar.run({'url':'http://localhost/private'})


def test_managed_nginx_ip_patch_is_idempotent_and_preserves_unowned_files(tmp_path):
    root=Path(__file__).resolve().parents[1]
    spec=importlib.util.spec_from_file_location('client_ip_config',root/'scripts/deployment/configure_client_ip.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    path=tmp_path/'nginx';path.write_text('# Managed by the 30nA installer. Do not put credentials here.\n        proxy_set_header Authorization $http_authorization;\n')
    module.configure(path);module.configure(path)
    assert path.read_text().count('proxy_set_header X-30na-Client-IP $remote_addr;')==1
    path.write_text('unowned config')
    with pytest.raises(ValueError):module.configure(path)
    assert path.read_text()=='unowned config'
