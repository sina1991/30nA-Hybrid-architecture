"""Bounded Biquote collector for the Dashboard service."""
import fcntl
import json
import logging
import os
import sqlite3
from pathlib import Path
import threading
import time

import httpx
from . import data

LOG = logging.getLogger(__name__)
URL = 'https://biquote.io/api/XAUUSD/ohlc'


def fetch_bars(limit):
    with httpx.Client(timeout=10, follow_redirects=False, trust_env=False) as client:
        with client.stream('GET', URL, params={'interval':'1m', 'limit':limit}, headers={'Accept':'application/json'}) as response:
            response.raise_for_status()
            body = bytearray()
            for chunk in response.iter_bytes():
                body.extend(chunk)
                if len(body) > 1_000_000: raise ValueError('response too large')
    payload = json.loads(body)
    if not isinstance(payload, dict) or not isinstance(payload.get('bars'), list):
        raise ValueError('invalid upstream response')
    return payload['bars']


class GoldCollector:
    def __init__(self):
        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        if self.thread is None:
            self.thread = threading.Thread(target=self._loop, name='30na-gold-collector', daemon=True)
            self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread is not None: self.thread.join(timeout=3)

    def _loop(self):
        lock = None
        while not self.stop_event.is_set():
            try:
                if lock is None:
                    directory = data.database_path().parent
                    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
                    fd = os.open(directory / 'collector.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
                    try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        os.close(fd); self.stop_event.wait(5); continue
                    lock = fd
                previous = data.snapshot(limit=1, include_open=False)
                last_success = previous['last_success']
                count = 300 if not previous['candles'] or not last_success or time.time() - last_success > 90 else 3
                data.save_bars(fetch_bars(count))
            except (OSError, ValueError, TypeError, KeyError, OverflowError, sqlite3.Error, httpx.HTTPError):
                LOG.warning('Gold collector could not fetch or store data')
                try: data.set_collector_error()
                except (OSError, ValueError, sqlite3.Error): pass
            self.stop_event.wait(10)
        if lock is not None: os.close(lock)
