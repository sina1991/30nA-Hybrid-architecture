"""Owner-scoped server bindings between slots and trusted modules."""
import json
from pathlib import Path
import os
import re
import sqlite3
from uuid import uuid4
from .module_state import change
from .execution import MODULE_FILES, HOST_MONITORS, run_module


def _authorize_host_monitor(owner, module_id):
    if module_id in HOST_MONITORS:
        allowed = {item.strip() for item in os.environ.get('THIRTYNA_MONITOR_OWNERS', 'customer').split(',') if item.strip()}
        if owner not in allowed:
            raise ValueError('owner is not authorized for host monitors')


def binding(owner, slot, module_id=None, context=None, only_if_missing=False):
    if module_id is not None and module_id not in MODULE_FILES:
        raise ValueError('unknown module')
    context = {} if context is None else context
    if not isinstance(context, dict) or set(context) - {'timezone', 'theme'}:
        raise ValueError('invalid slot context')
    if any(not isinstance(value, str) or len(value) > 128 for value in context.values()):
        raise ValueError('invalid slot context')
    def update(previous):
        if module_id is None or (only_if_missing and previous is not None):
            return previous, False
        return {'module_id': module_id, 'context': context, 'revision': str(uuid4())}, True
    return change(owner, 'slot-binding', slot, None, update)


def list_slots(owner):
    # Reuse the same validation and initialization without creating a slot binding.
    binding(owner, 'validation-probe')
    path = Path(os.environ.get('DASHBOARD_MODULE_STATE_DIR', '/var/lib/30na/dashboard')) / 'module-state.sqlite3'
    db = sqlite3.connect(path, timeout=10)
    try:
        rows = db.execute("SELECT slot,value FROM module_state WHERE owner=? AND module='slot-binding' ORDER BY slot", (owner,)).fetchall()
    finally:
        db.close()
    return [{'slot':slot, **json.loads(value)} for slot,value in rows]


def execute(owner, slot, data, expected_module=None):
    config = binding(owner, slot)
    if config is None:
        raise LookupError('slot is not configured')
    module_id = config['module_id']
    _authorize_host_monitor(owner, module_id)
    if expected_module is not None and expected_module != module_id:
        raise ValueError('slot binding changed')
    if not isinstance(data, dict) or any(str(key).startswith('_') or key in ('owner', 'slot') for key in data):
        raise ValueError('invalid module input')
    payload = {**config.get('context', {}), **data}
    if module_id in ('counter', 'slot-note'):
        payload.update(_state_owner=owner, _state_slot=slot)
    result = run_module(module_id, payload)
    if module_id not in ('clock', 'counter', 'slot-note'):
        change(owner, 'slot-output', slot, None, lambda _: ({'module_id':module_id, 'binding_revision':config.get('revision'), 'result':result}, True))
    return {'slot':slot, 'module_id':module_id, 'result':result}


def read(owner, slot):
    config = binding(owner, slot)
    if config is None:
        raise LookupError('slot is not configured')
    module_id = config['module_id']
    _authorize_host_monitor(owner, module_id)
    if module_id in ('clock', 'counter', 'slot-note', 'empty', 'theme-summary', 'dashboard-health'):
        data = {'action':'get'} if module_id in ('counter','slot-note') else {}
        # Reads never change the saved output or execute arbitrary code.
        payload = {**config.get('context', {}), **data}
        if module_id in ('counter','slot-note'):
            payload.update(_state_owner=owner, _state_slot=slot)
        result = run_module(module_id, payload)
    else:
        saved = change(owner, 'slot-output', slot, None, lambda old:(old,False))
        result = saved['result'] if saved and saved.get('module_id') == module_id and saved.get('binding_revision') == config.get('revision') else None
    return {'slot':slot, **config, 'result':result}
