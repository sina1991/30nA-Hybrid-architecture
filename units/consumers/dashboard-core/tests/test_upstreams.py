import hashlib
import json

import pytest
from fastapi.testclient import TestClient
from dashboard.app import create_app
from public_api import ConsumerAPIError


@pytest.fixture
def configured(tmp_path):
    credentials = tmp_path/'credentials'
    credentials.write_text(json.dumps({hashlib.sha256(b'user-token').hexdigest():'alice'}))
    calls = []
    class Adapter:
        def get(self,path):
            calls.append(path)
            return {'workers':[{'worker_id':'alice-worker'}]}
    def factory(owner,token):
        assert owner == 'alice'
        assert token == 'user-token'
        return {'worker-manager':Adapter()}
    return TestClient(create_app(credential_path=credentials,upstream_factory=factory)),calls,credentials


def test_dashboard_never_contacts_upstream_without_valid_identity(configured):
    client,calls,_ = configured
    assert client.get('/api/upstreams/workers').status_code == 401
    assert client.get('/api/upstreams/workers',headers={'Authorization':'Bearer wrong'}).status_code == 401
    assert calls == []
    response = client.get('/api/upstreams/workers',headers={'Authorization':'Bearer user-token'})
    assert response.status_code == 200
    assert response.json()['payload']['workers'][0]['worker_id'] == 'alice-worker'
    assert calls == ['/api/v1/workers']
    assert 'user-token' not in client.get('/').text


@pytest.mark.parametrize('error,status', [('FORBIDDEN',403),('UNAUTHORIZED',401),('SERVICE_UNAVAILABLE',None),('INVALID_RESPONSE',None)])
def test_dashboard_upstream_errors_are_explicit_and_do_not_leak_credentials(tmp_path,error,status):
    path=tmp_path/'credentials'
    path.write_text(json.dumps({hashlib.sha256(b'test-token').hexdigest():'alice'}))
    class Adapter:
        def get(self,path): raise ConsumerAPIError(error,'sensitive upstream diagnostic',status)
    client=TestClient(create_app(credential_path=path,upstream_factory=lambda owner,token:{'worker-manager':Adapter()}))
    response=client.get('/api/upstreams/workers',headers={'Authorization':'Bearer test-token'})
    assert response.status_code == (status or 503)
    assert 'sensitive' not in response.text
    assert 'test-token' not in response.text
