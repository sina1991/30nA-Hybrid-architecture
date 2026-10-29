"""Boot real production factories in isolated subprocesses without operational secrets."""
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import httpx
import pytest


@pytest.mark.parametrize('service', ['code','manager','runtime','dashboard'])
def test_production_entrypoint_auth_and_health(tmp_path,service):
    root=Path(__file__).resolve().parents[3]
    incoming=tmp_path/'incoming.json'
    incoming.write_text(json.dumps({hashlib.sha256(b'ephemeral-entrypoint-token').hexdigest():'alice'}))
    outgoing=tmp_path/'outgoing.json'
    outgoing.write_text(json.dumps({'alice':{'url':'https://localhost:1','token':'ephemeral-outgoing-token'}}))
    environment=os.environ.copy()
    environment.update(PYTHONPATH=':'.join(str(root/'units'/path) for path in [
        'code-manager','worker-manager','worker-runtime','consumers/dashboard-core']),
        DATA_MANAGER_DB=str(tmp_path/'data.sqlite3'),
        CODE_MANAGER_BLOB_ROOT=str(tmp_path/'blobs'),
        CODE_MANAGER_CREDENTIAL_FILE=str(incoming),
        WORKER_MANAGER_DB=str(tmp_path/'manager.sqlite3'),
        WORKER_MANAGER_CREDENTIAL_FILE=str(incoming),
        WORKER_MANAGER_RUNTIME_CREDENTIALS=str(outgoing),
        WORKER_RUNTIME_STATE_ROOT=str(tmp_path/'runtime'),
        WORKER_RUNTIME_CREDENTIAL_FILE=str(incoming),
        WORKER_RUNTIME_CODE_CREDENTIALS=str(outgoing),
        WORKER_RUNTIME_SANDBOX_IMAGE='sha256:'+'a'*64,
        DASHBOARD_CREDENTIAL_FILE=str(incoming),
        DASHBOARD_WORKER_MANAGER_URL='',DASHBOARD_CODE_MANAGER_URL='',
        DATA_MANAGER_ALLOW_INSECURE_HEADER='0',CODE_MANAGER_ALLOW_INSECURE_HEADER='0')
    listener=socket.socket();listener.bind(('127.0.0.1',0));port=listener.getsockname()[1];listener.close()
    if service=='code':
        command=[sys.executable,'-m','gunicorn','--workers','1','--threads','2','--bind',f'127.0.0.1:{port}',
                 'code_manager.production:create_app()']
        route='/api/v1/sources'
    else:
        module={'manager':'worker_manager','runtime':'worker_runtime','dashboard':'dashboard'}[service]
        command=[sys.executable,'-m','uvicorn',module+'.production:create_app','--factory','--host','127.0.0.1','--port',str(port),'--no-access-log']
        route={'manager':'/api/v1/workers','runtime':'/api/v1/executions/missing','dashboard':'/api/upstreams/workers'}[service]
    log=(tmp_path/'service.log').open('w')
    process=subprocess.Popen(command,cwd=root,env=environment,stdout=log,stderr=subprocess.STDOUT)
    try:
        with httpx.Client(trust_env=False,timeout=1) as client:
            deadline=time.monotonic()+10
            while time.monotonic()<deadline and process.poll() is None:
                try:
                    response=client.get(f'http://127.0.0.1:{port}'+route)
                    if response.status_code==401:break
                except httpx.TransportError:time.sleep(0.05)
            else:
                pytest.fail('Entrypoint did not start: '+(tmp_path/'service.log').read_text())
            assert response.status_code==401
            response=client.get(f'http://127.0.0.1:{port}'+route,headers={'Authorization':'Bearer ephemeral-entrypoint-token'})
            assert response.status_code=={'code':200,'manager':200,'runtime':404,'dashboard':503}[service],response.text
            if service!='code':
                assert client.get(f'http://127.0.0.1:{port}/health').json()['status']=='ok'
    finally:
        process.terminate()
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:process.kill();process.wait()
        log.close()
    assert process.returncode in (0,-15)
