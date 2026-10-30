"""HTTP authentication and private chat checks with in-memory clients."""
import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from dashboard.app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('DASHBOARD_MODULE_STATE_DIR', str(tmp_path / 'state'))
    from market_data.collector import GoldCollector
    from modules.slot_workers import SlotWorkerScheduler
    from modules.signal_rules import SignalScheduler
    for scheduler in (GoldCollector, SlotWorkerScheduler, SignalScheduler):
        monkeypatch.setattr(scheduler, 'start', lambda self: None)
        monkeypatch.setattr(scheduler, 'stop', lambda self: None)
    credentials = tmp_path / 'credentials.json'
    credentials.write_text(json.dumps({hashlib.sha256(b'legacy-secret').hexdigest(): 'customer'}))
    class Adapter:
        def get(self, path): return {'workers':[]} if path.endswith('/workers') else {'executions':[]}
    return TestClient(create_app(credential_path=credentials, upstream_factory=lambda owner,token: {'worker-manager':Adapter()}))


def auth(token): return {'Authorization':'Bearer '+token}


def create_accounts(client):
    admin=auth('legacy-secret')
    assert client.post('/api/upstreams/account/bootstrap',headers=admin,json={'username':'admin','password':'admin password over twelve'}).status_code == 200
    users=[]
    for name in ('alice','bob','eve'):
        response=client.post('/api/upstreams/accounts',headers=admin,json={'username':name,'password':name+' password over twelve','role':'user'})
        assert response.status_code == 200
        user=response.json()['payload']['user']
        session=client.post('/api/upstreams/account/login',json={'username':name,'password':name+' password over twelve'})
        assert session.status_code == 200
        users.append((user,session.json()['payload']['token']))
    return users


def test_bootstrap_user_access_and_worker_fail_closed(client):
    assert client.post('/api/upstreams/account/bootstrap',json={'username':'admin','password':'admin password over twelve'}).status_code == 401
    users=create_accounts(client)
    alice, token=users[0]
    assert client.get('/api/upstreams/account/me',headers=auth(token)).json()['payload']['user']['id'] == alice['id']
    assert client.get('/api/upstreams/accounts',headers=auth(token)).status_code == 403
    assert client.get('/api/upstreams/workers',headers=auth(token)).status_code == 503
    assert client.get('/api/upstreams/workers',headers=auth('legacy-secret')).status_code == 200
    assert client.post('/api/upstreams/account/logout',headers=auth(token)).status_code == 200
    assert client.get('/api/upstreams/account/me',headers=auth(token)).status_code == 401


def test_chat_requires_acceptance_and_isolates_participants(client):
    (alice,a),(bob,b),(eve,e)=create_accounts(client)
    request=client.post('/api/upstreams/chat/requests',headers=auth(a),json={'recipient':bob['id']})
    assert request.status_code == 200
    request_id=request.json()['payload']['request']['id']
    assert client.post('/api/upstreams/chat/requests/'+request_id+'/respond',headers=auth(e),json={'accept':True}).status_code == 404
    accepted=client.post('/api/upstreams/chat/requests/'+request_id+'/respond',headers=auth(b),json={'accept':True})
    room=accepted.json()['payload']['request']['room_id']
    assert client.post('/api/upstreams/chat/rooms/'+room+'/messages',headers=auth(a),json={'text':'private'}).status_code == 200
    assert client.get('/api/upstreams/chat/rooms/'+room+'/messages',headers=auth(b)).json()['payload']['messages'][0]['body'] == 'private'
    assert client.get('/api/upstreams/chat/rooms/'+room+'/messages',headers=auth(e)).status_code == 403
    assert client.post('/api/upstreams/chat/rooms/public/messages',headers=auth(e),json={'text':'public'}).status_code == 200
    assert client.get('/api/upstreams/chat/rooms/public/messages',headers=auth(a)).status_code == 200
    assert client.post('/api/upstreams/accounts/'+alice['id']+'/enabled',headers=auth('legacy-secret'),json={'enabled':False}).status_code == 200
    assert client.get('/api/upstreams/chat/rooms/public/messages',headers=auth(a)).status_code == 401


def test_session_can_create_and_use_owner_scoped_chat_slot(client):
    (alice,a),(bob,b),_=create_accounts(client)
    first=client.post('/api/upstreams/slots',headers=auth(a),json={'type':'chat'})
    assert first.status_code == 200
    slot=first.json()['payload']['slot']['slot']
    assert first.json()['payload']['slot']['module_id'] == 'chat-box'
    result=client.post('/api/upstreams/slots/'+slot+'/execute',headers=auth(a),json={'module_id':'chat-box','input':{'action':'send','text':'hello'}})
    assert result.status_code == 200
    assert result.json()['payload']['result']['message']['body'] == 'hello'
    assert client.post('/api/upstreams/slots/'+slot+'/read',headers=auth(b),json={'module_id':'chat-box'}).status_code == 404
    assert client.post('/api/upstreams/slots/'+slot+'/appearance',headers=auth(a),json={'chat_room':'room-'+'a'*32}).status_code == 422


def test_legacy_token_with_session_prefix_remains_valid(tmp_path, monkeypatch):
    monkeypatch.setenv('DASHBOARD_MODULE_STATE_DIR', str(tmp_path/'state'))
    token='s_'+'x'*43
    path=tmp_path/'credentials.json'
    path.write_text(json.dumps({hashlib.sha256(token.encode()).hexdigest():'customer'}))
    class Adapter:
        def get(self,path): return {'workers':[]}
    client=TestClient(create_app(credential_path=path,upstream_factory=lambda owner,credential:{'worker-manager':Adapter()}))
    response=client.get('/api/upstreams/account/me',headers=auth(token))
    assert response.status_code == 200 and response.json()['payload']['legacy'] is True
    assert client.get('/api/upstreams/workers',headers=auth(token)).status_code == 200


def test_provisioned_session_can_use_its_worker_credential(client, tmp_path):
    import secrets
    (alice,a),(bob,b),_=create_accounts(client)
    first=secrets.token_urlsafe(48); second=secrets.token_urlsafe(48)
    credential_file=tmp_path/'state'/'account-upstream.json'
    credential_file.write_text(json.dumps({alice['id']:first,bob['id']:second}))
    credential_file.chmod(0o600)
    assert client.get('/api/upstreams/account/me',headers=auth(a)).json()['payload']['worker_access'] is True
    assert client.get('/api/upstreams/workers',headers=auth(a)).status_code == 200
    assert client.get('/api/upstreams/workers',headers=auth(b)).status_code == 200
    assert client.post('/api/upstreams/accounts/'+alice['id']+'/enabled',headers=auth('legacy-secret'),json={'enabled':False}).status_code == 200
    assert client.get('/api/upstreams/workers',headers=auth(a)).status_code == 401


def test_forwarded_credentials_never_cross_accounts(tmp_path, monkeypatch):
    import secrets
    state=tmp_path/'state'; monkeypatch.setenv('DASHBOARD_MODULE_STATE_DIR',str(state))
    path=tmp_path/'credentials.json';path.write_text(json.dumps({hashlib.sha256(b'legacy-secret').hexdigest():'customer'}))
    calls=[]
    class Adapter:
        def __init__(self,owner,credential): self.owner,self.credential=owner,credential
        def get(self,path): calls.append((self.owner,self.credential));return {'workers':[]}
    client=TestClient(create_app(credential_path=path,upstream_factory=lambda owner,credential:{'worker-manager':Adapter(owner,credential)}))
    (alice,a),(bob,b),_=create_accounts(client)
    first,second=secrets.token_urlsafe(48),secrets.token_urlsafe(48)
    file=state/'account-upstream.json';file.write_text(json.dumps({alice['id']:first,bob['id']:second}));file.chmod(0o600)
    assert client.get('/api/upstreams/workers',headers=auth(a)).status_code==200
    assert client.get('/api/upstreams/workers',headers=auth(b)).status_code==200
    assert calls==[(alice['id'],first),(bob['id'],second)]
    assert all(credential not in (a,b) for _,credential in calls)


def test_disabling_customer_revokes_legacy_dashboard_access(client):
    create_accounts(client)
    admin=auth('legacy-secret')
    second=client.post('/api/upstreams/accounts',headers=admin,json={'username':'secondadmin','password':'second administrator password','role':'admin'})
    assert second.status_code==200
    second_session=client.post('/api/upstreams/account/login',json={'username':'secondadmin','password':'second administrator password'}).json()['payload']['token']
    assert client.post('/api/upstreams/accounts/customer/enabled',headers=auth(second_session),json={'enabled':False}).status_code==200
    assert client.get('/api/upstreams/account/me',headers=admin).status_code==401
    assert client.get('/api/upstreams/account/me',headers=auth(second_session)).status_code==200
