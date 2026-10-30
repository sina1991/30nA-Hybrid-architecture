"""Exercise Dashboard CRUD through the real Manager API and owner-bound adapter."""
import hashlib
import io
import json
from urllib.error import HTTPError
from urllib.parse import urlsplit

from fastapi.testclient import TestClient
import pytest
from dashboard.app import create_app
from public_api import PublicAPI
from worker_manager.api import create_app as manager_app
from worker_manager.control_service import ControlService


@pytest.fixture
def clients(tmp_path):
    path=tmp_path/'credentials'
    path.write_text(json.dumps({hashlib.sha256((x+'-token').encode()).hexdigest():x for x in ('alice','bob')}))
    service=ControlService(tmp_path/'manager.db',lambda owner:None)
    manager=TestClient(manager_app(service,path))
    calls=[]
    def factory(owner,token):
        assert token==owner+'-token'
        def transport(request,timeout):
            calls.append((owner,request.get_method(),request.full_url))
            response=manager.request(request.get_method(),urlsplit(request.full_url).path,
                                     headers=dict(request.header_items()),content=request.data)
            if response.status_code>=400:
                raise HTTPError(request.full_url,response.status_code,'upstream failed',response.headers,io.BytesIO(response.content))
            return io.BytesIO(response.content)
        return {'worker-manager':PublicAPI('https://manager.example',token=token,transport=transport)}
    dashboard=TestClient(create_app(credential_path=path,upstream_factory=factory))
    yield dashboard,service,calls
    service.close()


def test_worker_crud_owner_binding_and_history_after_deletion(clients):
    client,service,calls=clients
    a={'Authorization':'Bearer alice-token'};b={'Authorization':'Bearer bob-token'}
    endpoint='/api/upstreams/workers/test-worker'
    body={'worker_id':'test-worker','artifact_id':'published@1','artifact_hash':'sha256:'+'a'*64,
          'entrypoint':'worker:run','configuration':{'value':1}}
    assert client.post('/api/upstreams/workers',headers=a,json=body).status_code==201
    assert client.post('/api/upstreams/workers',headers=a,json=body).status_code==409
    row=client.get(endpoint,headers=a).json()['payload']
    assert row['lifecycle']=='configured'
    assert client.get(endpoint,headers=b).status_code==404
    assert client.patch(endpoint,headers=b,json={'configuration':{}}).status_code==404
    assert client.delete(endpoint,headers=b).status_code==404
    assert client.post(endpoint+'/enable',headers=b).status_code==404
    assert client.patch(endpoint,headers=a,json={'configuration':{'value':2},'schedule':{'kind':'interval','interval_seconds':60}}).status_code==200
    assert client.post(endpoint+'/enable',headers=a,json={}).json()['payload']['lifecycle']=='enabled'
    assert client.post(endpoint+'/disable',headers=a,json={}).json()['payload']['lifecycle']=='disabled'
    changed=client.get(endpoint,headers=a).json()['payload']
    assert changed['configuration']=={'value':2} and changed['schedule']['interval_seconds']==60
    assert client.post(endpoint+'/enable',headers=a,json={}).status_code==200
    job=client.post(endpoint+'/executions',headers=a,json={'idempotency_key':'preserve-history'}).json()['payload']
    assert client.delete(endpoint,headers=a).json()['payload']['deleted'] is True
    assert client.get('/api/upstreams/executions/'+job['execution_id'],headers=a).status_code==200
    assert client.get('/api/upstreams/executions/'+job['execution_id'],headers=b).status_code==404
    assert client.get(endpoint,headers=a).status_code==404
    assert service.manager('alice').list()==()
    assert any(method=='PATCH' for _,method,_ in calls)
    assert any(method=='DELETE' for _,method,_ in calls)


def test_management_auth_validation_and_immutable_definition_precede_forwarding(clients):
    client,_,calls=clients
    endpoint='/api/upstreams/workers'
    body={'worker_id':'test-worker','artifact_id':'artifact','artifact_hash':'sha256:'+'a'*64,'entrypoint':'worker:run'}
    assert client.post(endpoint,json=body).status_code==401
    assert client.delete(endpoint+'/test-worker').status_code==401
    a={'Authorization':'Bearer alice-token'}
    assert client.post(endpoint,headers=a,json=dict(body,owner_id='bob')).status_code==422
    assert client.patch(endpoint+'/test-worker',headers=a,json={'artifact_hash':'sha256:'+'b'*64}).status_code==422
    assert client.patch(endpoint+'/test-worker',headers=a,json={}).status_code==422
    assert client.post(endpoint,headers=a,json=dict(body,artifact_hash='wrong')).status_code==422
    assert client.post(endpoint+'/test-worker/restart',headers=a,json={}).status_code==404
    assert calls==[]
