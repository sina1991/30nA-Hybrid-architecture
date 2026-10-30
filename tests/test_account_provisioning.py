"""Credential provisioning preserves and separates downstream owners."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import pytest
from modules import accounts

SPEC=importlib.util.spec_from_file_location('account_sync',Path(__file__).parents[1]/'scripts/deployment/sync_account_credentials.py')
sync_module=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(sync_module)


def token(): return secrets.token_urlsafe(48)
def digest(value): return hashlib.sha256(value.encode()).hexdigest()


def test_provision_is_owner_scoped_stable_and_revocable(tmp_path,monkeypatch):
    config=tmp_path/'config';state=tmp_path/'state';config.mkdir(mode=0o700);state.mkdir(mode=0o700)
    monkeypatch.setenv('DASHBOARD_MODULE_STATE_DIR',str(state))
    accounts.bootstrap_admin('administrator','admin password over twelve')
    alice=accounts.create_user('alice','alice password over twelve')
    bob=accounts.create_user('bob','bob password over twelve')
    base={key:token() for key in ('customer','manager_runtime','runtime_code')}
    data={
        'installer-secrets.json':base,
        'manager-incoming.json':{digest(base['customer']):'customer'},
        'runtime-incoming.json':{digest(base['manager_runtime']):'customer'},
        'code-incoming.json':{digest(base['customer']):'customer',digest(base['runtime_code']):'customer'},
        'manager-runtime.json':{'customer':{'url':'https://localhost:18445','token':base['manager_runtime']}},
        'runtime-code.json':{'customer':{'url':'https://localhost:18443','token':base['runtime_code']}},
    }
    for name,value in data.items(): (config/name).write_text(json.dumps(value))
    (config/'installer-secrets.json').chmod(0o600)
    (state/'accounts.sqlite3').chmod(0o600)
    assert sync_module.sync(config,state,os.geteuid(),os.getegid()) == 3
    alice_token=accounts.upstream_credential(alice['id']); bob_token=accounts.upstream_credential(bob['id'])
    assert alice_token and bob_token and alice_token != bob_token
    manager=json.loads((config/'manager-incoming.json').read_text()); assert manager[digest(alice_token)] == alice['id']
    assert manager[digest(bob_token)] == bob['id'] and manager[digest(base['customer'])] == 'customer'
    before=(config/'manager-incoming.json').stat().st_mtime_ns
    sync_module.sync(config,state,os.geteuid(),os.getegid()); assert accounts.upstream_credential(alice['id']) == alice_token
    assert (config/'manager-incoming.json').stat().st_mtime_ns == before
    accounts.set_enabled(alice['id'],False);sync_module.sync(config,state,os.geteuid(),os.getegid())
    assert accounts.upstream_credential(alice['id']) is None
    assert digest(alice_token) not in json.loads((config/'manager-incoming.json').read_text())
    assert accounts.upstream_credential(bob['id']) == bob_token
    accounts.set_enabled(alice['id'],True);sync_module.sync(config,state,os.geteuid(),os.getegid())
    assert accounts.upstream_credential(alice['id']) == alice_token
    accounts.create_user('secondadmin','another long password',role='admin')
    accounts.set_enabled('customer',False);sync_module.sync(config,state,os.geteuid(),os.getegid())
    assert digest(base['customer']) not in json.loads((config/'manager-incoming.json').read_text())
    assert digest(base['manager_runtime']) not in json.loads((config/'runtime-incoming.json').read_text())
    assert 'customer' not in json.loads((config/'manager-runtime.json').read_text())
    accounts.set_enabled('customer',True);sync_module.sync(config,state,os.geteuid(),os.getegid())
    assert json.loads((config/'manager-runtime.json').read_text())['customer'] == data['manager-runtime.json']['customer']
    assert json.loads((config/'manager-incoming.json').read_text())[digest(base['customer'])] == 'customer'


def test_rejects_symlinked_account_db(tmp_path,monkeypatch):
    config=tmp_path/'config';state=tmp_path/'state';config.mkdir(mode=0o700);state.mkdir(mode=0o700)
    (state/'accounts.sqlite3').symlink_to(tmp_path/'elsewhere')
    with pytest.raises(ValueError): sync_module.sync(config,state,os.geteuid(),os.getegid())


def test_rejects_symlinked_output_before_touching_configuration(tmp_path):
    config=tmp_path/'config';state=tmp_path/'state';config.mkdir(mode=0o700);state.mkdir(mode=0o700)
    target=tmp_path/'target';target.write_text('unchanged')
    (state/'account-upstream.json').symlink_to(target)
    with pytest.raises(ValueError): sync_module.sync(config,state,os.geteuid(),os.getegid())
    assert target.read_text() == 'unchanged'


def test_refuses_to_replace_unmanaged_owner_binding(tmp_path, monkeypatch):
    config=tmp_path/'config';state=tmp_path/'state';config.mkdir(mode=0o700);state.mkdir(mode=0o700)
    monkeypatch.setenv('DASHBOARD_MODULE_STATE_DIR',str(state))
    accounts.bootstrap_admin('administrator','admin password over twelve')
    alice=accounts.create_user('alice','alice password over twelve')
    base={key:token() for key in ('customer','manager_runtime','runtime_code')}
    data={'installer-secrets.json':base,'manager-incoming.json':{},'runtime-incoming.json':{},'code-incoming.json':{},
          'manager-runtime.json':{alice['id']:{'url':'https://existing','token':'external'}},'runtime-code.json':{}}
    for name,value in data.items(): (config/name).write_text(json.dumps(value))
    (config/'installer-secrets.json').chmod(0o600);(state/'accounts.sqlite3').chmod(0o600)
    original=(config/'manager-runtime.json').read_text()
    with pytest.raises(ValueError,match='unowned'): sync_module.sync(config,state,os.geteuid(),os.getegid())
    assert (config/'manager-runtime.json').read_text() == original
    assert not (config/'multiuser-secrets.json').exists()


def test_provisioned_accounts_flow_through_separate_manager_identities(tmp_path,monkeypatch):
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient
    from worker_manager.http_common import owner_dependency
    from dashboard.app import create_app
    config=tmp_path/'config';state=tmp_path/'state';config.mkdir(mode=0o700);state.mkdir(mode=0o700)
    monkeypatch.setenv('DASHBOARD_MODULE_STATE_DIR',str(state))
    accounts.bootstrap_admin('administrator','admin password over twelve')
    alice=accounts.create_user('alice','alice password over twelve');bob=accounts.create_user('bob','bob password over twelve')
    base={key:token() for key in ('customer','manager_runtime','runtime_code')}
    data={'installer-secrets.json':base,'dashboard-incoming.json':{digest(base['customer']):'customer'},
          'manager-incoming.json':{digest(base['customer']):'customer'},'runtime-incoming.json':{digest(base['manager_runtime']):'customer'},
          'code-incoming.json':{digest(base['runtime_code']):'customer'},'manager-runtime.json':{},'runtime-code.json':{}}
    for name,value in data.items(): (config/name).write_text(json.dumps(value))
    (config/'installer-secrets.json').chmod(0o600);(state/'accounts.sqlite3').chmod(0o600)
    sync_module.sync(config,state,os.geteuid(),os.getegid())
    manager=FastAPI(); manager_owner=owner_dependency(config/'manager-incoming.json')
    @manager.get('/api/v1/workers')
    def list_workers(owner=Depends(manager_owner)): return {'workers':[{'owner':owner}]}
    manager_client=TestClient(manager)
    class Adapter:
        def __init__(self,credential):self.credential=credential
        def get(self,path):
            response=manager_client.get(path,headers={'Authorization':'Bearer '+self.credential})
            assert response.status_code==200
            return response.json()
    dashboard=TestClient(create_app(credential_path=config/'dashboard-incoming.json',upstream_factory=lambda owner,credential:{'worker-manager':Adapter(credential)}))
    alice_session=accounts.login('alice','alice password over twelve')['token']
    bob_session=accounts.login('bob','bob password over twelve')['token']
    for user,session in ((alice,alice_session),(bob,bob_session)):
        response=dashboard.get('/api/upstreams/workers',headers={'Authorization':'Bearer '+session})
        assert response.status_code==200 and response.json()['payload']['workers'][0]['owner']==user['id']


def test_new_sessions_use_isolated_real_worker_manager(tmp_path,monkeypatch):
    import io
    from urllib.error import HTTPError
    from urllib.parse import urlsplit
    from fastapi.testclient import TestClient
    from dashboard.app import create_app
    from public_api import PublicAPI
    from worker_manager.api import create_app as manager_app
    from worker_manager.control_service import ControlService
    config=tmp_path/'config';state=tmp_path/'state';config.mkdir(mode=0o700);state.mkdir(mode=0o700)
    monkeypatch.setenv('DASHBOARD_MODULE_STATE_DIR',str(state))
    accounts.bootstrap_admin('administrator','admin password over twelve')
    alice=accounts.create_user('alice','alice password over twelve');bob=accounts.create_user('bob','bob password over twelve')
    base={key:token() for key in ('customer','manager_runtime','runtime_code')}
    data={'installer-secrets.json':base,'dashboard-incoming.json':{digest(base['customer']):'customer'},
          'manager-incoming.json':{digest(base['customer']):'customer'},'runtime-incoming.json':{digest(base['manager_runtime']):'customer'},
          'code-incoming.json':{digest(base['runtime_code']):'customer'},'manager-runtime.json':{},'runtime-code.json':{}}
    for name,value in data.items(): (config/name).write_text(json.dumps(value))
    (config/'installer-secrets.json').chmod(0o600);(state/'accounts.sqlite3').chmod(0o600)
    sync_module.sync(config,state,os.geteuid(),os.getegid())
    service=ControlService(tmp_path/'manager.db',lambda owner:None)
    manager=TestClient(manager_app(service,config/'manager-incoming.json'))
    def factory(owner,credential):
        def transport(request,timeout):
            response=manager.request(request.get_method(),urlsplit(request.full_url).path,headers=dict(request.header_items()),content=request.data)
            if response.status_code>=400: raise HTTPError(request.full_url,response.status_code,'failed',response.headers,io.BytesIO(response.content))
            return io.BytesIO(response.content)
        return {'worker-manager':PublicAPI('https://manager.example',token=credential,transport=transport)}
    dashboard=TestClient(create_app(credential_path=config/'dashboard-incoming.json',upstream_factory=factory))
    a=accounts.login('alice','alice password over twelve')['token'];b=accounts.login('bob','bob password over twelve')['token']
    headers=lambda value:{'Authorization':'Bearer '+value}
    body={'worker_id':'private-worker','artifact_id':'published@1','artifact_hash':'sha256:'+'a'*64,'entrypoint':'worker:run'}
    try:
        assert dashboard.post('/api/upstreams/workers',headers=headers(a),json=body).status_code==201
        assert dashboard.get('/api/upstreams/workers/private-worker',headers=headers(b)).status_code==404
        assert dashboard.post('/api/upstreams/workers',headers=headers(b),json=body).status_code==201
        assert service.manager(alice['id']).get('private-worker') is not service.manager(bob['id']).get('private-worker')
        accounts.set_enabled(alice['id'],False)
        assert dashboard.get('/api/upstreams/workers',headers=headers(a)).status_code==401
        sync_module.sync(config,state,os.geteuid(),os.getegid())
        assert dashboard.get('/api/upstreams/workers',headers=headers(b)).status_code==200
    finally: service.close()
