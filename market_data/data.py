"""XAUUSD 1-minute storage and calculations, informed by db-gold ad23525."""
from datetime import datetime
import json
import math
import os
from pathlib import Path
import sqlite3
import time

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


def save_bars(bars):
    if not isinstance(bars, list) or len(bars) > 301:
        raise ValueError('invalid candle collection')
    parsed = [parse_bar(bar) for bar in bars]
    latest_open = max((bar['time'] for bar in parsed if bar['is_open']), default=None)
    db = connect()
    try:
        with db:
            for bar in parsed:
                if bar['is_open'] and bar['time'] != latest_open: continue
                db.execute('''INSERT INTO candles(time,open,high,low,close,tick_volume,is_open)
                    VALUES(:time,:open,:high,:low,:close,:tick_volume,:is_open)
                    ON CONFLICT(time) DO UPDATE SET open=excluded.open,high=excluded.high,
                    low=excluded.low,close=excluded.close,tick_volume=excluded.tick_volume,is_open=excluded.is_open
                    WHERE candles.is_open=1 OR excluded.is_open=0''', bar)
            if latest_open is not None:
                db.execute('DELETE FROM candles WHERE is_open=1 AND time != ?', (latest_open,))
            elif parsed:
                db.execute('DELETE FROM candles WHERE is_open=1')
            db.execute("INSERT INTO collector_status(key,value) VALUES('last_success',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(time.time()),))
            db.execute("INSERT INTO collector_status(key,value) VALUES('error','') ON CONFLICT(key) DO UPDATE SET value='' ")
    finally: db.close()
    return len(parsed)


def set_collector_error():
    db = connect()
    try:
        with db:
            db.execute("INSERT INTO collector_status(key,value) VALUES('error','Upstream unavailable or invalid response') ON CONFLICT(key) DO UPDATE SET value=excluded.value")
    finally: db.close()


def snapshot(limit=200, include_open=True):
    if type(limit) is not int or not 1 <= limit <= 1000 or type(include_open) is not bool:
        raise ValueError('invalid candle query')
    db = connect()
    try:
        rows = db.execute('SELECT time,open,high,low,close,tick_volume,is_open FROM candles ' +
                          ('' if include_open else 'WHERE is_open=0 ') + 'ORDER BY time DESC LIMIT ?', (limit,)).fetchall()
        status = dict(db.execute('SELECT key,value FROM collector_status').fetchall())
    finally: db.close()
    candles = [{**dict(row), 'is_open':bool(row['is_open'])} for row in reversed(rows)]
    return {'symbol':SYMBOL, 'interval':INTERVAL, 'candles':candles,
            'last_success':float(status['last_success']) if status.get('last_success') else None,
            'collector_error':status.get('error') or None}


def moving_average(candles, period=20):
    if type(period) is not int or not 1 <= period <= 500:
        raise ValueError('period must be between 1 and 500')
    result, running = [], 0.0
    for index, candle in enumerate(candles):
        running += candle['close']
        if index >= period: running -= candles[index - period]['close']
        if index >= period - 1:
            result.append({'time':candle['time'], 'value':running / period, 'is_open':candle['is_open']})
    return result


def chart(limit=200, period=20, include_open=True):
    data = snapshot(limit=limit, include_open=include_open)
    data['moving_average'] = {'type':'SMA', 'period':period, 'points':moving_average(data['candles'], period)}
    return data
