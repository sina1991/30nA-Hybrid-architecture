"""Owner-scoped declarative market signal rules; no user code is executed here."""
import math
import time
import json
from uuid import uuid4
from .module_state import change
from . import indicator_profiles
from market_data.data import chart

OPS = ('gt', 'lt', 'gte', 'lte', 'crosses_above', 'crosses_below')
FIELDS = {'sma':('value',), 'rsi':('value',), 'macd':('macd', 'signal', 'histogram')}


def list_rules(owner):
    return change(owner, 'signal-rules', 'catalog', [], lambda old: (old, False))


def save(owner, data, rule_id=None):
    if not isinstance(data, dict) or set(data) != {'name','interval','enabled','signal','conditions'}: raise ValueError('invalid signal rule')
    if not isinstance(data['name'], str) or not data['name'].strip() or len(data['name']) > 80: raise ValueError('invalid rule name')
    if data['interval'] not in ('1m','5m','15m') or type(data['enabled']) is not bool or data['signal'] not in ('BUY','SELL'):
        raise ValueError('invalid rule options')
    profiles = {item['id']:item for item in indicator_profiles.list_profiles(owner)}
    conditions = data['conditions']
    if not isinstance(conditions, list) or not 1 <= len(conditions) <= 8: raise ValueError('one to eight conditions required')
    for item in conditions:
        if not isinstance(item, dict) or set(item) != {'left','field','op','right_kind','right','right_field'}: raise ValueError('invalid condition')
        if item['left'] not in profiles or item['field'] not in FIELDS[profiles[item['left']]['type']] or item['op'] not in OPS: raise ValueError('invalid condition')
        if item['right_kind'] == 'number':
            if type(item['right']) not in (int,float) or not math.isfinite(item['right']) or item['right_field'] != '': raise ValueError('invalid value')
        elif item['right_kind'] == 'indicator':
            if item['right'] not in profiles or item['right_field'] not in FIELDS[profiles[item['right']]['type']]: raise ValueError('invalid indicator')
        else: raise ValueError('invalid comparison')
    ident = rule_id or 'signal-' + uuid4().hex[:12]
    rule = {'id':ident, **data, 'name':data['name'].strip(), 'revision':uuid4().hex}
    def update(old):
        index = next((i for i,item in enumerate(old) if item['id'] == ident), None)
        if rule_id is not None and index is None: raise LookupError('signal not found')
        if index is None:
            if len(old) >= 32: raise ValueError('signal limit reached')
            return [*old, rule], True
        new = list(old); new[index] = rule
        return new, True
    change(owner, 'signal-rules', 'catalog', [], update)
    return rule


def delete(owner, rule_id):
    def update(old):
        new = [item for item in old if item['id'] != rule_id]
        if len(new) == len(old): raise LookupError('signal not found')
        return new, True
    change(owner, 'signal-rules', 'catalog', [], update)


def market_input(owner, interval='1m'):
    profiles = [item for item in indicator_profiles.list_profiles(owner) if item['enabled']]
    if not profiles: raise ValueError('no enabled indicators')
    data = chart(limit=2, include_open=False, interval=interval, profiles=profiles)
    if not data['last_success'] or time.time() - data['last_success'] > 90 or data['collector_error']:
        raise ValueError('market data is unavailable or stale')
    if not data['candles']: raise ValueError('no closed candles available')
    if time.time() - data['candles'][-1]['time'] > {'1m':60,'5m':300,'15m':900}[interval] + 120:
        raise ValueError('latest closed candle is stale')
    return {'symbol':data['symbol'], 'interval':interval, 'candles':data['candles'], 'indicators':data.get('series', [])}


def evaluate(owner, rule_id):
    rule = next((item for item in list_rules(owner) if item['id'] == rule_id), None)
    if rule is None: raise LookupError('signal not found')
    if not rule['enabled']: return {'rule_id':rule_id, 'signal':'WAIT', 'reason':'Rule is disabled'}
    try: payload = market_input(owner, rule['interval'])
    except ValueError as exc: return {'rule_id':rule_id, 'signal':'WAIT', 'reason':str(exc)}
    series = {item['id']:item for item in payload['indicators']}
    candles = payload['candles']; current = candles[-1]['time']; previous = candles[-2]['time'] if len(candles) > 1 else None
    previous_valid = previous is not None and current - previous == {'1m':60,'5m':300,'15m':900}[rule['interval']]
    def value(profile_id, field, stamp):
        source = series.get(profile_id)
        if not source: return None
        point = next((item for item in source['points'] if item['time'] == stamp), None)
        return point.get(field) if point else None
    checks = []
    for item in rule['conditions']:
        left = value(item['left'], item['field'], current)
        right = item['right'] if item['right_kind'] == 'number' else value(item['right'], item['right_field'], current)
        if left is None or right is None: return {'rule_id':rule_id, 'signal':'WAIT', 'reason':'Indicator disabled or insufficient data', 'time':current}
        op = item['op']
        if op.startswith('crosses_'):
            old_left = value(item['left'], item['field'], previous) if previous_valid else None
            old_right = item['right'] if item['right_kind'] == 'number' else value(item['right'], item['right_field'], previous) if previous_valid else None
            if old_left is None or old_right is None: return {'rule_id':rule_id, 'signal':'WAIT', 'reason':'Previous candle unavailable', 'time':current}
            matched = old_left <= old_right and left > right if op == 'crosses_above' else old_left >= old_right and left < right
        else: matched = {'gt':left > right,'lt':left < right,'gte':left >= right,'lte':left <= right}[op]
        checks.append({'left':left,'right':right,'matched':matched})
    return {'rule_id':rule_id, 'signal':rule['signal'] if all(item['matched'] for item in checks) else 'WAIT', 'time':current, 'checks':checks}


def _fingerprint(owner, rule_id):
    rule = next((item for item in list_rules(owner) if item['id'] == rule_id), None)
    if rule is None: raise LookupError('signal not found')
    profiles = indicator_profiles.list_profiles(owner)
    return json.dumps({'revision':rule.get('revision'), 'profiles':profiles}, sort_keys=True, separators=(',', ':'))


def latest(owner, rule_id):
    result = change(owner, 'signal-result', rule_id, None, lambda old: (old, False))
    if result is None or result.get('configuration') != _fingerprint(owner, rule_id): return None
    if time.time() - result.get('evaluated_at', 0) > 150:
        return {**result, 'signal':'WAIT', 'reason':'Evaluation is stale'}
    return result


def evaluate_and_save(owner, rule_id):
    before = _fingerprint(owner, rule_id)
    result = evaluate(owner, rule_id)
    if before != _fingerprint(owner, rule_id):
        return {'rule_id':rule_id, 'signal':'WAIT', 'reason':'Configuration changed during evaluation'}
    result['evaluated_at'] = time.time(); result['configuration'] = before
    change(owner, 'signal-result', rule_id, None, lambda old: (result, True))
    return result


def evaluate_enabled_rules():
    """Run bounded declarative rules for each owner after market collection."""
    import os
    from pathlib import Path
    import sqlite3
    db = sqlite3.connect(Path(os.environ.get('DASHBOARD_MODULE_STATE_DIR', '/var/lib/30na/dashboard')) / 'module-state.sqlite3', timeout=10)
    try:
        rows = db.execute("SELECT owner FROM module_state WHERE module='signal-rules' AND slot='catalog'").fetchall()
    except sqlite3.OperationalError:
        return
    finally: db.close()
    for (owner,) in rows:
        for rule in list_rules(owner):
            if rule['enabled']:
                try: evaluate_and_save(owner, rule['id'])
                except (ValueError, LookupError, OSError, sqlite3.Error):
                    continue


class SignalScheduler:
    """One background evaluator per state directory; rule results are read-only signals."""
    def __init__(self):
        import threading
        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        import threading
        if self.thread is None:
            self.thread = threading.Thread(target=self._loop, name='30na-signal-evaluator', daemon=True)
            self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread is not None: self.thread.join(timeout=3)

    def _loop(self):
        import fcntl
        import logging
        import os
        import sqlite3
        from pathlib import Path
        lock = None
        try:
            while not self.stop_event.is_set():
                try:
                    if lock is None:
                        directory = Path(os.environ.get('DASHBOARD_MODULE_STATE_DIR', '/var/lib/30na/dashboard'))
                        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
                        fd = os.open(directory / 'signal-scheduler.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
                        try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        except BlockingIOError:
                            os.close(fd); self.stop_event.wait(10); continue
                        lock = fd
                    evaluate_enabled_rules()
                except (OSError, ValueError, TypeError, KeyError, sqlite3.Error):
                    logging.getLogger(__name__).warning('Signal evaluation is unavailable')
                self.stop_event.wait(60)
        finally:
            if lock is not None: os.close(lock)
