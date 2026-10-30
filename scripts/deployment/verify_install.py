#!/usr/bin/env python3
"""Exercise the installed authenticated Dashboard path; no credential output."""
import json
import ssl

import httpx
from pathlib import Path
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'units/consumers/dashboard-core'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from seed_demo import read_token


class DashboardAPI:
    """Installer-only adapter for the Dashboard's explicit BFF routes."""
    def __init__(self,client):self.client=client

    def _request(self,method,path,payload=None):
        if not path.startswith('/api/upstreams/') or '..' in path or '?' in path:
            raise ValueError('Unsupported verification route')
        with self.client.stream(method,path,json=payload) as response:
            response.raise_for_status()
            body=bytearray()
            for part in response.iter_bytes():
                body.extend(part)
                if len(body)>2_000_000:raise ValueError('Verification response too large')
        data=json.loads(body)
        if not str(data.get('contract_version','')).startswith('1.') or not isinstance(data.get('payload'),dict):
            raise ValueError('Invalid verification envelope')
        return data['payload']

    def post(self,path,payload):return self._request('POST',path,payload)
    def get(self,path):return self._request('GET',path)


def verify(api, *, timeout=90):
    def execute(payload):
        accepted=api.post('/api/upstreams/workers/demo-summary/executions',{
            'input_payload':payload,'idempotency_key':'installer-'+str(uuid.uuid4())})
        eid=accepted['execution_id']
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            result=api.get('/api/upstreams/executions/'+eid)
            if result['status'] in ('succeeded','failed','cancelled'):return result
            time.sleep(.5)
        raise RuntimeError('Demo execution did not finish')
    successful=execute({'values':[10,20,30]})
    if successful['status']!='succeeded' or successful['result']['result']!={'count':3,'sum':60,'min':10,'max':30,'mean':20}:
        raise RuntimeError('Unexpected demo result')
    failed=execute({'values':['invalid']})
    if failed['status']!='failed' or failed['result']['error']['code']!='EXECUTION_ERROR':
        raise RuntimeError('Invalid demo input did not fail with its execution error')
    return True


def main():
    try:
        token=read_token('/etc/30na/customer-token')
        with httpx.Client(base_url='https://localhost:18446',
                          verify=ssl.create_default_context(cafile='/etc/30na/ca/trust.pem'),
                          headers={'Authorization':'Bearer '+token},trust_env=False,
                          follow_redirects=False,timeout=15) as client:
            verify(DashboardAPI(client))
    except Exception:
        print('Installation verification failed; inspect 30na-review status and service history.',file=sys.stderr)
        return 1
    print('PASS: authenticated Dashboard -> Manager -> Docker Runtime: success/result and invalid-input failure')
    return 0

if __name__=='__main__':sys.exit(main())
