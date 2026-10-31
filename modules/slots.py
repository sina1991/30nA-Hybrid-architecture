"""Owner-scoped server bindings between slots and trusted modules."""
import json
from pathlib import Path
import os
import re
import sqlite3
from uuid import uuid4
from market_data.indicators import CHART_DEFAULTS
from .module_state import change
from . import chat_store, technical, economic_calendar, indicator_profiles
from .execution import MODULE_FILES, HOST_MONITORS, MARKET_MODULES, run_module


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
    if module_id is not None and not only_if_missing:
        def update_meta(old):
            if old is None:
                return ({'overview': False}, True) if module_id != 'empty' else (None, False)
            worker = old.get('worker')
            if worker and worker.get('enabled') and worker.get('binding_revision') != result.get('revision'):
                worker.update(enabled=False, status='stopped', next_due=None, last_error='Module binding changed; configure this worker again.')
                return old, True
            return old, False
        change(owner, 'slot-meta', slot, None, update_meta)
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
                           'layout': meta.get('layout'), 'minimized': bool(meta.get('minimized', False)), 'output_settings':meta.get('output_settings', {'mode':'full','label':'','field':''}), 'frame_color': meta.get('frame_color'),
                           'display_theme': meta.get('display_theme', 'visual'), 'worker': meta.get('worker'),
                           'calendar_settings':meta.get('calendar_settings',economic_calendar.settings()),'profile_visibility':meta.get('profile_visibility',{}),
                           'technical_settings':meta.get('technical_settings', {}), 'technical_defaults':technical.DEFAULTS.get(json.loads(value)['module_id']),
                           'slot_type': meta.get('slot_type', 'standard'), 'chat_room':meta.get('chat_room', 'public'),
                           'chart_period': meta.get('chart_period', 20), 'chart_interval': meta.get('chart_interval', '1m'), 'indicator_period': meta.get('indicator_period', 14), 'chart_overlay': meta.get('chart_overlay', True),
                           'chart_live': meta.get('chart_live', True), 'chart_indicators': meta.get('chart_indicators', [])})
        return result
    finally:
        db.close()


def create(owner, slot_type='standard'):
    if slot_type not in ('standard', 'small', 'minimal', 'chart', 'fix-chart', 'chat', 'linear'): raise ValueError('invalid slot type')
    db = _layout_db(owner)
    try:
        count = db.execute("SELECT count(*) FROM module_state WHERE owner=? AND module='slot-meta'", (owner,)).fetchone()[0]
        if count >= 100:
            raise ValueError('slot limit reached')
        slot = 'slot-' + uuid4().hex[:12]
        config = {'module_id': 'gold-chart' if slot_type in ('chart', 'fix-chart') else 'chat-box' if slot_type == 'chat' else 'economic-calendar' if slot_type=='linear' else 'empty', 'context': {}, 'revision': str(uuid4())}
        db.execute("INSERT INTO module_state(owner,module,slot,value) VALUES(?,'slot-binding',?,?)", (owner, slot, json.dumps(config)))
        db.execute("INSERT INTO module_state(owner,module,slot,value) VALUES(?,'slot-meta',?,?)", (owner, slot, json.dumps({'overview': False, 'slot_type':slot_type})))
        db.commit()
        return {'slot': slot, **config, 'overview': False, 'slot_type':slot_type}
    finally:
        db.close()


def duplicate(owner, slot):
    """Copy slot configuration and state without starting its worker."""
    db = _layout_db(owner)
    try:
        row = db.execute("""SELECT b.value,m.value FROM module_state b JOIN module_state m
            ON m.owner=b.owner AND m.slot=b.slot AND m.module='slot-meta'
            WHERE b.owner=? AND b.slot=? AND b.module='slot-binding'""", (owner, slot)).fetchone()
        if row is None: raise LookupError('slot is not active')
        if db.execute("SELECT count(*) FROM module_state WHERE owner=? AND module='slot-meta'", (owner,)).fetchone()[0] >= 100:
            raise ValueError('slot limit reached')
        config, meta = json.loads(row[0]), json.loads(row[1])
        new_slot = 'slot-' + uuid4().hex[:12]
        config['revision'] = str(uuid4())
        meta.pop('layout', None); meta['minimized'] = False
        worker = meta.get('worker')
        if worker:
            worker.update(enabled=False, status='stopped', next_due=None, last_error=None,
                          last_started=None, last_finished=None, revision=str(uuid4()), binding_revision=config['revision'])
        db.execute("INSERT INTO module_state(owner,module,slot,value) VALUES(?,'slot-binding',?,?)", (owner,new_slot,json.dumps(config)))
        db.execute("INSERT INTO module_state(owner,module,slot,value) VALUES(?,'slot-meta',?,?)", (owner,new_slot,json.dumps(meta)))
        for module, value in db.execute("SELECT module,value FROM module_state WHERE owner=? AND slot=? AND module IN ('counter','slot-note')", (owner,slot)).fetchall():
            db.execute("INSERT INTO module_state(owner,module,slot,value) VALUES(?,?,?,?)", (owner,module,new_slot,value))
        db.commit()
        return {'slot':new_slot, **config, 'overview':bool(meta.get('overview'))}
    finally: db.close()


def bind_active(owner, slot, module_id, context, only_if_missing=False):
    if module_id not in MODULE_FILES:
        raise ValueError('unknown module')
    if not isinstance(context, dict) or set(context) - {'timezone', 'theme'} or any(
            not isinstance(value, str) or len(value) > 128 for value in context.values()):
        raise ValueError('invalid slot context')
    db = _layout_db(owner)
    try:
        meta = db.execute("SELECT value FROM module_state WHERE owner=? AND module='slot-meta' AND slot=?", (owner, slot)).fetchone()
        existing = db.execute("SELECT value FROM module_state WHERE owner=? AND module='slot-binding' AND slot=?", (owner, slot)).fetchone()
        if not meta or not existing: raise LookupError('slot is not active')
        value = json.loads(existing[0]) if only_if_missing else {'module_id': module_id, 'context': context, 'revision': str(uuid4())}
        if not only_if_missing:
            db.execute("UPDATE module_state SET value=? WHERE owner=? AND module='slot-binding' AND slot=?", (json.dumps(value), owner, slot))
            data = json.loads(meta[0]); worker = data.get('worker')
            if worker and worker.get('enabled'):
                worker.update(enabled=False, status='stopped', next_due=None, last_error='Module binding changed; configure this worker again.')
                db.execute("UPDATE module_state SET value=? WHERE owner=? AND module='slot-meta' AND slot=?", (json.dumps(data), owner, slot))
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
    if not isinstance(updates, dict) or not updates or set(updates) - {'layout', 'frame_color', 'display_theme', 'chart_period', 'chart_overlay', 'chart_live', 'slot_type', 'indicator_period', 'chart_interval', 'chart_indicators', 'minimized', 'output_settings', 'chat_room', 'technical_settings', 'profile_visibility', 'calendar_settings'}:
        raise ValueError('invalid slot appearance')
    if 'profile_visibility' in updates:
        visibility=updates['profile_visibility']
        known={p['id'] for p in indicator_profiles.list_profiles(owner)}
        if not isinstance(visibility,dict) or len(visibility)>24 or set(visibility)-known or any(type(v) is not bool for v in visibility.values()):raise ValueError('Invalid indicator visibility')
    if 'calendar_settings' in updates:
        updates=dict(updates,calendar_settings=economic_calendar.settings(updates['calendar_settings']))
    if 'technical_settings' in updates:
        configs=updates['technical_settings']
        if not isinstance(configs,dict) or not configs or set(configs)-set(technical.KINDS): raise ValueError('invalid technical settings')
        updates=dict(updates,technical_settings={kind:technical.settings(kind,value) for kind,value in configs.items()})
    if 'minimized' in updates and type(updates['minimized']) is not bool:
        raise ValueError('invalid minimized state')
    if 'output_settings' in updates:
        output = updates['output_settings']
        base = {'mode', 'label', 'field'}
        optional = {'font_size', 'label_size', 'text_color', 'label_color', 'background_color', 'font_weight', 'font_family', 'align', 'decimals'}
        if not isinstance(output, dict) or not base <= set(output) or set(output) - base - optional:
            raise ValueError('invalid output settings')
        if output['mode'] not in ('full', 'summary') or not isinstance(output['label'], str) or len(output['label']) > 32:
            raise ValueError('invalid output settings')
        field = output['field']
        if not isinstance(field, str) or len(field) > 160 or (field and not re.fullmatch(r'[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*', field)) or (output['mode'] == 'summary' and not field):
            raise ValueError('invalid output field')
        for key in ('font_size', 'label_size'):
            value = output.get(key)
            if value is not None and (type(value) is not int or not 8 <= value <= 72):
                raise ValueError('invalid output font size')
        for key in ('text_color', 'label_color', 'background_color'):
            value = output.get(key)
            if value is not None and (not isinstance(value, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', value)):
                raise ValueError('invalid output color')
        if output.get('font_weight') not in (None, 'normal', 'medium', 'bold'):
            raise ValueError('invalid output font weight')
        if output.get('font_family') not in (None, 'system', 'mono', 'serif'):
            raise ValueError('invalid output font family')
        if output.get('align') not in (None, 'left', 'center', 'right'):
            raise ValueError('invalid output alignment')
        decimals = output.get('decimals')
        if decimals is not None and (type(decimals) is not int or not 0 <= decimals <= 8):
            raise ValueError('invalid output decimals')
    if 'chat_room' in updates:
        if not isinstance(updates['chat_room'], str): raise ValueError('invalid chat room')
        if updates['chat_room'] not in {room['id'] for room in chat_store.list_rooms(owner)}: raise ValueError('invalid chat room')
    if 'slot_type' in updates and updates['slot_type'] not in ('standard', 'small', 'minimal', 'chart', 'fix-chart', 'chat', 'linear'):
        raise ValueError('invalid slot type')
    if 'chart_indicators' in updates and (not isinstance(updates['chart_indicators'], list) or len(updates['chart_indicators']) > len(CHART_DEFAULTS) or any(not isinstance(item, str) or item not in CHART_DEFAULTS for item in updates['chart_indicators']) or len(set(updates['chart_indicators'])) != len(updates['chart_indicators'])):
        raise ValueError('invalid chart indicators')
    if 'chart_interval' in updates and updates['chart_interval'] not in ('1m', '5m', '15m'):
        raise ValueError('invalid chart interval')
    if 'indicator_period' in updates and (type(updates['indicator_period']) is not int or not 1 <= updates['indicator_period'] <= 500):
        raise ValueError('invalid indicator period')
    if 'chart_period' in updates and (type(updates['chart_period']) is not int or not 1 <= updates['chart_period'] <= 500):
        raise ValueError('invalid chart period')
    if any(type(updates[key]) is not bool for key in ('chart_overlay', 'chart_live') if key in updates):
        raise ValueError('invalid chart option')
    if 'display_theme' in updates and updates['display_theme'] not in ('visual', 'compact', 'json'):
        raise ValueError('invalid display theme')
    if 'frame_color' in updates:
        color = updates['frame_color']
        if color is not None and (not isinstance(color, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', color)):
            raise ValueError('invalid frame color')
    if 'layout' in updates:
        layout = updates['layout']
        if not isinstance(layout, dict) or set(layout) != {'x', 'y', 'w', 'h'} or any(type(v) is not int for v in layout.values()):
            raise ValueError('invalid layout')
        if not (0 <= layout['x'] < 12 and 0 <= layout['y'] <= 500 and 1 <= layout['w'] <= 12
                and layout['x'] + layout['w'] <= 12 and 1 <= layout['h'] <= 40):
            raise ValueError('layout out of bounds')
    db = _layout_db(owner)
    try:
        row = db.execute("SELECT value FROM module_state WHERE owner=? AND module='slot-meta' AND slot=?", (owner, slot)).fetchone()
        if not row: raise LookupError('slot is not active')
        meta = json.loads(row[0])
        resulting_type = updates.get('slot_type', meta.get('slot_type', 'standard'))
        if 'layout' in updates:
            minimum_width = 1 if resulting_type == 'minimal' else 2
            minimum_height = 1 if resulting_type in ('minimal','linear') else 3 if resulting_type == 'small' else 4
            if updates['layout']['w'] < minimum_width or updates['layout']['h'] < minimum_height:
                raise ValueError('layout out of bounds')
        if resulting_type == 'fix-chart' and 'layout' in updates and (updates['layout']['w'], updates['layout']['h']) != (8, 8):
            raise ValueError('fixed chart dimensions cannot be changed')
        if resulting_type != meta.get('slot_type', 'standard') and (resulting_type in ('fix-chart', 'small', 'minimal','linear') or meta.get('slot_type') in ('small', 'minimal')):
            meta.pop('layout', None)
        if 'technical_settings' in updates:
            updates=dict(updates,technical_settings={**meta.get('technical_settings',{}),**updates['technical_settings']})
        meta.update(updates)
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
        db.execute("DELETE FROM module_state WHERE owner=? AND slot=? AND module IN ('slot-binding','slot-meta','slot-output','counter','slot-note','round-spacing')", (owner, slot))
        db.commit()
    finally:
        db.close()


def _market_preferences(owner, slot, module_id):
    meta = change(owner, 'slot-meta', slot, None, lambda old: (old, False)) or {}
    result = {'include_open': meta.get('chart_live', True)}
    if module_id in ('gold-chart', 'moving-average'): result['period'] = meta.get('chart_period', 20)
    if module_id == 'gold-chart': result['interval'] = meta.get('chart_interval', '1m')
    if module_id == 'rsi': result['period'] = meta.get('indicator_period', 14)
    return result


def _technical_preferences(owner, slot, module_id):
    meta = change(owner, 'slot-meta', slot, None, lambda old:(old,False)) or {}
    return {'settings':meta.get('technical_settings',{}).get(module_id,{}), '_state_owner':owner, '_state_slot':slot}


def execute(owner, slot, data, expected_module=None, expected_revision=None, request_ip=None):
    config = binding(owner, slot)
    if config is None:
        raise LookupError('slot is not configured')
    module_id = config['module_id']
    _authorize_host_monitor(owner, module_id)
    if expected_module is not None and expected_module != module_id:
        raise ValueError('slot binding changed')
    if expected_revision is not None and config.get('revision') != expected_revision:
        raise ValueError('slot binding changed')
    if not isinstance(data, dict) or any(str(key).startswith('_') or key in ('owner', 'slot') for key in data):
        raise ValueError('invalid module input')
    defaults = _market_preferences(owner, slot, module_id) if module_id in MARKET_MODULES else {}
    if module_id in technical.KINDS: defaults=_technical_preferences(owner,slot,module_id)
    payload = {**defaults, **config.get('context', {}), **data}
    if module_id=='myip':payload['_request_ip']=request_ip
    if module_id=='economic-calendar':
        meta=change(owner,'slot-meta',slot,None,lambda old:(old,False)) or {}
        payload={'settings':meta.get('calendar_settings',{}),**data}
    if module_id in technical.KINDS and isinstance(data.get('settings'), dict):
        payload['settings'] = {**defaults.get('settings', {}), **data['settings']}
    if module_id in ('counter', 'slot-note', 'chat-box'):
        payload.update(_state_owner=owner, _state_slot=slot)
    if module_id == 'chat-box':
        meta = change(owner, 'slot-meta', slot, None, lambda old:(old,False)) or {}
        payload.setdefault('room', meta.get('chat_room','public'))
    result = run_module(module_id, payload)
    if module_id not in ('clock', 'counter', 'slot-note', 'chat-box','myip','economic-calendar'):
        change(owner, 'slot-output', slot, None, lambda _: ({'module_id':module_id, 'binding_revision':config.get('revision'), 'result':result}, True))
    return {'slot':slot, 'module_id':module_id, 'result':result}


def read(owner, slot, request_ip=None):
    config = binding(owner, slot)
    if config is None:
        raise LookupError('slot is not configured')
    module_id = config['module_id']
    _authorize_host_monitor(owner, module_id)
    if module_id in ('clock', 'counter', 'slot-note', 'empty', 'theme-summary', 'dashboard-health') or module_id in MARKET_MODULES or module_id in technical.KINDS or module_id in ('chat-box','myip','economic-calendar'):
        data = {'action':'get'} if module_id in ('counter','slot-note') else {}
        # Reads never change the saved output or execute arbitrary code.
        defaults = _market_preferences(owner, slot, module_id) if module_id in MARKET_MODULES else {}
        if module_id in technical.KINDS: defaults=_technical_preferences(owner,slot,module_id)
        payload = {**defaults, **config.get('context', {}), **data}
        if module_id=='myip':payload['_request_ip']=request_ip
        if module_id=='economic-calendar':
            meta=change(owner,'slot-meta',slot,None,lambda old:(old,False)) or {}
            payload={'settings':meta.get('calendar_settings',{})}
        if module_id in ('counter','slot-note','chat-box'):
            payload.update(_state_owner=owner, _state_slot=slot)
        if module_id == 'chat-box':
            meta = change(owner, 'slot-meta', slot, None, lambda old:(old,False)) or {}
            payload['room'] = meta.get('chat_room','public')
        result = run_module(module_id, payload)
    else:
        saved = change(owner, 'slot-output', slot, None, lambda old:(old,False))
        result = saved['result'] if saved and saved.get('module_id') == module_id and saved.get('binding_revision') == config.get('revision') else None
    return {'slot':slot, **config, 'result':result}
