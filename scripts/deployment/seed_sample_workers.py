#!/usr/bin/env python3
"""Build and register three owner-scoped sandboxed sample Workers."""
import argparse
import base64
import io
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'units/consumers/dashboard-core'))
from public_api import ConsumerAPIError, PublicAPI
from seed_demo import read_token

SAMPLES = {
    'sample-clock': {},
    'sample-math': {'values': [10, 20, 30]},
    'sample-text': {'text': 'Hello, 30nA!'},
}
VERSION = '1.0.0'


def archive_for(worker_id):
    source = ROOT / 'examples' / worker_id
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        for relative in ('worker.py', 'tests/__init__.py', 'tests/test_worker.py'):
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, (source / relative).read_bytes())
    return stream.getvalue()


def register_sample(code, manager, worker_id):
    artifact_id = worker_id + '@' + VERSION
    code.post('/api/v1/sources', {'source_id': worker_id, 'source_version': VERSION,
        'source_content_base64': base64.b64encode(archive_for(worker_id)).decode('ascii'),
        'entrypoint': 'worker:run', 'input_schema': {'type': 'object'}, 'output_schema': {'type': 'object'}})
    build = code.post('/api/v1/builds', {'source_id': worker_id, 'source_version': VERSION})['build']
    if build.get('status') != 'succeeded' or build.get('publishable') is not True:
        raise RuntimeError('Build failed; inspect Build history before retrying')
    artifact = code.post('/api/v1/artifacts/' + artifact_id + '/publish', {'build_id': build['build_id']})['artifact']
    definition = {'worker_id': worker_id, 'artifact_id': artifact_id,
                  'artifact_hash': artifact['artifact_hash'], 'entrypoint': 'worker:run'}
    try:
        worker = manager.post('/api/v1/workers', definition)
    except ConsumerAPIError as error:
        if error.status != 409: raise
        worker = manager.get('/api/v1/workers/' + worker_id)
        if worker.get('definition') != definition:
            raise RuntimeError('Existing Worker has a different definition; it was not changed') from None
    if worker['lifecycle'] == 'configured':
        worker = manager.post('/api/v1/workers/' + worker_id + '/enable', {})
    return {'worker_id': worker_id, 'lifecycle': worker['lifecycle'], 'sample_input': SAMPLES[worker_id]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--code-url', default='https://localhost:18443')
    parser.add_argument('--manager-url', default='https://localhost:18444')
    parser.add_argument('--token-file', default='/etc/30na/customer-token')
    args = parser.parse_args()
    if not args.code_url.startswith('https://') or not args.manager_url.startswith('https://'):
        parser.error('Verified HTTPS service URLs are required')
    try:
        token = read_token(args.token_file)
        code = PublicAPI(args.code_url, token=token, timeout=120)
        manager = PublicAPI(args.manager_url, token=token, timeout=15)
        for worker_id in SAMPLES:
            print(json.dumps(register_sample(code, manager, worker_id), ensure_ascii=False), flush=True)
    except (OSError, ValueError, RuntimeError, ConsumerAPIError, KeyError) as error:
        print('Sample setup stopped (' + type(error).__name__ + '). Inspect service health, Build history and existing Workers before retrying.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
