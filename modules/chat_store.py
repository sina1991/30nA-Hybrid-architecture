"""Persist public and invitation-based private chats for authenticated owners.

The caller must authenticate and pass the principal, never take it from a
request body. This module is a storage layer, not an HTTP authentication layer.
"""
import os
from pathlib import Path
import re
import sqlite3
import time
from uuid import uuid4
from . import accounts

USER_ID = re.compile(r'(?:customer|user-[0-9a-f]{32})\Z')
ROOM_ID = re.compile(r'(?:public|room-[0-9a-f]{32})\Z')
REQUEST_ID = re.compile(r'request-[0-9a-f]{32}\Z')


def _connect():
    directory = Path(os.environ.get('DASHBOARD_MODULE_STATE_DIR', '/var/lib/30na/dashboard'))
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = directory / 'chat.sqlite3'
    if path.is_symlink(): raise OSError('invalid chat database path')
    db = sqlite3.connect(path, timeout=10, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('''CREATE TABLE IF NOT EXISTS rooms (
        id TEXT PRIMARY KEY, member_a TEXT NOT NULL, member_b TEXT NOT NULL,
        created_at INTEGER NOT NULL, UNIQUE(member_a,member_b))''')
    db.execute('''CREATE TABLE IF NOT EXISTS invitations (
        id TEXT PRIMARY KEY, sender TEXT NOT NULL, recipient TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('pending','accepted','rejected')),
        room_id TEXT REFERENCES rooms(id), created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL)''')
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS chat_pending_pair ON invitations(sender,recipient) WHERE status='pending'")
    db.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, room_id TEXT NOT NULL, author TEXT NOT NULL,
        body TEXT NOT NULL, created_at INTEGER NOT NULL)''')
    db.execute('CREATE INDEX IF NOT EXISTS chat_messages_room_id ON messages(room_id,id)')
    return db


def _active_user(owner):
    if not isinstance(owner, str) or not USER_ID.fullmatch(owner): raise ValueError('invalid user')
    user = accounts.get_user(owner)
    if user is None or not user['enabled']: raise PermissionError('account unavailable')
    return user


def _authorize(db, owner, room):
    if not isinstance(room, str) or not ROOM_ID.fullmatch(room): raise ValueError('invalid room')
    if room == 'public': return
    found = db.execute('SELECT 1 FROM rooms WHERE id=? AND (member_a=? OR member_b=?)', (room, owner, owner)).fetchone()
    if found is None: raise PermissionError('room unavailable')


def request_private(owner, recipient):
    _active_user(owner); _active_user(recipient)
    if owner == recipient: raise ValueError('cannot invite yourself')
    a, b = sorted((owner, recipient)); now = int(time.time()); request_id = 'request-' + uuid4().hex
    db = _connect()
    try:
        db.execute('BEGIN IMMEDIATE')
        if db.execute('SELECT 1 FROM rooms WHERE member_a=? AND member_b=?', (a,b)).fetchone(): raise ValueError('private room already exists')
        if db.execute("SELECT 1 FROM invitations WHERE status='pending' AND ((sender=? AND recipient=?) OR (sender=? AND recipient=?))", (owner,recipient,recipient,owner)).fetchone():
            raise ValueError('a request is already pending')
        db.execute('INSERT INTO invitations VALUES(?,?,?,?,?,?,?)', (request_id,owner,recipient,'pending',None,now,now))
        db.commit()
        return {'id':request_id,'sender':owner,'recipient':recipient,'status':'pending','created_at':now}
    finally: db.close()


def respond(owner, request_id, accept):
    _active_user(owner)
    if not isinstance(request_id,str) or not REQUEST_ID.fullmatch(request_id) or type(accept) is not bool: raise ValueError('invalid response')
    db = _connect()
    try:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT * FROM invitations WHERE id=? AND recipient=?', (request_id,owner)).fetchone()
        if row is None: raise LookupError('request not found')
        if row['status'] != 'pending': raise ValueError('request already resolved')
        room_id = None
        if accept:
            _active_user(row['sender'])
            a, b = sorted((row['sender'],owner)); room_id = 'room-' + uuid4().hex
            db.execute('INSERT OR IGNORE INTO rooms VALUES(?,?,?,?)', (room_id,a,b,int(time.time())))
            room_id = db.execute('SELECT id FROM rooms WHERE member_a=? AND member_b=?', (a,b)).fetchone()['id']
        status = 'accepted' if accept else 'rejected'
        db.execute('UPDATE invitations SET status=?,room_id=?,updated_at=? WHERE id=?', (status,room_id,int(time.time()),request_id))
        db.commit()
        return {'id':request_id,'status':status,'room_id':room_id}
    finally: db.close()


def list_rooms(owner):
    _active_user(owner)
    db = _connect()
    try:
        rows = db.execute('SELECT id,member_a,member_b,created_at FROM rooms WHERE member_a=? OR member_b=? ORDER BY created_at DESC', (owner,owner)).fetchall()
        return [{'id':'public','kind':'public'}] + [{'id':row['id'],'kind':'private','peer':row['member_b'] if row['member_a'] == owner else row['member_a'], 'created_at':row['created_at']} for row in rows]
    finally: db.close()


def list_requests(owner):
    _active_user(owner)
    db = _connect()
    try:
        return [dict(row) for row in db.execute('SELECT id,sender,recipient,status,room_id,created_at,updated_at FROM invitations WHERE sender=? OR recipient=? ORDER BY created_at DESC LIMIT 200', (owner,owner))]
    finally: db.close()


def send(owner, room, text):
    _active_user(owner)
    if not isinstance(text,str) or not text.strip() or len(text) > 4000 or len(text.encode('utf-8')) > 16000:
        raise ValueError('message must contain 1 to 4000 characters')
    db = _connect()
    try:
        db.execute('BEGIN IMMEDIATE'); _authorize(db,owner,room)
        now = int(time.time()); cursor = db.execute('INSERT INTO messages(room_id,author,body,created_at) VALUES(?,?,?,?)', (room,owner,text,now))
        db.commit()
        return {'id':cursor.lastrowid,'room_id':room,'author':owner,'body':text,'created_at':now}
    finally: db.close()


def messages(owner, room, limit=50, before=None):
    _active_user(owner)
    if type(limit) is not int or not 1 <= limit <= 200 or (before is not None and (type(before) is not int or before <= 0)):
        raise ValueError('invalid pagination')
    db = _connect()
    try:
        _authorize(db,owner,room)
        query='SELECT id,room_id,author,body,created_at FROM messages WHERE room_id=?'
        args = [room]
        if before is not None: query += ' AND id<?'; args.append(before)
        rows = db.execute(query + ' ORDER BY id DESC LIMIT ?', (*args,limit)).fetchall()
        return [dict(row) for row in reversed(rows)]
    finally: db.close()
