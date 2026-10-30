"""Persistent, owner-scoped scheduling of explicitly trusted slot modules.

Slot workers run in the Dashboard service, not the isolated Artifact runtime.
A single process owns scheduling. Interrupted executions are paused for review.
"""
import fcntl
import json
import logging
import os
from pathlib import Path
import sqlite3
import threading
import time
from uuid import uuid4

from . import slots

LOG = logging.getLogger(__name__)
MONITORS = frozenset(('clock', 'dashboard-health', 'system-monitor', 'service-monitor',
                      'disk-usage', 'network-monitor', 'process-monitor', 'log-viewer',
                      'docker-monitor', 'alerts', 'gold-chart', 'moving-average', 'rsi', 'macd'))


def configure(owner, slot, payload):
    if not isinstance(payload, dict) or set(payload) != {'enabled', 'kind', 'interval_seconds', 'input'}:
        raise ValueError('invalid worker configuration')
    enabled, kind, interval, data = (payload[key] for key in ('enabled', 'kind', 'interval_seconds', 'input'))
    if type(enabled) is not bool or kind not in ('monitor', 'task') or type(interval) is not int or not 10 <= interval <= 86400:
        raise ValueError('invalid worker configuration')
    if not isinstance(data, dict) or any(str(key).startswith('_') or key in ('owner', 'slot') for key in data):
        raise ValueError('invalid worker input')
    try:
        encoded = json.dumps(data, ensure_ascii=False, allow_nan=False)
    except (ValueError, TypeError, OverflowError):
        raise ValueError('invalid worker input') from None
    if len(encoded.encode('utf-8')) > 8192:
        raise ValueError('worker input is too large')
    db = slots._layout_db(owner)
    try:
        meta_row = db.execute("SELECT value FROM module_state WHERE owner=? AND module='slot-meta' AND slot=?", (owner, slot)).fetchone()
        binding_row = db.execute("SELECT value FROM module_state WHERE owner=? AND module='slot-binding' AND slot=?", (owner, slot)).fetchone()
        if not meta_row or not binding_row: raise LookupError('slot is not active')
        binding = json.loads(binding_row[0])
        if enabled and kind == 'monitor' and binding['module_id'] not in MONITORS:
            raise ValueError('monitor worker requires a monitoring module')
        if enabled and binding['module_id'] == 'empty':
            raise ValueError('select a module before starting a worker')
        # Validate host-monitor ownership before scheduling anything.
        if enabled: slots._authorize_host_monitor(owner, binding['module_id'])
        meta = json.loads(meta_row[0]); old = meta.get('worker') or {}
        worker = {'enabled': enabled, 'kind': kind, 'interval_seconds': interval, 'input': data,
                  'module_id': binding['module_id'], 'binding_revision': binding['revision'],
                  'revision': str(uuid4()), 'next_due': time.time() if enabled else None,
                  'status': 'waiting' if enabled else 'stopped', 'last_started': old.get('last_started'),
                  'last_finished': old.get('last_finished'), 'last_error': None}
        meta['worker'] = worker
        db.execute("UPDATE module_state SET value=? WHERE owner=? AND module='slot-meta' AND slot=?", (json.dumps(meta, ensure_ascii=False, allow_nan=False), owner, slot))
        db.commit()
        return worker
    finally:
        db.close()


class SlotWorkerScheduler:
    def __init__(self):
        self.stopping = threading.Event()
        self.thread = None

    def start(self):
        if self.thread is None:
            self.thread = threading.Thread(target=self._loop, name='30na-slot-workers', daemon=True)
            self.thread.start()

    def stop(self):
        self.stopping.set()
        if self.thread is not None: self.thread.join(timeout=3)

    def _connect(self):
        directory = Path(os.environ.get('DASHBOARD_MODULE_STATE_DIR', '/var/lib/30na/dashboard'))
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        db = sqlite3.connect(directory / 'module-state.sqlite3', timeout=10, isolation_level=None)
        db.execute('CREATE TABLE IF NOT EXISTS module_state (owner TEXT NOT NULL, module TEXT NOT NULL, slot TEXT NOT NULL, value TEXT NOT NULL, PRIMARY KEY(owner,module,slot))')
        return db

    def _recover(self):
        db = self._connect()
        try:
            db.execute('BEGIN IMMEDIATE')
            for owner, slot, value in db.execute("SELECT owner,slot,value FROM module_state WHERE module='slot-meta'").fetchall():
                meta = json.loads(value); worker = meta.get('worker')
                if worker and worker.get('status') == 'running':
                    worker.update(enabled=False, status='interrupted', next_due=None,
                                  last_error='Execution was interrupted; inspect the slot before restarting.')
                    db.execute("UPDATE module_state SET value=? WHERE owner=? AND module='slot-meta' AND slot=?", (json.dumps(meta), owner, slot))
            db.commit()
        finally: db.close()

    def _claim(self):
        db = self._connect()
        try:
            db.execute('BEGIN IMMEDIATE')
            now = time.time()
            rows = db.execute("SELECT owner,slot,value FROM module_state WHERE module='slot-meta' ORDER BY owner,slot").fetchall()
            entries = [(owner, slot, json.loads(value)) for owner, slot, value in rows]
            entries.sort(key=lambda row: ((row[2].get('worker') or {}).get('next_due') or float('inf'), row[0], row[1]))
            for owner, slot, meta in entries:
                worker = meta.get('worker')
                if not worker or not worker.get('enabled') or worker.get('status') == 'running' or (worker.get('next_due') or 0) > now:
                    continue
                binding_row = db.execute("SELECT value FROM module_state WHERE owner=? AND module='slot-binding' AND slot=?", (owner, slot)).fetchone()
                binding = json.loads(binding_row[0]) if binding_row else {}
                if binding.get('revision') != worker.get('binding_revision'):
                    worker.update(enabled=False, status='stopped', next_due=None, last_error='Module binding changed; configure this worker again.')
                    db.execute("UPDATE module_state SET value=? WHERE owner=? AND module='slot-meta' AND slot=?", (json.dumps(meta), owner, slot))
                    continue
                worker.update(status='running', last_started=now, next_due=now + worker['interval_seconds'], last_error=None)
                db.execute("UPDATE module_state SET value=? WHERE owner=? AND module='slot-meta' AND slot=?", (json.dumps(meta), owner, slot))
                db.commit()
                return owner, slot, worker.copy()
            db.commit()
            return None
        finally: db.close()

    def _finish(self, owner, slot, revision, error):
        db = self._connect()
        try:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute("SELECT value FROM module_state WHERE owner=? AND module='slot-meta' AND slot=?", (owner, slot)).fetchone()
            if row:
                meta = json.loads(row[0]); worker = meta.get('worker')
                if worker and worker.get('revision') == revision and worker.get('status') == 'running':
                    finished = time.time()
                    worker.update(status='failed' if error else 'waiting', last_finished=finished,
                                  last_error='Execution failed; check module input and permissions.' if error else None)
                    if error: worker.update(enabled=False, next_due=None)
                    else: worker['next_due'] = finished + worker['interval_seconds']
                    db.execute("UPDATE module_state SET value=? WHERE owner=? AND module='slot-meta' AND slot=?", (json.dumps(meta), owner, slot))
            db.commit()
        finally: db.close()

    def _loop(self):
        lock = None
        while not self.stopping.is_set():
            try:
                if lock is None:
                    directory = Path(os.environ.get('DASHBOARD_MODULE_STATE_DIR', '/var/lib/30na/dashboard'))
                    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
                    fd = os.open(directory / 'slot-workers.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
                    try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        os.close(fd); self.stopping.wait(5); continue
                    lock = fd
                    self._recover()
                job = self._claim()
                if job is None:
                    self.stopping.wait(1); continue
                owner, slot, worker = job
                failed = False
                try:
                    slots.execute(owner, slot, worker['input'], expected_module=worker['module_id'], expected_revision=worker['binding_revision'])
                except Exception:
                    failed = True
                    LOG.warning('Slot worker failed; owner and inputs omitted')
                self._finish(owner, slot, worker['revision'], failed)
            except (OSError, sqlite3.Error, ValueError, KeyError, TypeError):
                LOG.exception('Slot worker scheduler error')
                self.stopping.wait(5)
        if lock is not None: os.close(lock)
