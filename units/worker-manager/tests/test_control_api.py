import hashlib
import json
import sqlite3
import threading
import time
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from worker_manager import Schedule, SQLiteWorkerStore, WorkerDefinition, WorkerManager
from worker_manager.api import create_app
from worker_manager.control_service import ControlService
from worker_manager.service import WorkerConflict


def credentials(path):
    path.write_text(json.dumps({hashlib.sha256((owner + '-test-token').encode()).hexdigest(): owner for owner in ('alice','bob')}))
    return path


def auth(owner='alice'):
    return {'Authorization': 'Bearer ' + owner + '-test-token'}


class Gateway:
    def __init__(self):
        self.results, self.requests = {}, []
    def submit(self, request):
        self.requests.append(request)
        result = {'execution_id': request.execution_id, 'worker_id': request.definition.worker_id,
                  'status': 'succeeded', 'result': request.input_payload, 'error': None}
        self.results[request.execution_id] = result
        return result
    def get(self, execution_id):
        return self.results[execution_id]
    def cancel(self, execution_id):
        return execution_id in self.results


@pytest.fixture
def service(tmp_path):
    gateway = Gateway()
    instance = ControlService(tmp_path / 'control.db', lambda owner: gateway)
    yield instance, gateway
    instance.close()


def register(service, owner='alice', schedule=None):
    service.register(owner, WorkerDefinition('worker','artifact','sha256:'+'a'*64,'worker:run'), {}, schedule or Schedule())
    service.change(owner,'worker','enable')


def test_owner_scoping_and_mutations(service):
    svc, _ = service
    register(svc,'alice'); register(svc,'bob')
    svc.change('bob','worker','configure',configuration={'owner':'bob'})
    assert svc.manager('alice').get('worker').configuration == {}
    svc.change('alice','worker','delete')
    assert svc.manager('bob').get('worker').configuration == {'owner':'bob'}
    assert svc.manager('alice').list() == ()


def test_legacy_migration_preserves_rows_but_does_not_assign_to_users(tmp_path):
    db = tmp_path/'old.db'
    with sqlite3.connect(db) as c:
        c.execute('''CREATE TABLE workers(worker_id TEXT PRIMARY KEY, artifact_id TEXT,
            artifact_hash TEXT, entrypoint TEXT, lifecycle TEXT, configuration_json TEXT,
            schedule_kind TEXT, interval_seconds INTEGER, created_at TEXT, updated_at TEXT)''')
        c.execute("INSERT INTO workers VALUES ('old','artifact','sha256:old','worker:run','enabled','{}','manual',NULL,'then','then')")
    assert SQLiteWorkerStore(db, owner_id='alice').list() == ()
    assert SQLiteWorkerStore(db).get('old').definition.worker_id == 'old'
    assert SQLiteWorkerStore(db, owner_id='bob').list() == ()


def test_durable_idempotency_and_claim_race(service):
    svc, gateway = service
    register(svc)
    job = svc.submit('alice','worker',{'value':42},5.0,'key')
    assert svc.submit('alice','worker',{'value':42},5.0,'key') == job
    with pytest.raises(WorkerConflict): svc.submit('alice','worker',{'value':43},5.0,'key')
    claims = []
    threads = [threading.Thread(target=lambda: claims.append(svc.claim())) for _ in range(8)]
    for thread in threads: thread.start()
    for thread in threads: thread.join()
    claimed = [claim for claim in claims if claim]
    assert len(claimed) == 1
    svc.execute(claimed[0])
    assert len(gateway.requests) == 1
    assert svc.get('alice',job['execution_id'])['status'] == 'succeeded'
    with pytest.raises(KeyError): svc.get('bob',job['execution_id'])
    with pytest.raises(KeyError): svc.cancel('bob',job['execution_id'])


def test_restart_retains_history_and_never_replays_unknown_work(tmp_path):
    path = tmp_path/'db'
    gateway = Gateway()
    svc = ControlService(path,lambda owner: gateway)
    register(svc)
    queued = svc.submit('alice','worker',{},5.0,'key')
    svc.claim()
    svc.close()
    restarted = ControlService(path,lambda owner: gateway)
    try:
        result = restarted.get('alice',queued['execution_id'])
        assert result['status'] == 'failed'
        assert result['result']['error']['code'] == 'MANAGER_RESTARTED'
        assert restarted.claim() is None
        assert gateway.requests == []
        assert restarted.manager('alice').get('worker').lifecycle == 'enabled'
    finally:
        restarted.close()


def test_scheduler_due_and_no_burst_replay(service):
    svc,_ = service
    register(svc,schedule=Schedule('interval',10))
    svc._schedule_due(100)
    assert svc.claim(100) is None
    svc._schedule_due(110)
    assert svc.claim(110) is not None
    svc._schedule_due(110)
    assert svc.claim(110) is None
    svc._schedule_due(1000)
    assert svc.claim(1000) is not None
    assert svc.claim(1000) is None
    svc.change('alice','worker','disable')
    svc._schedule_due(2000)
    assert svc.claim(2000) is None


def test_lease_expiry_does_not_duplicate_remote_work(service):
    svc,_ = service
    register(svc)
    job = svc.submit('alice','worker',{},1.0,'key')
    assert svc.claim(0)
    assert svc.claim(100) is None
    result = svc.get('alice',job['execution_id'])
    assert result['status'] == 'failed'
    assert result['result']['error']['code'] == 'LEASE_EXPIRED'


def test_single_process_guard(service):
    svc,_ = service
    with pytest.raises(RuntimeError,match='Only one'):
        ControlService(svc.database,lambda owner: Gateway())


def test_cancel_queued_prevents_execution(service):
    svc,_ = service
    register(svc)
    job = svc.submit('alice','worker',{},5.0,'key')
    assert svc.cancel('alice',job['execution_id'])
    assert svc.claim() is None
    assert svc.get('alice',job['execution_id'])['status'] == 'cancelled'


def test_http_crud_auth_validation_revocation_and_size(service,tmp_path):
    svc,_ = service
    path = credentials(tmp_path/'credentials')
    client = TestClient(create_app(svc,path))
    assert client.get('/api/v1/workers').status_code == 401
    body = {'worker_id':'same','artifact_id':'artifact','artifact_hash':'sha256:'+'a'*64,'entrypoint':'worker:run'}
    for owner in ('alice','bob'):
        assert client.post('/api/v1/workers',json=body,headers=auth(owner)).status_code == 201
    assert client.post('/api/v1/workers/same/enable',headers=auth()).status_code == 200
    queued = client.post('/api/v1/workers/same/executions',json={'idempotency_key':'key'},headers=auth())
    assert queued.status_code == 202
    eid = queued.json()['payload']['execution_id']
    assert client.get('/api/v1/executions/'+eid,headers=auth('bob')).status_code == 404
    assert client.post('/api/v1/executions/'+eid+'/cancel',headers=auth('bob')).status_code == 404
    assert client.get('/api/v1/executions',headers=auth('bob')).json()['payload']['executions'] == []
    assert client.patch('/api/v1/workers/same',headers=auth(),json={'schedule':{'kind':'bad'}}).status_code == 422
    assert client.post('/api/v1/workers/same/executions',headers=auth(),json={'timeout_seconds':-1,'idempotency_key':'x'}).status_code == 422
    assert client.post('/api/v1/workers',headers=auth(),content=b'x'*1048577).status_code == 413
    path.write_text('{}')
    assert client.get('/api/v1/workers',headers=auth()).status_code == 401
    path.write_text('invalid')
    assert client.get('/api/v1/workers',headers=auth()).status_code == 503


def test_transport_failure_is_explicit_not_success_or_retry(service):
    svc,gateway = service
    register(svc)
    job = svc.submit('alice','worker',{},5.0,'key')
    def unavailable(request): raise TimeoutError()
    gateway.submit = unavailable
    svc.execute(svc.claim())
    result = svc.get('alice',job['execution_id'])
    assert result['status'] == 'failed'
    assert result['result']['error']['code'] == 'RUNTIME_OUTCOME_UNKNOWN'
    assert svc.claim() is None
