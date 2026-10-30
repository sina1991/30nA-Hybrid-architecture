"""Local account and session storage. Callers must enforce administrator authorization.

This storage layer does not provision downstream service credentials and is not
an authentication boundary until explicitly wired into the Dashboard API.
"""
import hashlib
import hmac
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time
from uuid import uuid4

USERNAME = re.compile(r'[a-z0-9][a-z0-9_.-]{2,31}\Z')
SESSION_SECONDS = 12 * 60 * 60


def _connect():
    directory = Path(os.environ.get('DASHBOARD_MODULE_STATE_DIR', '/var/lib/30na/dashboard'))
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = directory / 'accounts.sqlite3'
    if path.is_symlink(): raise OSError('invalid account database path')
    db = sqlite3.connect(path, timeout=10, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE, role TEXT NOT NULL CHECK(role IN ('admin','user')),
        salt BLOB NOT NULL, password_hash BLOB NOT NULL, enabled INTEGER NOT NULL CHECK(enabled IN (0,1)),
        created_at INTEGER NOT NULL)''')
    db.execute('''CREATE TABLE IF NOT EXISTS sessions (
        token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        expires_at INTEGER NOT NULL, created_at INTEGER NOT NULL)''')
    return db


def _username(value):
    if not isinstance(value, str): raise ValueError('invalid username')
    value = value.strip().lower()
    if not USERNAME.fullmatch(value): raise ValueError('invalid username')
    return value


def _password(value):
    if not isinstance(value, str): raise ValueError('invalid password')
    encoded = value.encode('utf-8')
    if not 12 <= len(encoded) <= 256: raise ValueError('password must contain 12 to 256 UTF-8 bytes')
    return encoded


def _hash(password, salt):
    return hashlib.scrypt(password, salt=salt, n=16384, r=8, p=1, dklen=32)


def _user(row):
    return {'id':row['id'], 'username':row['username'], 'role':row['role'], 'enabled':bool(row['enabled']), 'created_at':row['created_at']}


def bootstrap_admin(username, password):
    """Bootstrap customer owner once; caller must first authenticate legacy admin."""
    username, password = _username(username), _password(password)
    salt = secrets.token_bytes(16); digest = _hash(password, salt)
    db = _connect()
    try:
        db.execute('BEGIN IMMEDIATE')
        if db.execute('SELECT 1 FROM users LIMIT 1').fetchone(): raise ValueError('accounts already initialized')
        now = int(time.time())
        db.execute('INSERT INTO users VALUES(?,?,?,?,?,?,?)', ('customer', username, 'admin', salt, digest, 1, now))
        db.commit()
        return {'id':'customer', 'username':username, 'role':'admin', 'enabled':True, 'created_at':now}
    finally: db.close()


def create_user(username, password, role='user'):
    """Create an account; only an authenticated admin may call this function."""
    username, password = _username(username), _password(password)
    if role not in ('admin', 'user'): raise ValueError('invalid role')
    salt = secrets.token_bytes(16); digest = _hash(password, salt)
    user_id = 'user-' + uuid4().hex
    db = _connect()
    try:
        db.execute('BEGIN IMMEDIATE')
        if not db.execute("SELECT 1 FROM users WHERE role='admin' AND enabled=1").fetchone(): raise ValueError('administrator bootstrap required')
        if db.execute('SELECT 1 FROM users WHERE username=?', (username,)).fetchone(): raise ValueError('username already exists')
        now = int(time.time())
        db.execute('INSERT INTO users VALUES(?,?,?,?,?,?,?)', (user_id, username, role, salt, digest, 1, now))
        db.commit()
        return {'id':user_id, 'username':username, 'role':role, 'enabled':True, 'created_at':now}
    finally: db.close()


def get_user(user_id):
    db = _connect()
    try:
        row = db.execute('SELECT id,username,role,enabled,created_at FROM users WHERE id=?', (user_id,)).fetchone()
        return _user(row) if row else None
    finally: db.close()


def list_users():
    db = _connect()
    try: return [_user(row) for row in db.execute('SELECT id,username,role,enabled,created_at FROM users ORDER BY username')]
    finally: db.close()


def login(username, password):
    """Return a new bearer token; caller must apply network login throttling."""
    try: username = _username(username)
    except ValueError: username = 'invalid-user'
    try: password = _password(password)
    except ValueError: password = b'invalid-password'
    db = _connect()
    try:
        row = db.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
        candidate = _hash(password, row['salt'] if row else b'\x00' * 16)
        valid = hmac.compare_digest(candidate, row['password_hash'] if row else b'\x00' * 32)
        if not row or not valid or not row['enabled']: raise ValueError('invalid credentials')
        token = secrets.token_urlsafe(32); now = int(time.time()); digest = hashlib.sha256(token.encode('ascii')).hexdigest()
        db.execute('BEGIN IMMEDIATE')
        active = db.execute('SELECT enabled FROM users WHERE id=?', (row['id'],)).fetchone()
        if not active or not active['enabled']: raise ValueError('invalid credentials')
        db.execute('DELETE FROM sessions WHERE expires_at<=?', (now,))
        db.execute('INSERT INTO sessions VALUES(?,?,?,?)', (digest, row['id'], now + SESSION_SECONDS, now))
        db.commit()
        return {'token':token, 'expires_at':now + SESSION_SECONDS, 'user':_user(row)}
    finally: db.close()


def authenticate(token):
    if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9_-]{40,128}', token): return None
    digest = hashlib.sha256(token.encode('ascii')).hexdigest()
    db = _connect()
    try:
        row = db.execute('''SELECT u.id,u.username,u.role,u.enabled,u.created_at FROM sessions s
            JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>? AND u.enabled=1''', (digest, int(time.time()))).fetchone()
        return _user(row) if row else None
    finally: db.close()


def logout(token):
    if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9_-]{40,128}', token): return
    db = _connect()
    try: db.execute('DELETE FROM sessions WHERE token_hash=?', (hashlib.sha256(token.encode('ascii')).hexdigest(),))
    finally: db.close()


def set_enabled(user_id, enabled):
    """Disable/re-enable an account; only an authenticated admin may call this."""
    if type(enabled) is not bool: raise ValueError('invalid status')
    db = _connect()
    try:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT id,role,enabled FROM users WHERE id=?', (user_id,)).fetchone()
        if row is None: raise LookupError('user not found')
        if not enabled and row['role'] == 'admin' and row['enabled']:
            if db.execute("SELECT count(*) FROM users WHERE role='admin' AND enabled=1").fetchone()[0] <= 1:
                raise ValueError('cannot disable the last administrator')
        db.execute('UPDATE users SET enabled=? WHERE id=?', (int(enabled), user_id))
        if not enabled: db.execute('DELETE FROM sessions WHERE user_id=?', (user_id,))
        db.commit()
    finally: db.close()
