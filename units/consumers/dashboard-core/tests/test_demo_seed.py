import importlib.util
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[4]
spec=importlib.util.spec_from_file_location('demo_seed_unit',ROOT/'scripts/deployment/seed_demo.py')
seed=importlib.util.module_from_spec(spec);spec.loader.exec_module(seed)


def test_token_file_must_be_private(tmp_path):
    path=tmp_path/'token';path.write_text('unit-only-token\n');path.chmod(0o600)
    assert seed.read_token(path)=='unit-only-token'
    path.chmod(0o644)
    with pytest.raises(ValueError,match='private'):seed.read_token(path)
    path.chmod(0o600);path.write_text('bad\nvalue')
    with pytest.raises(ValueError):seed.read_token(path)


def test_seed_does_not_replace_conflicting_worker_or_reenable_disabled_worker():
    class Code:
        def post(self,path,body):
            if path=='/api/v1/sources':return {}
            if path=='/api/v1/builds':return {'build':{'status':'succeeded','publishable':True,'build_id':'a'*32}}
            return {'artifact':{'artifact_hash':'sha256:'+'b'*64}}
    class Manager:
        def __init__(self):self.changed=False;self.wrong=False
        def post(self,path,body):
            if path=='/api/v1/workers':raise seed.ConsumerAPIError('CONFLICT','exists',409)
            self.changed=True;return {}
        def get(self,path):
            return {'definition':{'worker_id':seed.WORKER_ID,'artifact_id':seed.ARTIFACT_ID,
                'artifact_hash':'sha256:'+('c' if self.wrong else 'b')*64,'entrypoint':'demo_worker:run'},'lifecycle':'disabled'}
    manager=Manager()
    assert seed.seed(Code(),manager)['lifecycle']=='disabled'
    assert not manager.changed
    manager.wrong=True
    with pytest.raises(RuntimeError,match='different code'):seed.seed(Code(),manager)
    assert not manager.changed
