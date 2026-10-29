#!/usr/bin/env python3
"""Run the complete release suites against an owned, disposable DATA MANAGER."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
SUITES=['contracts/core/tests','contracts/code/tests','units/data-manager/tests',
        'units/code-manager/tests','units/worker-manager/tests','units/worker-runtime/tests',
        'units/consumers/dashboard-core/tests','units/consumers/dashboard-core/legacy-tests',
        'units/integration/agent08/tests']


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--image',default=os.environ.get('WORKER_RUNTIME_SANDBOX_TEST_IMAGE'))
    parser.add_argument('--unit-only',action='store_true',help='Explicitly allow skipped Docker checks; not release acceptance')
    parser.add_argument('--evidence-dir',default='tmp/release-evidence')
    args=parser.parse_args()
    if not args.unit_only:
        if not args.image or not re.fullmatch(r'sha256:[0-9a-f]{64}',args.image):
            parser.error('The full suite requires --image sha256:<immutable image ID>')
        subprocess.run(['docker','image','inspect',args.image],stdout=subprocess.DEVNULL,check=True,timeout=15)
        subprocess.run(['docker','info','--format','version={{.ServerVersion}} security={{json .SecurityOptions}} cgroup={{.CgroupVersion}}'],check=True,timeout=15)
    os.chdir(ROOT)
    evidence=Path(args.evidence_dir).resolve()
    evidence.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy()
    env.update(PYTHONPATH=':'.join(str(ROOT/path) for path in ['units/code-manager','units/worker-manager','units/worker-runtime','units/consumers/dashboard-core']),
        PYTHONDONTWRITEBYTECODE='1',CODE_MANAGER_INTEGRATION='1',DATA_MANAGER_ALLOW_INSECURE_HEADER='1',CODE_MANAGER_ALLOW_INSECURE_HEADER='0')
    for name in ['WORKER_RUNTIME_SANDBOX_TEST_IMAGE','CODE_MANAGER_BUILD_SANDBOX_IMAGE']:
        if args.unit_only:env.pop(name,None)
        else:env[name]=args.image
    sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    dirty=subprocess.check_output(['git','status','--porcelain'],text=True)
    tracked_diff=subprocess.check_output(['git','diff','HEAD','--binary'])
    metadata={'commit':sha,'dirty':bool(dirty),'tracked_diff_sha256':hashlib.sha256(tracked_diff).hexdigest(),
              'python':sys.version,'image':args.image,'unit_only':args.unit_only}
    started=time.time()
    with tempfile.TemporaryDirectory(prefix='30na-ci-') as directory:
        ready=Path(directory)/'ready.json'
        with (evidence/'data-manager.log').open('w') as log:
            server=subprocess.Popen([sys.executable,str(ROOT/'scripts/development/data_manager_server.py'),
                '--database',str(Path(directory)/'data.sqlite3'),'--ready-file',str(ready)],env=env,stdout=log,stderr=subprocess.STDOUT)
            try:
                deadline=time.monotonic()+15
                while not ready.exists() and server.poll() is None and time.monotonic()<deadline:
                    time.sleep(0.05)
                if server.poll() is not None or not ready.exists():raise RuntimeError('Owned DATA MANAGER did not start')
                port=json.loads(ready.read_text())['port']
                url=f'http://127.0.0.1:{port}'
                client=urllib.request.build_opener(urllib.request.ProxyHandler({}))
                with client.open(url+'/health',timeout=5) as response:
                    if json.load(response).get('status')!='ok':raise RuntimeError('DATA MANAGER health failed')
                env['CODE_MANAGER_DATA_MANAGER_URL']=url
                command=[sys.executable,'-m','pytest',*SUITES,'--import-mode=importlib','-q','-ra','--tb=short',
                         '--junitxml='+str(evidence/'tests.xml')]
                with (evidence/'tests.log').open('w') as tests_log:
                    result=subprocess.run(command,env=env,stdout=tests_log,stderr=subprocess.STDOUT)
                print((evidence/'tests.log').read_text())
                cases=list(ET.parse(evidence/'tests.xml').getroot().iter('testcase'))
                skipped=sum(case.find('skipped') is not None for case in cases)
                code=result.returncode
                if not cases or (skipped and not args.unit_only):
                    print('Release gate failed: no executed tests or skipped required checks')
                    code=1
                metadata.update(exit_code=code,pytest_exit_code=result.returncode,
                    test_cases=len(cases),skipped=skipped,elapsed_seconds=round(time.time()-started,2))
                (evidence/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
                return code
            finally:
                if server.poll() is None:
                    server.terminate()
                    try:server.wait(timeout=5)
                    except subprocess.TimeoutExpired:server.kill();server.wait()

if __name__=='__main__':
    sys.exit(main())
