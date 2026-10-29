#!/usr/bin/env python3
"""Register/build/publish the trusted demo and enable its owner-scoped Worker."""
import argparse
import base64
import io
import json
from pathlib import Path
import stat
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'units/consumers/dashboard-core'))
from public_api import ConsumerAPIError, PublicAPI

WORKER_ID = 'demo-summary'
ARTIFACT_ID = WORKER_ID + '@1.0.0'


def source_archive():
    stream = io.BytesIO()
    source = ROOT/'examples/demo-summary'
    with zipfile.ZipFile(stream, 'w') as archive:
        # Fixed paths/timestamps/modes keep source registration repeatable.
        for relative in ['demo_worker.py','tests/__init__.py','tests/test_demo.py']:
            info = zipfile.ZipInfo(relative, date_time=(1980,1,1,0,0,0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, (source/relative).read_bytes())
    return stream.getvalue()


def seed(code, manager):
    code.post('/api/v1/sources', {'source_id':WORKER_ID,'source_version':'1.0.0',
        'source_content_base64':base64.b64encode(source_archive()).decode('ascii'),
        'entrypoint':'demo_worker:run','input_schema':{'type':'object',
            'required':['values'],'properties':{'values':{'type':'array','minItems':1,'maxItems':1000,
                'items':{'type':'number','minimum':-1e12,'maximum':1e12}}}},
        'output_schema':{'type':'object'}})
    built = code.post('/api/v1/builds', {'source_id':WORKER_ID,'source_version':'1.0.0'})['build']
    if built.get('status') != 'succeeded' or built.get('publishable') is not True:
        raise RuntimeError('Demo Build did not pass; inspect its Build history before continuing')
    published = code.post('/api/v1/artifacts/'+ARTIFACT_ID+'/publish',{'build_id':built['build_id']})['artifact']
    definition = {'worker_id':WORKER_ID,'artifact_id':ARTIFACT_ID,
                  'artifact_hash':published['artifact_hash'],'entrypoint':'demo_worker:run'}
    try:
        record = manager.post('/api/v1/workers', definition)
    except ConsumerAPIError as error:
        if error.status != 409:
            raise
        record = manager.get('/api/v1/workers/'+WORKER_ID)
        if record.get('definition') != definition:
            raise RuntimeError('Existing demo Worker references different code; it was not changed') from None
    if record['lifecycle'] == 'configured':
        record = manager.post('/api/v1/workers/'+WORKER_ID+'/enable',{})
    # An operator-disabled worker remains disabled on repeat setup.
    return {'worker_id':WORKER_ID,'artifact_id':ARTIFACT_ID,
            'artifact_hash':published['artifact_hash'],'lifecycle':record['lifecycle'],
            'sample_input':{'values':[10,20,30]},
            'expected_result':{'count':3,'sum':60,'min':10,'max':30,'mean':20.0}}


def read_token(path):
    path = Path(path)
    mode = path.stat().st_mode
    if not stat.S_ISREG(mode) or stat.S_IMODE(mode) & 0o077:
        raise ValueError('Token file must be a regular private file with mode 0400 or 0600')
    token = path.read_text().strip()
    if not token or not token.isascii() or any(c.isspace() for c in token):
        raise ValueError('Token file must contain one nonempty bearer token')
    return token


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--code-url',required=True)
    parser.add_argument('--manager-url',required=True)
    parser.add_argument('--code-token-file',required=True)
    parser.add_argument('--manager-token-file',required=True)
    args = parser.parse_args()
    if not all(url.startswith('https://') for url in (args.code_url,args.manager_url)):
        parser.error('Verified HTTPS service URLs are required')
    try:
        code = PublicAPI(args.code_url,token=read_token(args.code_token_file),timeout=120)
        manager = PublicAPI(args.manager_url,token=read_token(args.manager_token_file),timeout=15)
        result = seed(code,manager)
    except (OSError,ValueError,RuntimeError,ConsumerAPIError) as error:
        # Do not print credential files, HTTP headers or raw upstream diagnostics.
        print('Demo setup failed ('+type(error).__name__+'). Inspect service health and Build history.',file=sys.stderr)
        return 1
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__':
    sys.exit(main())
