"""Regression: invalid ID reuse must preserve active/terminal snapshots and keys."""
from dataclasses import replace
import hashlib
import io
import threading
import time
from uuid import uuid4
import zipfile

import pytest
from worker_manager import ExecutionRequest, WorkerDefinition
from worker_runtime import WorkerRuntime, SQLiteExecutionStore


def make_runtime(tmp_path):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w') as archive:
        archive.writestr('task.py', '''import time
def run(data, configuration):
    if data.get('slow'):time.sleep(5)
    if data.get('fail'):raise ValueError('trusted fixture failure')
    return {'value':7}
''')
    content=stream.getvalue()
    class Provider:
        def fetch(self,key):return content
    provider=Provider()
    database=tmp_path/'history.db'
    runtime=WorkerRuntime(provider,require_sandbox=False,execution_store=SQLiteExecutionStore(database))
    definition=WorkerDefinition('worker','artifact','sha256:'+hashlib.sha256(content).hexdigest(),'task:run')
    return runtime,provider,database,ExecutionRequest(definition,idempotency_key='original-key',timeout_seconds=15)


def start(runtime,request):
    results=[]
    thread=threading.Thread(target=lambda:results.append(runtime.submit(request)))
    thread.start()
    deadline=time.monotonic()+3
    while time.monotonic()<deadline:
        state=runtime.get(request.execution_id)
        if state is not None and state.status=='running':return thread,results
        time.sleep(.01)
    runtime.cancel(request.execution_id);thread.join(timeout=3)
    raise AssertionError('Trusted fixture did not start')


def invalid(request,kind):
    if kind=='entrypoint':return replace(request,definition=replace(request.definition,entrypoint='task:invalid-name'))
    if kind=='hash':return replace(request,definition=replace(request.definition,artifact_hash='sha256:invalid'))
    if kind=='timeout':return replace(request,timeout_seconds=float('nan'))
    if kind=='depth':return replace(request,depth=999)
    raise AssertionError(kind)


@pytest.mark.parametrize('terminal',['succeeded','failed','cancelled'])
@pytest.mark.parametrize('kind',['entrypoint','hash','timeout','depth'])
def test_invalid_reuse_preserves_terminal_history_and_persistent_idempotency(tmp_path,terminal,kind):
    runtime,provider,database,request=make_runtime(tmp_path)
    if terminal=='failed':request=replace(request,input_payload={'fail':True})
    if terminal=='cancelled':
        request=replace(request,input_payload={'slow':True})
        thread,results=start(runtime,request)
        assert runtime.cancel(request.execution_id)
        thread.join(timeout=3);assert not thread.is_alive()
        first=results[0]
    else:first=runtime.submit(request)
    assert first.status==terminal
    rejected=runtime.submit(invalid(request,kind))
    assert not rejected.accepted and rejected.error.code=='EXECUTION_CONFLICT'
    assert runtime.get(first.execution_id)==first
    restarted=WorkerRuntime(provider,require_sandbox=False,execution_store=SQLiteExecutionStore(database))
    assert restarted.get(first.execution_id)==first
    assert restarted.submit(replace(request,execution_id=str(uuid4())))==first


def test_invalid_reuse_cannot_terminate_a_running_execution(tmp_path):
    runtime,_,_,request=make_runtime(tmp_path)
    request=replace(request,input_payload={'slow':True})
    thread,results=start(runtime,request)
    try:
        response=runtime.submit(invalid(request,'entrypoint'))
        assert response.error.code=='EXECUTION_CONFLICT'
        assert runtime.get(request.execution_id).status=='running'
    finally:
        runtime.cancel(request.execution_id);thread.join(timeout=3)
    assert not thread.is_alive() and results[0].status=='cancelled'
