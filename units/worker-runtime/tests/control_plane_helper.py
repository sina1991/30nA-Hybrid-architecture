"""Real HTTPS Manager -> Runtime -> CODE and Dashboard read integration."""
from contextlib import contextmanager
import socket
import json
import os
import subprocess
import importlib.util
from pathlib import Path
import ssl
import threading
import time

import httpx
import uvicorn


@contextmanager
def https_server(app, cert, key):
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0))
    port = listener.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port,
        ssl_certfile=str(cert),ssl_keyfile=str(key),log_level='error',access_log=False,timeout_graceful_shutdown=5))
    thread=threading.Thread(target=server.run,kwargs={'sockets':[listener]},daemon=True)
    thread.start()
    try:
        deadline=time.monotonic()+10
        while not server.started and thread.is_alive() and time.monotonic()<deadline:
            time.sleep(0.01)
        assert server.started,'HTTPS test server did not start'
        yield f'https://localhost:{port}'
    finally:
        server.should_exit=True
        thread.join(timeout=15)
        listener.close()
        assert not thread.is_alive(),'HTTPS test server did not stop'


def exercise_control_plane(root,cert,key,credentials,code_url,image,artifact_hash):
    from worker_runtime import CodeManagerArtifactProvider,DockerSandboxBackend,SQLiteExecutionStore,WorkerRuntime
    from worker_runtime.api import create_app as runtime_app
    from worker_manager.control_service import ControlService
    from worker_manager.api import create_app as manager_app
    from worker_manager.http_gateway import RuntimeHTTPGateway
    from dashboard.app import create_app as dashboard_app
    from public_api import PublicAPI
    runtimes={}
    def factory(owner):
        instance=WorkerRuntime(CodeManagerArtifactProvider(code_url,'Bearer '+owner+'-integration-token'),
            sandbox_backend=DockerSandboxBackend(image),execution_store=SQLiteExecutionStore(root/(owner+'-runtime.db')))
        runtimes[owner]=instance
        return instance
    with https_server(runtime_app(credentials,factory),cert,key) as runtime_url:
        try:
            RuntimeHTTPGateway(runtime_url,'alice-integration-token').get('missing')
        except httpx.ConnectError:
            pass  # The ephemeral private CA must not be trusted by default.
        else:
            raise AssertionError('Untrusted Runtime certificate was accepted')
        def gateway(owner):
            return RuntimeHTTPGateway(runtime_url,owner+'-integration-token',ca_file=str(cert))
        service=ControlService(root/'manager.db',gateway)
        with https_server(manager_app(service,credentials),cert,key) as manager_url:
            def upstream(owner,token): return {'worker-manager':PublicAPI(manager_url,token=token)}
            with https_server(dashboard_app(credential_path=credentials,upstream_factory=upstream),cert,key) as dashboard_url:
                with httpx.Client(verify=ssl.create_default_context(cafile=str(cert)),trust_env=False) as client:
                    auth={'Authorization':'Bearer alice-integration-token'}
                    other={'Authorization':'Bearer bob-integration-token'}
                    body={'worker_id':'managed-worker','artifact_id':'sample-worker@1.0.0','artifact_hash':artifact_hash,
                          'entrypoint':'worker:run','configuration':{'increment':2}}
                    response=client.post(manager_url+'/api/v1/workers',headers=auth,json=body)
                    assert response.status_code==201,response.text
                    assert client.post(manager_url+'/api/v1/workers/managed-worker/enable',headers=auth).status_code==200
                    assert client.get(manager_url+'/api/v1/workers/managed-worker',headers=other).status_code==404
                    assert client.get(dashboard_url+'/api/upstreams/workers').status_code==401
                    dashboard=client.get(dashboard_url+'/api/upstreams/workers',headers=auth)
                    assert dashboard.status_code==200,dashboard.text
                    assert dashboard.json()['payload']['workers'][0]['definition']['worker_id']=='managed-worker'
                    assert client.get(dashboard_url+'/api/upstreams/workers',headers=other).json()['payload']['workers']==[]
                    repository=Path(__file__).resolve().parents[3]
                    spec=importlib.util.spec_from_file_location('seed_demo',repository/'scripts/deployment/seed_demo.py')
                    seeder=importlib.util.module_from_spec(spec);spec.loader.exec_module(seeder)
                    code_api=PublicAPI(code_url,token='alice-integration-token',timeout=60)
                    manager_api=PublicAPI(manager_url,token='alice-integration-token')
                    demo=seeder.seed(code_api,manager_api)
                    repeated=seeder.seed(code_api,manager_api)
                    assert demo==repeated
                    assert demo['lifecycle']=='enabled'
                    payload={'input_payload' :{'value':40},'idempotency_key':'test-job'}
                    response=client.post(dashboard_url+'/api/upstreams/workers/managed-worker/executions',headers=auth,json=payload)
                    assert response.status_code==202,response.text
                    eid=response.json()['payload']['execution_id']
                    deadline=time.monotonic()+30
                    while time.monotonic()<deadline:
                        result=client.get(dashboard_url+'/api/upstreams/executions/'+eid,headers=auth).json()['payload']
                        if result['status'] in ('succeeded','failed','cancelled'):break
                        time.sleep(0.1)
                    assert result['status']=='succeeded',result
                    assert result['result']['result']=={'value':42}
                    assert client.get(runtime_url+'/api/v1/executions/'+eid,headers=other).status_code==404
                    assert client.post(dashboard_url+'/api/upstreams/executions/'+eid+'/cancel',headers=other).status_code==404
                    assert client.post(dashboard_url+'/api/upstreams/workers/managed-worker/executions',headers=auth,json=payload).json()['payload']['execution_id']==eid
                    if os.environ.get('DASHBOARD_SKIP_BROWSER')!='1':
                        script=repository/'units/consumers/dashboard-core/browser-tests/check.cjs'
                        browser=subprocess.run(['node',str(script)],text=True,input=json.dumps({
                            'url':dashboard_url,'token':'alice-integration-token',
                            'screenshot':os.environ.get('DASHBOARD_SCREENSHOT')}),
                            stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=75)
                        assert browser.returncode==0,browser.stdout+'\n'+browser.stderr
                        assert 'PASS: Chromium real Dashboard' in browser.stdout
        restarted=ControlService(root/'manager.db',gateway)
        try:
            assert restarted.get('alice',eid)['result']['result']=={'value':42}
        finally:
            restarted.close()
