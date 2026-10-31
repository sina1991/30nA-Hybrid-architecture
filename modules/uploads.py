"""Persistent shared files. Callers must supply an authenticated principal."""
import base64
import binascii
from contextlib import contextmanager
import os
from pathlib import Path
import re
import sqlite3
import time
from uuid import uuid4
from . import accounts

MAX_BYTES = 512 * 1024


@contextmanager
def database():
    root = Path(os.environ.get('DASHBOARD_MODULE_STATE_DIR', '/var/lib/30na/dashboard')).resolve()
    checkout = Path(__file__).resolve().parents[1]
    if root == checkout or checkout in root.parents:
        raise OSError('Upload state must be outside the checkout')
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = root / 'uploads.sqlite3'
    if path.is_symlink(): raise OSError('Invalid upload state')
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    os.close(fd)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    try:
        db.execute('''CREATE TABLE IF NOT EXISTS uploads (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, size INTEGER NOT NULL,
            sender TEXT NOT NULL, recipient TEXT, created_at INTEGER NOT NULL, content BLOB NOT NULL)''')
        yield db
        db.commit()
    finally:
        db.close()


def principal(owner):
    user = accounts.get_user(owner)
    if not user or not user['enabled']: raise PermissionError('Account setup required')


def create(owner, name, visibility, recipient, content):
    principal(owner)
    if not isinstance(name, str) or not 1 <= len(name) <= 180 or name in ('.', '..') or re.search(r'[/\\\x00-\x1f\x7f]', name):
        raise ValueError('Invalid filename')
    if visibility not in ('public', 'direct'): raise ValueError('Invalid visibility')
    if visibility == 'direct':
        if not isinstance(recipient, str) or recipient == owner: raise ValueError('Invalid recipient')
        user = accounts.get_user(recipient)
        if not user or not user['enabled']: raise ValueError('Invalid recipient')
    elif recipient is not None: raise ValueError('Public files have no recipient')
    if not isinstance(content, str) or len(content) > 4 * ((MAX_BYTES + 2) // 3): raise OverflowError('File exceeds 512 KiB')
    try: data = base64.b64decode(content, validate=True)
    except (ValueError, binascii.Error): raise ValueError('Invalid file encoding') from None
    if len(data) > MAX_BYTES: raise OverflowError('File exceeds 512 KiB')
    item = dict(id=uuid4().hex, name=name, size=len(data), sender=owner, recipient=recipient, created_at=int(time.time()))
    with database() as db:
        db.execute('INSERT INTO uploads VALUES(?,?,?,?,?,?,?)', (*item.values(), data))
    return item


def list_files(owner):
    principal(owner)
    with database() as db:
        return [dict(row) for row in db.execute('SELECT id,name,size,sender,recipient,created_at FROM uploads WHERE recipient IS NULL OR sender=? OR recipient=? ORDER BY created_at DESC,id', (owner, owner))]


def access(owner, file_id, delete=False):
    principal(owner)
    if not re.fullmatch(r'[0-9a-f]{32}', file_id): raise LookupError('File not found')
    with database() as db:
        row = db.execute('SELECT * FROM uploads WHERE id=?', (file_id,)).fetchone()
        if row is None or (row['sender'] != owner and (delete or row['recipient'] not in (None, owner))):
            raise LookupError('File not found')
        if delete: db.execute('DELETE FROM uploads WHERE id=?', (file_id,))
        return dict(row)
