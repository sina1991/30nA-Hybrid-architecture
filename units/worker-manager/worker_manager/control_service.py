"""Single-process, owner-scoped control plane with a durable SQLite queue.

Leases prevent duplicate claims; ambiguous remote execution is never retried
under a new identity. This service deliberately does not promise exactly-once.
"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import asdict
import fcntl
import hashlib
import json
from pathlib import Path
import sqlite3
import threading
import time
from uuid import uuid4

from . import ExecutionRequest, Schedule, SQLiteWorkerStore, WorkerDefinition, WorkerManager
from .http_common import identifier
from .service import WorkerConflict, WorkerNotEnabled

TERMINAL = {'succeeded', 'failed', 'cancelled'}


def canonical(value):
    return json.dumps(value, sort_keys=True, allow_nan=False, separators=(',', ':'))


class ControlService:
    def __init__(self, database, gateway_factory, *, max_concurrent=4):
        self.database = str(Path(database).resolve())
        Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        if type(max_concurrent) is not int or max_concurrent < 1:
            raise ValueError('max_concurrent must be positive')
        self._lockfile = open(self.database + '.lock', 'a')
        try:
            fcntl.flock(self._lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self._lockfile.close()
            raise RuntimeError('Only one control-service process may own this database') from None
        self.gateway_factory = gateway_factory
        self.managers, self.gateways = {}, {}
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.thread = None
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self.max_concurrent, self.futures = max_concurrent, set()
        self.lease_owner = uuid4().hex
        SQLiteWorkerStore(self.database)
        with self.transaction() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS control_jobs (
                owner_id TEXT NOT NULL, execution_id TEXT NOT NULL,
                worker_id TEXT NOT NULL, idempotency_key TEXT NOT NULL,
                fingerprint TEXT NOT NULL, request_json TEXT NOT NULL,
                status TEXT NOT NULL, result_json TEXT,
                lease_owner TEXT, lease_until REAL, created_at REAL NOT NULL,
                PRIMARY KEY (owner_id, execution_id), UNIQUE (owner_id, idempotency_key))''')
            db.execute('''CREATE TABLE IF NOT EXISTS control_schedules (
                owner_id TEXT NOT NULL, worker_id TEXT NOT NULL, next_due REAL NOT NULL,
                PRIMARY KEY(owner_id, worker_id))''')
            # A dead process may have left a remote workload active. Keep the ID
            # and fail explicitly; do not invent success or automatically rerun it.
            db.execute("""UPDATE control_jobs SET status='failed', result_json=?
                WHERE status='running'""", (canonical({'error': {'code': 'MANAGER_RESTARTED',
                'message': 'Remote execution may still be active; inspect and cancel by execution ID',
                'retryable': False}}),))

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.database, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def manager(self, owner):
        identifier(owner)
        with self.lock:
            if owner not in self.managers:
                self.managers[owner] = WorkerManager(store=SQLiteWorkerStore(self.database, owner_id=owner))
            return self.managers[owner]

    def gateway(self, owner):
        with self.lock:
            if owner not in self.gateways:
                self.gateways[owner] = self.gateway_factory(owner)
            return self.gateways[owner]

    def register(self, owner, definition, configuration, schedule):
        with self.lock:
            result = self.manager(owner).register(definition, configuration=configuration, schedule=schedule)
            return asdict(result)

    def change(self, owner, worker_id, action, *, configuration=None, schedule=None):
        with self.lock:
            manager = self.manager(owner)
            if action == 'configure':
                result = manager.configure(worker_id, configuration=configuration, schedule=schedule)
            elif action == 'delete':
                manager.remove(worker_id)
                result = None
            else:
                result = getattr(manager, action)(worker_id)
            with self.transaction() as db:
                db.execute('DELETE FROM control_schedules WHERE owner_id=? AND worker_id=?', (owner, worker_id))
            return None if result is None else asdict(result)

    def _insert_job(self, db, owner, record, input_payload, timeout, key, now):
        body = {'definition': asdict(record.definition), 'configuration': dict(record.configuration),
                'input_payload': input_payload, 'timeout_seconds': timeout, 'depth': 0}
        fingerprint = hashlib.sha256(canonical(body).encode()).hexdigest()
        prior = db.execute('SELECT * FROM control_jobs WHERE owner_id=? AND idempotency_key=?', (owner, key)).fetchone()
        if prior:
            if prior['fingerprint'] != fingerprint:
                raise WorkerConflict('Idempotency key reused with a different request')
            return self._job(prior)
        queued = db.execute("SELECT count(*) FROM control_jobs WHERE status IN ('accepted','running')").fetchone()[0]
        if queued >= 1000:
            raise WorkerConflict('Execution queue is full')
        execution_id = str(uuid4())
        body.update(execution_id=execution_id, idempotency_key='manager:' + execution_id)
        db.execute('''INSERT INTO control_jobs
            (owner_id,execution_id,worker_id,idempotency_key,fingerprint,request_json,status,created_at)
            VALUES (?,?,?,?,?,?,'accepted',?)''',
            (owner, execution_id, record.definition.worker_id, key, fingerprint, canonical(body), now))
        return {'execution_id': execution_id, 'worker_id': record.definition.worker_id, 'status': 'accepted', 'result': None}

    def submit(self, owner, worker_id, input_payload, timeout, key):
        canonical(input_payload)
        if not isinstance(key, str) or not 1 <= len(key) <= 256:
            raise ValueError('A bounded idempotency key is required')
        with self.lock:
            record = self.manager(owner).get(worker_id)
            if record.lifecycle != 'enabled':
                raise WorkerNotEnabled('Worker is not enabled')
            with self.transaction() as db:
                return self._insert_job(db, owner, record, input_payload, timeout, key, time.time())

    @staticmethod
    def _job(row):
        return {'execution_id': row['execution_id'], 'worker_id': row['worker_id'],
                'status': row['status'], 'result': json.loads(row['result_json']) if row['result_json'] else None}

    def get(self, owner, execution_id):
        with self.transaction() as db:
            row = db.execute('SELECT * FROM control_jobs WHERE owner_id=? AND execution_id=?', (owner, execution_id)).fetchone()
            if row is None:
                raise KeyError('Execution not found')
            return self._job(row)

    def history(self, owner, limit=100):
        with self.transaction() as db:
            return [self._job(row) for row in db.execute('SELECT * FROM control_jobs WHERE owner_id=? ORDER BY created_at DESC LIMIT ?', (owner, limit))]

    def cancel(self, owner, execution_id):
        with self.transaction() as db:
            row = db.execute('SELECT * FROM control_jobs WHERE owner_id=? AND execution_id=?', (owner, execution_id)).fetchone()
            if row is None:
                raise KeyError('Execution not found')
            if row['status'] == 'accepted':
                db.execute("UPDATE control_jobs SET status='cancelled' WHERE owner_id=? AND execution_id=?", (owner, execution_id))
                return True
            if row['status'] == 'cancelled':
                return True
            # A restart/transport failure can leave remote work alive. Permit
            # cancellation of retained IDs even after the manager marked failure.
            if row['status'] == 'succeeded':
                return False
        return bool(self.gateway(owner).cancel(execution_id))

    def _schedule_due(self, now):
        with self.lock, self.transaction() as db:
            records = db.execute("SELECT * FROM workers WHERE owner_id != '__legacy__' AND lifecycle='enabled' AND schedule_kind='interval'").fetchall()
            for row in records:
                owner, worker_id, interval = row['owner_id'], row['worker_id'], row['interval_seconds']
                db.execute('INSERT OR IGNORE INTO control_schedules VALUES (?,?,?)', (owner, worker_id, now + interval))
                due = db.execute('SELECT next_due FROM control_schedules WHERE owner_id=? AND worker_id=?', (owner, worker_id)).fetchone()[0]
                if due > now:
                    continue
                # Skip missed periods; never burst replay jobs after downtime.
                record = SQLiteWorkerStore._decode(row)
                self._insert_job(db, owner, record, {}, 30.0, 'schedule:' + worker_id + ':' + str(due), now)
                db.execute('UPDATE control_schedules SET next_due=? WHERE owner_id=? AND worker_id=?', (now + interval, owner, worker_id))

    def claim(self, now=None):
        now = time.time() if now is None else now
        with self.transaction() as db:
            # Do not re-execute expired claims: the remote side may be alive.
            db.execute("""UPDATE control_jobs SET status='failed', result_json=?
                WHERE status='running' AND lease_until < ?""", (canonical({'error': {'code': 'LEASE_EXPIRED',
                'message': 'Remote outcome unknown; inspect retained execution ID', 'retryable': False}}), now))
            row = db.execute("SELECT * FROM control_jobs WHERE status='accepted' ORDER BY created_at LIMIT 1").fetchone()
            if row is None:
                return None
            timeout = json.loads(row['request_json'])['timeout_seconds']
            db.execute("""UPDATE control_jobs SET status='running',lease_owner=?,lease_until=?
                WHERE owner_id=? AND execution_id=? AND status='accepted'""",
                (self.lease_owner, now + timeout + 60, row['owner_id'], row['execution_id']))
            return dict(row)

    def execute(self, job):
        owner, execution_id = job['owner_id'], job['execution_id']
        body = json.loads(job['request_json'])
        request = ExecutionRequest(definition=WorkerDefinition(**body.pop('definition')), **body)
        try:
            result = self.gateway(owner).submit(request)
            if not isinstance(result, dict):
                result = asdict(result)
            # A prior in-flight idempotent response is a snapshot, never success.
            deadline = time.monotonic() + request.timeout_seconds + 15
            while result.get('status') in {'accepted', 'running'} and time.monotonic() < deadline:
                time.sleep(0.1)
                result = self.gateway(owner).get(execution_id)
            if result.get('execution_id') != execution_id or result.get('status') not in TERMINAL:
                raise ValueError('Invalid or nonterminal Runtime result')
            status = result['status']
            encoded = canonical(result)
        except Exception:
            status = 'failed'
            result = {'error': {'code': 'RUNTIME_OUTCOME_UNKNOWN',
                'message': 'Runtime request failed; inspect retained execution ID before retry', 'retryable': False}}
            encoded = canonical(result)
        with self.transaction() as db:
            db.execute('''UPDATE control_jobs SET status=?,result_json=?
                WHERE owner_id=? AND execution_id=? AND status='running' AND lease_owner=?''',
                (status, encoded, owner, execution_id, self.lease_owner))

    def tick(self, now=None):
        now = time.time() if now is None else now
        self._schedule_due(now)
        self.futures = {future for future in self.futures if not future.done()}
        while len(self.futures) < self.max_concurrent:
            job = self.claim(now)
            if job is None:
                break
            self.futures.add(self.executor.submit(self.execute, job))

    def start(self):
        if self.thread is not None:
            return
        def run():
            while not self.stop.is_set():
                try:
                    self.tick()
                    self.last_error = None
                except Exception:
                    self.last_error = 'Scheduler unavailable'
                self.stop.wait(0.25)
        self.last_error = None
        self.thread = threading.Thread(target=run, name='worker-scheduler', daemon=True)
        self.thread.start()

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join()
        self.executor.shutdown(wait=True)
        self._lockfile.close()
