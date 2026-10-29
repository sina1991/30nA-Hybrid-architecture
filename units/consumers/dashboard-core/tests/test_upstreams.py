import hashlib
import json

import pytest
from fastapi.testclient import TestClient
from dashboard.app import create_app
from public_api import ConsumerAPIError


@pytest.fixture
def configured(tmp_path):
    credentials = tmp_path/'credentials'
    credentials.write_text(json.dumps({hashlib.sha256(b'user-token').hexdigest():'alice'}))
    calls = []
    class Adapter:
        def get(self,path):
            calls.append(path)
            return {'workers':[{'worker_id':'alice-worker'}]}
    def factory(owner,token):
        assert owner == 'alice'
        assert token == 'user-token'
        return {'worker-manager':Adapter()}
    return TestClient(create_app(credential_path=credentials,upstream_factory=factory)),calls,credentials


def test_dashboard_never_contacts_upstream_without_valid_identity(configured):
    client,calls,_ = configured
    assert client.get('/api/upstreams/workers').status_code == 401
    assert client.get('/api/upstreams/workers',headers={'Authorization':'Bearer wrong'}).status_code == 401
    assert calls == []
    response = client.get('/api/upstreams/workers',headers={'Authorization':'Bearer user-token'})
    assert response.status_code == 200
    assert response.json()['payload']['workers'][0]['worker_id'] == 'alice-worker'
    assert calls == ['/api/v1/workers']
    assert 'user-token' not in client.get('/').text


@pytest.mark.parametrize('error,status', [('FORBIDDEN',403),('UNAUTHORIZED',401),('SERVICE_UNAVAILABLE',None),('INVALID_RESPONSE',None)])
def test_dashboard_upstream_errors_are_explicit_and_do_not_leak_credentials(tmp_path,error,status):
    path=tmp_path/'credentials'
    path.write_text(json.dumps({hashlib.sha256(b'test-token').hexdigest():'alice'}))
    class Adapter:
        def get(self,path): raise ConsumerAPIError(error,'sensitive upstream diagnostic',status)
    client=TestClient(create_app(credential_path=path,upstream_factory=lambda owner,token:{'worker-manager':Adapter()}))
    response=client.get('/api/upstreams/workers',headers={'Authorization':'Bearer test-token'})
    assert response.status_code == (status or 503)
    assert 'sensitive' not in response.text
    assert 'test-token' not in response.text


@pytest.fixture
def execution_client(tmp_path):
    path=tmp_path/'credentials'
    path.write_text(json.dumps({hashlib.sha256((owner+'-token').encode()).hexdigest():owner for owner in ('alice','bob')}))
    calls=[]
    class Adapter:
        def __init__(self,owner):self.owner=owner
        def get(self,path):
            calls.append((self.owner,'GET',path,None))
            if self.owner=='bob':raise ConsumerAPIError('NOT_FOUND','private diagnostic',404)
            return {'execution_id':'11111111-1111-4111-8111-111111111111','status':'succeeded','result':{'result':{'sum':60}}}
        def post(self,path,body):
            calls.append((self.owner,'POST',path,body))
            if self.owner=='bob':raise ConsumerAPIError('NOT_FOUND','private diagnostic',404)
            if path.endswith('/cancel'):return {'cancelled':True}
            return {'execution_id':'11111111-1111-4111-8111-111111111111','status':'accepted'}
    def factory(owner,token):
        assert token==owner+'-token'
        return {'worker-manager':Adapter(owner)}
    return TestClient(create_app(credential_path=path,upstream_factory=factory)),calls


def test_run_lookup_and_cancel_forward_validated_owner_credentials(execution_client):
    client,calls=execution_client
    headers={'Authorization':'Bearer alice-token'}
    body={'input_payload':{'values':[10,20,30]},'idempotency_key':'stable-key','timeout_seconds':15}
    response=client.post('/api/upstreams/workers/demo/executions',headers=headers,json=body)
    assert response.status_code==202
    assert calls[-1]==('alice','POST','/api/v1/workers/demo/executions',body)
    assert response.headers['cache-control']=='no-store'
    eid=response.json()['payload']['execution_id']
    assert client.get('/api/upstreams/executions/'+eid,headers=headers).json()['payload']['result']['result']=={'sum':60}
    assert client.post('/api/upstreams/executions/'+eid+'/cancel',headers=headers).json()['payload']['cancelled']
    other={'Authorization':'Bearer bob-token'}
    assert client.get('/api/upstreams/executions/'+eid,headers=other).status_code==404
    assert client.post('/api/upstreams/executions/'+eid+'/cancel',headers=other).status_code==404


def test_submission_auth_and_validation_precede_upstream_calls(execution_client):
    client,calls=execution_client
    endpoint='/api/upstreams/workers/demo/executions'
    body={'idempotency_key':'key','input_payload':{}}
    assert client.post(endpoint,json=body).status_code==401
    assert client.post(endpoint,headers={'Authorization':'Bearer wrong'},json=body).status_code==401
    headers={'Authorization':'Bearer alice-token'}
    for invalid in ({},dict(body,owner_id='bob'),dict(body,timeout_seconds=-1),dict(body,input_payload=[])):
        assert client.post(endpoint,headers=headers,json=invalid).status_code==422
    assert client.get('/api/upstreams/executions/not-a-uuid',headers=headers).status_code==422
    assert client.post(endpoint,headers=headers,content=b'x'*1048577).status_code==413
    assert calls==[]


@pytest.mark.parametrize('status',[401,403,404,409,422,503])
def test_submission_errors_preserve_status_without_leaking_diagnostics(tmp_path,status):
    path=tmp_path/'credentials';path.write_text(json.dumps({hashlib.sha256(b'token').hexdigest():'alice'}))
    class Adapter:
        def post(self,path,body):raise ConsumerAPIError('UPSTREAM_ERROR','private-secret-diagnostic',status)
    client=TestClient(create_app(credential_path=path,upstream_factory=lambda owner,token:{'worker-manager':Adapter()}))
    response=client.post('/api/upstreams/workers/demo/executions',headers={'Authorization':'Bearer token'},json={'idempotency_key':'key'})
    assert response.status_code==status
    assert 'private-secret-diagnostic' not in response.text
