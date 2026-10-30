"""Contracts for owner-scoped server monitoring and slot results."""
import hashlib
import json

from fastapi.testclient import TestClient
import pytest

from dashboard.app import app, create_app
from modules import slots
from modules.execution import run_module


def test_monitor_is_not_exposed_by_public_module_endpoint():
    response = TestClient(app).post('/api/modules/system-monitor/run', json={})
    assert response.status_code == 403


def test_slot_monitor_result_is_owner_scoped_and_binding_checked(tmp_path, monkeypatch):
    monkeypatch.setenv('DASHBOARD_MODULE_STATE_DIR', str(tmp_path))
    monkeypatch.setenv('THIRTYNA_MONITOR_OWNERS', 'alice')
    creds = tmp_path / 'credentials'
    creds.write_text(json.dumps({hashlib.sha256(f'{owner}-token'.encode()).hexdigest(): owner for owner in ('alice', 'bob')}))
    client = TestClient(create_app(credential_path=creds, upstream_factory=lambda *_: {}))
    alice = {'Authorization': 'Bearer alice-token'}
    bob = {'Authorization': 'Bearer bob-token'}
    bind = '/api/upstreams/slots/slot-01/binding'
    execute = '/api/upstreams/slots/slot-01/execute'
    read = '/api/upstreams/slots/slot-01/read'
    assert client.post(read, json={'module_id': 'disk-usage'}).status_code == 401
    assert client.post(bind, headers=alice, json={'module_id': 'disk-usage'}).status_code == 200
    response = client.post(execute, headers=alice, json={'module_id': 'disk-usage', 'input': {}})
    assert response.status_code == 200
    result = response.json()['payload']['result']
    assert result['path'] == '/' and result['total_bytes'] > 0
    assert client.post(read, headers=alice, json={'module_id': 'disk-usage'}).json()['payload']['result'] == result
    assert client.post(read, headers=alice, json={'module_id': 'system-monitor'}).status_code == 422
    assert client.post(read, headers=bob, json={'module_id': 'disk-usage'}).status_code == 404
    assert client.post(bind, headers=bob, json={'module_id': 'disk-usage'}).status_code == 200
    assert client.post(execute, headers=bob, json={'module_id': 'disk-usage', 'input': {}}).status_code == 422


def test_log_and_disk_paths_require_explicit_permission(tmp_path, monkeypatch):
    log = tmp_path / 'log.txt'
    log.write_text('first\nerror here\nlast\n')
    monkeypatch.delenv('THIRTYNA_MONITOR_LOG_PATHS', raising=False)
    with pytest.raises(ValueError):
        run_module('log-viewer', {'path': str(log)})
    monkeypatch.setenv('THIRTYNA_MONITOR_LOG_PATHS', str(log))
    assert run_module('log-viewer', {'path': str(log), 'query': 'error'})['lines'] == ['error here']
    monkeypatch.setenv('THIRTYNA_MONITOR_DISK_PATHS', '/')
    with pytest.raises(ValueError):
        run_module('disk-usage', {'path': str(tmp_path)})


def test_rebinding_invalidates_saved_slot_output(tmp_path, monkeypatch):
    monkeypatch.setenv('DASHBOARD_MODULE_STATE_DIR', str(tmp_path))
    slots.binding('customer', 'slot-01', 'disk-usage')
    slots.execute('customer', 'slot-01', {})
    assert slots.read('customer', 'slot-01')['result'] is not None
    slots.binding('customer', 'slot-01', 'network-monitor')
    assert slots.read('customer', 'slot-01')['result'] is None
