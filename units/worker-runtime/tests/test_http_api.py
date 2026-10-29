import hashlib
import json
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from worker_runtime import ExecutionResult
from worker_runtime.api import create_app


class Runtime:
    require_sandbox = True
    sandbox_backend = object()
    def __init__(self): self.results = {}
    def submit(self, request):
        value = ExecutionResult(request.execution_id,request.definition.worker_id,True,'succeeded',{'owner_scoped':True})
        self.results[request.execution_id] = value
        return value
    def get(self,eid): return self.results.get(eid)
    def cancel(self,eid): return False


def test_runtime_auth_and_owner_isolation(tmp_path):
    path = tmp_path/'credentials'
    path.write_text(json.dumps({hashlib.sha256(x.encode()).hexdigest(): x for x in ('alice','bob')}))
    client = TestClient(create_app(path,lambda owner: Runtime()))
    body = {'execution_id':str(uuid4()),'idempotency_key':'key','definition':{'worker_id':'worker','artifact_id':'artifact','artifact_hash':'sha256:'+'a'*64,'entrypoint':'worker:run'}}
    assert client.post('/api/v1/executions',json=body).status_code == 401
    a = {'Authorization':'Bearer alice'}
    b = {'Authorization':'Bearer bob'}
    response = client.post('/api/v1/executions',json=body,headers=a)
    assert response.status_code == 200,response.text
    eid = body['execution_id']
    assert response.json()['payload']['status'] == 'succeeded'
    assert client.get('/api/v1/executions/'+eid,headers=b).status_code == 404
    assert client.post('/api/v1/executions/'+eid+'/cancel',headers=b).status_code == 404
    assert client.get('/api/v1/executions/'+eid,headers=a).status_code == 200
    path.write_text('{}')
    assert client.get('/api/v1/executions/'+eid,headers=a).status_code == 401


def test_runtime_rejects_shared_or_unsafe_runtime(tmp_path):
    path = tmp_path/'credentials'
    path.write_text(json.dumps({hashlib.sha256(x.encode()).hexdigest(): x for x in ('alice','bob')}))
    shared = Runtime()
    client = TestClient(create_app(path,lambda owner: shared))
    assert client.get('/api/v1/executions/missing',headers={'Authorization':'Bearer alice'}).status_code == 404
    assert client.get('/api/v1/executions/missing',headers={'Authorization':'Bearer bob'}).status_code == 503
    shared.require_sandbox = False
    other = TestClient(create_app(path,lambda owner: shared))
    assert other.get('/api/v1/executions/missing',headers={'Authorization':'Bearer alice'}).status_code == 503
