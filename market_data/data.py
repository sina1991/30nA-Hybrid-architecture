"""XAUUSD 1-minute storage and calculations, informed by db-gold ad23525."""
from datetime import datetime
import json
import math
import os
from pathlib import Path
import sqlite3
import time
from . import indicators

SYMBOL = 'XAUUSD'
INTERVAL = '1m'


def database_path():
    return Path(os.environ.get('DASHBOARD_MODULE_STATE_DIR', '/var/lib/30na/dashboard')) / 'market' / 'xauusd.db'


def connect():
    path = database_path()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('''CREATE TABLE IF NOT EXISTS candles (
        time INTEGER PRIMARY KEY, open REAL NOT NULL, high REAL NOT NULL,
        low REAL NOT NULL, close REAL NOT NULL, tick_volume INTEGER,
        is_open INTEGER NOT NULL CHECK(is_open IN (0,1)))''')
    db.execute('CREATE TABLE IF NOT EXISTS collector_status (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
    db.execute('''CREATE TABLE IF NOT EXISTS indicator_specs (
        name TEXT NOT NULL, parameters TEXT NOT NULL, computed_revision INTEGER NOT NULL DEFAULT -1,
        PRIMARY KEY(name,parameters))''')
    db.execute('''CREATE TABLE IF NOT EXISTS indicator_values (
        name TEXT NOT NULL, parameters TEXT NOT NULL, time INTEGER NOT NULL,
        value_json TEXT NOT NULL, is_open INTEGER NOT NULL CHECK(is_open IN (0,1)),
        PRIMARY KEY(name,parameters,time))''')
    if db.execute("SELECT 1 FROM collector_status WHERE key='candle_revision'").fetchone() is None:
        db.execute("INSERT OR IGNORE INTO collector_status(key,value) VALUES('candle_revision','0')")
        for name, params in indicators.DEFAULTS.items():
            db.execute('INSERT OR IGNORE INTO indicator_specs(name,parameters) VALUES(?,?)',
                       (name, json.dumps(params, sort_keys=True, separators=(',', ':'))))
        db.commit()
    return db


def parse_bar(bar):
    if not isinstance(bar, dict) or type(bar.get('isOpen')) is not bool:
        raise ValueError('invalid candle state')
    stamp = bar.get('openTime')
    if not isinstance(stamp, str) or len(stamp) > 64:
        raise ValueError('invalid candle timestamp')
    dt = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError('candle timestamp must include a timezone')
    timestamp = int(dt.timestamp())
    if timestamp < 0 or timestamp % 60 != 0:
        raise ValueError('invalid one-minute candle timestamp')
    fields = []
    for key in ('open', 'high', 'low', 'close'):
        raw = bar.get(key)
        if isinstance(raw, bool): raise ValueError('invalid candle price')
        try: number = float(raw)
        except (TypeError, ValueError, OverflowError): raise ValueError('invalid candle price') from None
        if not math.isfinite(number) or number <= 0: raise ValueError('invalid candle price')
        fields.append(number)
    op, high, low, close = fields
    if low > min(op, close) or high < max(op, close) or low > high:
        raise ValueError('inconsistent candle prices')
    volume = bar.get('tickVolume')
    if volume is not None:
        if type(volume) is bool: raise ValueError('invalid tick volume')
        try: numeric = float(volume)
        except (TypeError, ValueError, OverflowError): raise ValueError('invalid tick volume') from None
        if not math.isfinite(numeric) or not numeric.is_integer() or not 0 <= numeric < 2**63:
            raise ValueError('invalid tick volume')
        volume = int(numeric)
    return {'time':timestamp, 'open':op, 'high':high, 'low':low, 'close':close,
            'tick_volume':volume, 'is_open':bar['isOpen']}


def save_bars(bars, historical=False):
    if not isinstance(bars, list) or len(bars) > 301:
        raise ValueError('invalid candle collection')
    parsed = [parse_bar(bar) for bar in bars]
    if historical: parsed = [bar for bar in parsed if not bar['is_open']]
    latest_open = max((bar['time'] for bar in parsed if bar['is_open']), default=None)
    db = connect()
    try:
        with db:
            changed = False
            dirty_from = None
            for bar in parsed:
                if bar['is_open'] and bar['time'] != latest_open: continue
                cursor = db.execute('''INSERT INTO candles(time,open,high,low,close,tick_volume,is_open)
                    VALUES(:time,:open,:high,:low,:close,:tick_volume,:is_open)
                    ON CONFLICT(time) DO UPDATE SET open=excluded.open,high=excluded.high,
                    low=excluded.low,close=excluded.close,tick_volume=excluded.tick_volume,is_open=excluded.is_open
                    WHERE (candles.is_open=1 OR excluded.is_open=0) AND
                    (candles.open IS NOT excluded.open OR candles.high IS NOT excluded.high OR
                     candles.low IS NOT excluded.low OR candles.close IS NOT excluded.close OR
                     candles.tick_volume IS NOT excluded.tick_volume OR candles.is_open IS NOT excluded.is_open)''', bar)
                if cursor.rowcount > 0:
                    changed = True
                    dirty_from = bar['time'] if dirty_from is None else min(dirty_from, bar['time'])
            old_open = [row[0] for row in db.execute('SELECT time FROM candles WHERE is_open=1').fetchall()]
            if historical:
                removed = 0
            elif latest_open is not None:
                removed = db.execute('DELETE FROM candles WHERE is_open=1 AND time != ?', (latest_open,)).rowcount
            elif parsed:
                removed = db.execute('DELETE FROM candles WHERE is_open=1').rowcount
            else: removed = 0
            if changed or removed:
                if removed and old_open:
                    dirty_from = min(old_open) if dirty_from is None else min(dirty_from, *old_open)
                db.execute("UPDATE collector_status SET value=CAST(CAST(value AS INTEGER)+1 AS TEXT) WHERE key='candle_revision'")
                previous_dirty = db.execute("SELECT value FROM collector_status WHERE key='indicator_dirty_from'").fetchone()
                if previous_dirty and previous_dirty[0]: dirty_from = min(dirty_from, int(previous_dirty[0]))
                db.execute("INSERT INTO collector_status(key,value) VALUES('indicator_dirty_from',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(dirty_from),))
            if not historical:
                db.execute("INSERT INTO collector_status(key,value) VALUES('last_success',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(time.time()),))
                db.execute("INSERT INTO collector_status(key,value) VALUES('error','') ON CONFLICT(key) DO UPDATE SET value='' ")
    finally: db.close()
    try: refresh_indicators()
    except (ValueError, OSError, sqlite3.Error):
        db = connect()
        try:
            with db: db.execute("INSERT INTO collector_status(key,value) VALUES('indicators_error','Indicator update failed') ON CONFLICT(key) DO UPDATE SET value=excluded.value")
        finally: db.close()
    return len(parsed)


def backfill_state():
    db = connect()
    try:
        oldest = db.execute('SELECT MIN(time) FROM candles WHERE is_open=0').fetchone()[0]
        row = db.execute("SELECT value FROM collector_status WHERE key='backfill_state'").fetchone()
        return oldest, row[0] if row else 'pending'
    finally: db.close()


def set_backfill_state(value):
    if value not in ('pending', 'running', 'no_older_data', 'error'): raise ValueError('invalid backfill status')
    db = connect()
    try:
        with db: db.execute("INSERT INTO collector_status(key,value) VALUES('backfill_state',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (value,))
    finally: db.close()


def set_collector_error():
    db = connect()
    try:
        with db:
            db.execute("INSERT INTO collector_status(key,value) VALUES('error','Upstream unavailable or invalid response') ON CONFLICT(key) DO UPDATE SET value=excluded.value")
    finally: db.close()


def snapshot(limit=200, include_open=True, end_time=None):
    if type(limit) is not int or not 1 <= limit <= 1000 or type(include_open) is not bool or (end_time is not None and (type(end_time) is not int or end_time < 0)):
        raise ValueError('invalid candle query')
    db = connect()
    try:
        conditions, args = [], []
        if not include_open: conditions.append('is_open=0')
        if end_time is not None: conditions.append('time<=?'); args.append(end_time)
        rows = db.execute('SELECT time,open,high,low,close,tick_volume,is_open FROM candles ' +
                          ('WHERE ' + ' AND '.join(conditions) + ' ' if conditions else '') + 'ORDER BY time DESC LIMIT ?', (*args, limit)).fetchall()
        status = dict(db.execute('SELECT key,value FROM collector_status').fetchall())
    finally: db.close()
    candles = [{**dict(row), 'is_open':bool(row['is_open'])} for row in reversed(rows)]
    return {'symbol':SYMBOL, 'interval':INTERVAL, 'candles':candles,
            'last_success':float(status['last_success']) if status.get('last_success') else None,
            'collector_error':status.get('error') or None}


def moving_average(candles, period=20):
    return indicators.calculate('sma', candles, {'period':period})


def refresh_indicators():
    db = connect()
    try:
        db.execute('BEGIN IMMEDIATE')
        revision = int(db.execute("SELECT value FROM collector_status WHERE key='candle_revision'").fetchone()[0])
        specs = db.execute('SELECT name,parameters,computed_revision FROM indicator_specs WHERE computed_revision != ?', (revision,)).fetchall()
        if not specs:
            db.commit(); return
        rows = db.execute('SELECT time,open,high,low,close,tick_volume,is_open FROM candles ORDER BY time').fetchall()
        candles = [{**dict(row), 'is_open':bool(row['is_open'])} for row in rows]
        dirty_row = db.execute("SELECT value FROM collector_status WHERE key='indicator_dirty_from'").fetchone()
        dirty = int(dirty_row[0]) if dirty_row and dirty_row[0] else None
        for spec in specs:
            name, parameters = spec['name'], spec['parameters']
            points = indicators.calculate(name, candles, json.loads(parameters))
            cutoff = dirty if spec['computed_revision'] >= 0 else None
            for point in points:
                if cutoff is not None and point['time'] < cutoff: continue
                value = {key:item for key,item in point.items() if key not in ('time', 'is_open')}
                db.execute('''INSERT INTO indicator_values(name,parameters,time,value_json,is_open) VALUES(?,?,?,?,?)
                    ON CONFLICT(name,parameters,time) DO UPDATE SET value_json=excluded.value_json,is_open=excluded.is_open
                    WHERE indicator_values.value_json != excluded.value_json OR indicator_values.is_open != excluded.is_open''',
                    (name, parameters, point['time'], json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False), int(point['is_open'])))
            db.execute('''DELETE FROM indicator_values WHERE name=? AND parameters=? AND (? IS NULL OR time>=?) AND time NOT IN (SELECT time FROM candles)''', (name, parameters, cutoff, cutoff))
            if points and cutoff is None:
                db.execute('DELETE FROM indicator_values WHERE name=? AND parameters=? AND time<?', (name, parameters, points[0]['time']))
            elif not points:
                db.execute('DELETE FROM indicator_values WHERE name=? AND parameters=?', (name, parameters))
            db.execute('UPDATE indicator_specs SET computed_revision=? WHERE name=? AND parameters=?', (revision, name, parameters))
        db.execute("INSERT INTO collector_status(key,value) VALUES('indicators_error','') ON CONFLICT(key) DO UPDATE SET value=''")
        db.execute("INSERT INTO collector_status(key,value) VALUES('indicator_dirty_from','') ON CONFLICT(key) DO UPDATE SET value=''")
        db.commit()
    finally: db.close()


def indicator(name, parameters, limit=200, include_open=True, end_time=None):
    if type(limit) is not int or not 1 <= limit <= 1000 or type(include_open) is not bool or (end_time is not None and (type(end_time) is not int or end_time < 0)):
        raise ValueError('invalid indicator query')
    params = indicators.normalize(name, parameters)
    encoded = json.dumps(params, sort_keys=True, separators=(',', ':'))
    db = connect()
    try:
        db.execute('BEGIN IMMEDIATE')
        count = db.execute('SELECT count(*) FROM indicator_specs').fetchone()[0]
        exists = db.execute('SELECT 1 FROM indicator_specs WHERE name=? AND parameters=?', (name, encoded)).fetchone()
        if not exists and count >= 32: raise ValueError('indicator configuration limit reached')
        db.execute('INSERT OR IGNORE INTO indicator_specs(name,parameters) VALUES(?,?)', (name, encoded))
        db.commit()
    finally: db.close()
    refresh_indicators()
    db = connect()
    try:
        suffix = ('' if include_open else 'AND is_open=0 ') + ('AND time<=? ' if end_time is not None else '')
        args = [name, encoded] + ([end_time] if end_time is not None else []) + [limit]
        rows = db.execute('SELECT time,value_json,is_open FROM indicator_values WHERE name=? AND parameters=? ' + suffix + 'ORDER BY time DESC LIMIT ?', args).fetchall()
        status = dict(db.execute('SELECT key,value FROM collector_status').fetchall())
    finally: db.close()
    points = [{'time':row['time'], **json.loads(row['value_json']), 'is_open':bool(row['is_open'])} for row in reversed(rows)]
    return {'symbol':SYMBOL, 'interval':INTERVAL, 'type':name.upper(), 'parameters':params, 'points':points,
            'last_success':float(status['last_success']) if status.get('last_success') else None,
            'collector_error':status.get('error') or None, 'indicator_error':status.get('indicators_error') or None}


def database_table(table, limit=50, offset=0, candle_state="all", indicator_name="all"):
    queries = {
        'candles_with_indicators': ('''SELECT c.time,c.open,c.high,c.low,c.close,c.tick_volume,c.is_open,
            s.value_json AS sma_json,r.value_json AS rsi_json,m.value_json AS macd_json
            FROM candles c
            LEFT JOIN indicator_values s ON s.time=c.time AND s.name='sma' AND s.parameters='{"period":20}'
            LEFT JOIN indicator_values r ON r.time=c.time AND r.name='rsi' AND r.parameters='{"period":14}'
            LEFT JOIN indicator_values m ON m.time=c.time AND m.name='macd' AND m.parameters='{"fast":12,"signal":9,"slow":26}'
            ORDER BY c.time DESC LIMIT ? OFFSET ?''', 'candles'),
        'candles': ('SELECT time,open,high,low,close,tick_volume,is_open FROM candles ORDER BY time DESC LIMIT ? OFFSET ?', 'candles'),
        'indicator_values': ('SELECT name,parameters,time,value_json,is_open FROM indicator_values ORDER BY time DESC,name,parameters LIMIT ? OFFSET ?', 'indicator_values'),
        'indicator_specs': ('SELECT name,parameters,computed_revision FROM indicator_specs ORDER BY name,parameters LIMIT ? OFFSET ?', 'indicator_specs'),
        'collector_status': ('SELECT key,value FROM collector_status ORDER BY key LIMIT ? OFFSET ?', 'collector_status'),
    }
    if table not in queries or type(limit) is not int or not 1 <= limit <= 200 or type(offset) is not int or not 0 <= offset <= 1000000:
        raise ValueError('invalid database query')
    if candle_state not in ('all', 'open', 'closed') or indicator_name not in ('all', 'sma', 'rsi', 'macd'):
        raise ValueError('invalid database filter')
    query, count_table = queries[table]
    conditions, args = [], []
    if candle_state != 'all' and table in ('candles_with_indicators', 'candles', 'indicator_values'):
        conditions.append(('c.is_open' if table == 'candles_with_indicators' else 'is_open') + '=?')
        args.append(1 if candle_state == 'open' else 0)
    if indicator_name != 'all' and table in ('indicator_values', 'indicator_specs'):
        conditions.append('name=?'); args.append(indicator_name)
    query, order = query.rsplit('ORDER BY ', 1)
    where = ' WHERE ' + ' AND '.join(conditions) if conditions else ''
    count_where = where.replace('c.is_open', 'is_open')
    query += where + ' ORDER BY ' + order
    db = connect()
    try:
        rows = [dict(row) for row in db.execute(query, (*args, limit, offset)).fetchall()]
        count = db.execute('SELECT count(*) FROM ' + count_table + count_where, args).fetchone()[0]
    finally: db.close()
    if table == 'candles_with_indicators':
        for row in rows:
            sma = json.loads(row.pop('sma_json') or '{}'); rsi = json.loads(row.pop('rsi_json') or '{}'); macd = json.loads(row.pop('macd_json') or '{}')
            row.update(sma_20=sma.get('value'), rsi_14=rsi.get('value'), macd=macd.get('macd'),
                       macd_signal=macd.get('signal'), macd_histogram=macd.get('histogram'))
    return {'table':table, 'rows':rows, 'count':count, 'limit':limit, 'offset':offset}


def chart(limit=200, period=20, include_open=True, end_time=None, interval='1m'):
    if interval not in ('1m', '5m', '15m'):
        raise ValueError('invalid chart interval')
    if interval != '1m':
        if type(limit) is not int or not 1 <= limit <= 1000 or type(include_open) is not bool or (end_time is not None and (type(end_time) is not int or end_time < 0)):
            raise ValueError('invalid candle query')
        indicators.normalize('sma', {'period':period})
        minutes = int(interval[:-1]); seconds = minutes * 60
        db = connect()
        try:
            db.execute('BEGIN')
            where = 'WHERE time<=?' if end_time is not None else ''
            args = ([end_time] if end_time is not None else []) + [(limit + period + 2) * minutes]
            rows = db.execute('SELECT time,open,high,low,close,tick_volume,is_open FROM candles ' + where + ' ORDER BY time DESC LIMIT ?', args).fetchall()
            status = dict(db.execute('SELECT key,value FROM collector_status').fetchall())
        finally: db.close()
        groups = {}
        for row in reversed(rows):
            bucket = row['time'] // seconds * seconds
            groups.setdefault(bucket, []).append(row)
        bars = []
        now = int(time.time())
        for bucket, group in groups.items():
            complete = len(group) == minutes and all(item['time'] == bucket + index * 60 for index, item in enumerate(group))
            provisional = bucket + seconds > now or any(item['is_open'] for item in group)
            contiguous = all(item['time'] == bucket + index * 60 for index, item in enumerate(group))
            if not complete and (not provisional or not contiguous): continue
            if provisional and not include_open: continue
            volume = [item['tick_volume'] for item in group]
            bars.append({'time':bucket, 'open':group[0]['open'], 'high':max(item['high'] for item in group),
                         'low':min(item['low'] for item in group), 'close':group[-1]['close'],
                         'tick_volume':sum(item for item in volume if item is not None) if any(item is not None for item in volume) else None,
                         'is_open':provisional})
        points = moving_average(bars, period)
        selected = bars[-limit:]
        times = {bar['time'] for bar in selected}
        return {'symbol':SYMBOL, 'interval':interval, 'candles':selected,
                'last_success':float(status['last_success']) if status.get('last_success') else None,
                'collector_error':status.get('error') or None,
                'moving_average':{'type':'SMA', 'period':period, 'points':[point for point in points if point['time'] in times]}}
    data = snapshot(limit=limit, include_open=include_open, end_time=end_time)
    result = indicator('sma', {'period':period}, limit=limit, include_open=include_open, end_time=end_time)
    data['moving_average'] = {'type':'SMA', 'period':period, 'points':result['points']}
    return data
