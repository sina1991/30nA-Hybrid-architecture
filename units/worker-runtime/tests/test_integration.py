import io, zipfile, hashlib, sys, unittest
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[2]/'worker-manager'),str(Path(__file__).resolve().parents[1])]
from worker_manager import WorkerManager, WorkerDefinition
from worker_runtime import WorkerRuntime

def zipcode(code):
 b=io.BytesIO()
 with zipfile.ZipFile(b,'w') as z:z.writestr('task.py',code)
 return b.getvalue()
class Provider:
 def __init__(self,d):self.d=d
 def fetch(self,k):return self.d[k]
class Integration(unittest.TestCase):
 def setUp(self):
  self.d={'ok':zipcode('def run(input, configuration):\n return {"sum":sum(input["items"])}\n'),'bad':zipcode('def run(input, configuration):\n raise ValueError("broken")\n'),'slow':zipcode('import time\ndef run(input, configuration):\n time.sleep(2)\n return 1\n'),'parent':zipcode('def run(input, configuration):\n return {"value":7,"children":[{"worker_id":"ok","input":{"items":[2,3]}}]}\n')}
  self.defs={k:WorkerDefinition(k,k,'sha256:'+hashlib.sha256(v).hexdigest(),'task:run') for k,v in self.d.items()}
  self.runtime=WorkerRuntime(Provider(self.d),self.defs,require_sandbox=False)
  self.manager=WorkerManager(self.runtime)
  for d in self.defs.values():self.manager.register(d);self.manager.enable(d.worker_id)
 def test_success(self):
  r=self.manager.request_execution('ok',input_payload={'items':[1,2]});self.assertEqual(r.status,'succeeded');self.assertEqual(r.result,{'sum':3});self.assertEqual(self.runtime.get(r.execution_id),r)
 def test_bad_hash(self):
  self.manager.register(WorkerDefinition('tampered','ok','sha256:wrong','task:run'));self.manager.enable('tampered');self.assertEqual(self.manager.request_execution('tampered').error.code,'ARTIFACT_HASH_MISMATCH')
 def test_error(self):self.assertEqual(self.manager.request_execution('bad').error.code,'EXECUTION_ERROR')
 def test_timeout(self):self.assertEqual(self.manager.request_execution('slow',timeout_seconds=.05).error.code,'TIMEOUT')
 def test_children(self):
  r=self.manager.request_execution('parent');self.assertEqual(r.status,'succeeded');self.assertEqual(r.children[0].result,{'sum':5})
 def test_unavailable(self):
  del self.d['ok'];self.assertEqual(self.manager.request_execution('ok').error.code,'ARTIFACT_UNAVAILABLE')
 def test_idempotency(self):
  a=self.manager.request_execution('ok',input_payload={'items':[1]},idempotency_key='x');b=self.manager.request_execution('ok',input_payload={'items':[1]},idempotency_key='x');self.assertEqual(a.execution_id,b.execution_id)
  c=self.manager.request_execution('ok',input_payload={'items':[2]},idempotency_key='x');self.assertEqual(c.error.code,'IDEMPOTENCY_CONFLICT')
