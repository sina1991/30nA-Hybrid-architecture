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
    result = change(owner, 'slot-binding', slot, None, update)
    if module_id is not None and module_id != 'empty' and not only_if_missing:
        change(owner, 'slot-meta', slot, None, lambda old: (old if old is not None else {'overview': False}, old is None))
    return result


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


def _layout_db(owner):
    binding(owner, 'validation-probe')
    path = Path(os.environ.get('DASHBOARD_MODULE_STATE_DIR', '/var/lib/30na/dashboard')) / 'module-state.sqlite3'
    db = sqlite3.connect(path, timeout=10, isolation_level=None)
    db.execute('BEGIN IMMEDIATE')
    # Preserve all old bindings and their state. Only non-empty legacy slots
    # become active on first use of the new dashboard.
    marker = db.execute("SELECT 1 FROM module_state WHERE owner=? AND module='slot-layout' AND slot='migration'", (owner,)).fetchone()
    if marker is None:
        rows = db.execute("SELECT slot,value FROM module_state WHERE owner=? AND module='slot-binding'", (owner,)).fetchall()
        for slot, value in rows:
            if json.loads(value).get('module_id') != 'empty':
                db.execute("INSERT OR IGNORE INTO module_state(owner,module,slot,value) VALUES(?,'slot-meta',?,?)", (owner, slot, json.dumps({'overview': False})))
        db.execute("INSERT INTO module_state(owner,module,slot,value) VALUES(?,'slot-layout','migration','true')", (owner,))
    return db


def list_active(owner):
    db = _layout_db(owner)
    try:
        rows = db.execute("""SELECT b.slot,b.value,m.value FROM module_state b
            JOIN module_state m ON m.owner=b.owner AND m.slot=b.slot AND m.module='slot-meta'
            WHERE b.owner=? AND b.module='slot-binding' ORDER BY b.slot""", (owner,)).fetchall()
        db.commit()
        result = []
        for slot, value, raw_meta in rows:
            meta = json.loads(raw_meta)
            result.append({'slot': slot, **json.loads(value), 'overview': bool(meta.get('overview')),
                           'layout': meta.get('layout'), 'frame_color': meta.get('frame_color')})
        return result
    finally:
        db.close()


def create(owner):
    db = _layout_db(owner)
    try:
        count = db.execute("SELECT count(*) FROM module_state WHERE owner=? AND module='slot-meta'", (owner,)).fetchone()[0]
        if count >= 100:
            raise ValueError('slot limit reached')
        slot = 'slot-' + uuid4().hex[:12]
        config = {'module_id': 'empty', 'context': {}, 'revision': str(uuid4())}
        db.execute("INSERT INTO module_state(owner,module,slot,value) VALUES(?,'slot-binding',?,?)", (owner, slot, json.dumps(config)))
        db.execute("INSERT INTO module_state(owner,module,slot,value) VALUES(?,'slot-meta',?,?)", (owner, slot, json.dumps({'overview': False})))
        db.commit()
        return {'slot': slot, **config, 'overview': False}
    finally:
        db.close()


def bind_active(owner, slot, module_id, context, only_if_missing=False):
    if module_id not in MODULE_FILES:
        raise ValueError('unknown module')
    if not isinstance(context, dict) or set(context) - {'timezone', 'theme'} or any(
            not isinstance(value, str) or len(value) > 128 for value in context.values()):
        raise ValueError('invalid slot context')
    db = _layout_db(owner)
    try:
        meta = db.execute("SELECT 1 FROM module_state WHERE owner=? AND module='slot-meta' AND slot=?", (owner, slot)).fetchone()
        existing = db.execute("SELECT value FROM module_state WHERE owner=? AND module='slot-binding' AND slot=?", (owner, slot)).fetchone()
        if not meta or not existing: raise LookupError('slot is not active')
        value = json.loads(existing[0]) if only_if_missing else {'module_id': module_id, 'context': context, 'revision': str(uuid4())}
        if not only_if_missing:
            db.execute("UPDATE module_state SET value=? WHERE owner=? AND module='slot-binding' AND slot=?", (json.dumps(value), owner, slot))
        db.commit()
        return value
    finally:
        db.close()


def set_overview(owner, slot, visible):
    if type(visible) is not bool:
        raise ValueError('overview must be boolean')
    db = _layout_db(owner)
    try:
        row = db.execute("SELECT value FROM module_state WHERE owner=? AND module='slot-meta' AND slot=?", (owner, slot)).fetchone()
        if not row: raise LookupError('slot is not active')
        meta = json.loads(row[0]); meta['overview'] = visible
        db.execute("UPDATE module_state SET value=? WHERE owner=? AND module='slot-meta' AND slot=?", (json.dumps(meta), owner, slot))
        db.commit()
    finally:
        db.close()


def update_appearance(owner, slot, updates):
    if not isinstance(updates, dict) or not updates or set(updates) - {'layout', 'frame_color'}:
        raise ValueError('invalid slot appearance')
    if 'frame_color' in updates:
        color = updates['frame_color']
        if color is not None and (not isinstance(color, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', color)):
            raise ValueError('invalid frame color')
    if 'layout' in updates:
        layout = updates['layout']
        if not isinstance(layout, dict) or set(layout) != {'x', 'y', 'w', 'h'} or any(type(v) is not int for v in layout.values()):
            raise ValueError('invalid layout')
        if not (0 <= layout['x'] < 12 and 0 <= layout['y'] <= 500 and 2 <= layout['w'] <= 12
                and layout['x'] + layout['w'] <= 12 and 4 <= layout['h'] <= 40):
            raise ValueError('layout out of bounds')
    db = _layout_db(owner)
    try:
        row = db.execute("SELECT value FROM module_state WHERE owner=? AND module='slot-meta' AND slot=?", (owner, slot)).fetchone()
        if not row: raise LookupError('slot is not active')
        meta = json.loads(row[0]); meta.update(updates)
        db.execute("UPDATE module_state SET value=? WHERE owner=? AND module='slot-meta' AND slot=?", (json.dumps(meta), owner, slot))
        db.commit()
        return meta
    finally:
        db.close()


def delete(owner, slot):
    db = _layout_db(owner)
    try:
        exists = db.execute("SELECT 1 FROM module_state WHERE owner=? AND module='slot-meta' AND slot=?", (owner, slot)).fetchone()
        if not exists: raise LookupError('slot is not active')
        db.execute("DELETE FROM module_state WHERE owner=? AND slot=? AND module IN ('slot-binding','slot-meta','slot-output','counter','slot-note')", (owner, slot))
        db.commit()
    finally:
        db.close()


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
