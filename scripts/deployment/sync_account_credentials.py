#!/usr/bin/env python3
"""Provision separate internal credentials for enabled Dashboard accounts.

Run as root on an installer-owned host after account creation or status changes.
Never prints credentials. A subsequent run repairs an interrupted update.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import secrets
import sqlite3
import stat
import tempfile

USER_ID = re.compile(r'user-[0-9a-f]{32}\Z')
TOKEN = re.compile(r'[A-Za-z0-9_-]{64}\Z')


def _read(path):
    if path.is_symlink() or not path.is_file(): raise ValueError('invalid credential configuration')
    info = path.stat()
    if info.st_uid != os.geteuid() or info.st_mode & 0o022: raise ValueError('credential configuration ownership is unsafe')
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict): raise ValueError('invalid credential configuration')
    return data


def _atomic(path, data, uid, gid, mode):
    if path.is_symlink(): raise ValueError('invalid credential path')
    if path.exists():
        info = path.stat()
        if info.st_uid == uid and info.st_gid == gid and info.st_mode & 0o777 == mode:
            try:
                if json.loads(path.read_text(encoding='utf-8')) == data: return
            except (OSError, ValueError): pass
    fd, temporary = tempfile.mkstemp(prefix='.accounts-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            os.fchmod(stream.fileno(), mode); os.fchown(stream.fileno(), uid, gid)
            json.dump(data, stream, sort_keys=True, separators=(',', ':'))
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def sync(config, state, dashboard_uid, dashboard_gid):
    """Synchronize a bounded owner list, preserving all unrelated credentials."""
    config, state = Path(config), Path(state)
    if config.is_symlink() or state.is_symlink() or not config.is_dir() or not state.is_dir(): raise ValueError('invalid account directories')
    output_path = state / 'account-upstream.json'
    if output_path.is_symlink(): raise ValueError('invalid account credential output')
    stat = state.stat()
    if stat.st_uid != dashboard_uid or stat.st_mode & 0o077: raise ValueError('dashboard state directory must be private')
    db_path = state / 'accounts.sqlite3'
    if db_path.is_symlink(): raise ValueError('invalid account database')
    if not db_path.exists(): return 0
    if not db_path.is_file(): raise ValueError('invalid account database')
    db_info = db_path.stat()
    if db_info.st_uid != dashboard_uid or db_info.st_mode & 0o077: raise ValueError('account database must be private')
    db = sqlite3.connect('file:' + str(db_path) + '?mode=ro', uri=True, timeout=10)
    try: users = db.execute('SELECT id,enabled FROM users LIMIT 1001').fetchall()
    finally: db.close()
    if len(users) > 1000 or any((owner != 'customer' and (not isinstance(owner, str) or not USER_ID.fullmatch(owner))) or enabled not in (0,1) for owner,enabled in users):
        raise ValueError('invalid account records')
    enabled = {owner for owner,active in users if active}
    installer_secrets = config / 'installer-secrets.json'
    if installer_secrets.is_symlink() or installer_secrets.stat().st_mode & 0o077: raise ValueError('installer secrets must be private')
    base = _read(installer_secrets)
    if set(base) != {'customer','manager_runtime','runtime_code'} or any(not isinstance(value,str) or not TOKEN.fullmatch(value) for value in base.values()):
        raise ValueError('invalid installer credentials')
    source = config / 'multiuser-secrets.json'
    if source.exists() and (source.is_symlink() or source.stat().st_mode & 0o077): raise ValueError('account secrets must be private')
    records = _read(source) if source.exists() else {}
    for owner, item in records.items():
        if not USER_ID.fullmatch(owner) or not isinstance(item,dict) or set(item) != {'user','runtime','code'} or any(not isinstance(value,str) or not TOKEN.fullmatch(value) for value in item.values()):
            raise ValueError('invalid account credential records')
    new_owners = enabled - {'customer'} - set(records)
    names = ('manager-incoming.json','runtime-incoming.json','code-incoming.json','manager-runtime.json','runtime-code.json')
    paths = {name:config / name for name in names}
    values = {name:_read(path) for name,path in paths.items()}
    for owner in new_owners:
        if (owner in values['manager-runtime.json'] or owner in values['runtime-code.json'] or
                any(owner in values[name].values() for name in ('manager-incoming.json','runtime-incoming.json','code-incoming.json'))):
            raise ValueError('existing unowned account credentials')
        records[owner] = {key:secrets.token_urlsafe(48) for key in ('user','runtime','code')}
    # The installer's customer identity is also revocable. Preserve its exact
    # routing before removal so enabling the account can restore it safely.
    customer_state = dict(users).get('customer')
    saved_path = config / 'customer-service-bindings.json'
    if saved_path.is_symlink(): raise ValueError('invalid customer bindings')
    saved = _read(saved_path) if saved_path.exists() else None
    if saved is not None and (saved_path.stat().st_mode & 0o077 or set(saved) != {'manager-runtime.json','runtime-code.json'}):
        raise ValueError('invalid customer bindings')
    if customer_state == 0 and saved is None:
        saved = {name:values[name].get('customer') for name in ('manager-runtime.json','runtime-code.json')}
        if any(not isinstance(item, dict) for item in saved.values()): raise ValueError('customer bindings unavailable')
        if saved['manager-runtime.json'].get('token') != base['manager_runtime'] or saved['runtime-code.json'].get('token') != base['runtime_code']:
            raise ValueError('customer binding conflict')
        _atomic(saved_path, saved, os.geteuid(), os.getegid(), 0o600)
    if customer_state is not None:
        for name, token in (('manager-incoming.json',base['customer']),('runtime-incoming.json',base['manager_runtime']),('code-incoming.json',base['customer']),('code-incoming.json',base['runtime_code'])):
            key = hashlib.sha256(token.encode('ascii')).hexdigest()
            if values[name].get(key) not in (None,'customer'): raise ValueError('customer credential conflict')
            if customer_state: values[name][key] = 'customer'
            else: values[name].pop(key,None)
        if customer_state == 0:
            for name in ('manager-runtime.json','runtime-code.json'): values[name].pop('customer',None)
        elif saved is not None:
            for name in ('manager-runtime.json','runtime-code.json'):
                if values[name].get('customer') not in (None,saved[name]): raise ValueError('customer binding conflict')
                values[name]['customer'] = saved[name]
    _atomic(source, records, os.geteuid(), os.getegid(), 0o600)
    digest = lambda value: hashlib.sha256(value.encode('ascii')).hexdigest()
    for owner, tokens in records.items():
        for name, token in (('manager-incoming.json',tokens['user']),('runtime-incoming.json',tokens['runtime']),('code-incoming.json',tokens['user']),('code-incoming.json',tokens['code'])):
            key = digest(token)
            previous = values[name].get(key)
            if previous not in (None,owner): raise ValueError('credential identity conflict')
            if owner in enabled: values[name][key] = owner
            else: values[name].pop(key,None)
        if owner in enabled:
            values['manager-runtime.json'][owner] = {'url':'https://localhost:18445','token':tokens['runtime'],'ca_file':'/etc/30na/ca/internal.crt'}
            values['runtime-code.json'][owner] = {'url':'https://localhost:18443','token':tokens['code']}
        else:
            values['manager-runtime.json'].pop(owner,None); values['runtime-code.json'].pop(owner,None)
    for name,path in paths.items():
        info=path.stat(); _atomic(path,values[name],info.st_uid,info.st_gid,info.st_mode & 0o777)
    accessible = {owner:records[owner]['user'] for owner in enabled if owner != 'customer'}
    if 'customer' in enabled: accessible['customer'] = base['customer']
    _atomic(output_path, accessible, dashboard_uid, dashboard_gid, 0o600)
    return len(enabled)


def main():
    if os.geteuid() != 0: raise SystemExit('Run as root on the installed server.')
    if not Path('/etc/30na/installed-release').is_file():
        print('Managed installation not initialized; synchronization skipped.')
        return
    account = pwd.getpwnam('30na')
    def open_lock(path):
        fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        handle = os.fdopen(fd, 'r+')
        info = os.fstat(handle.fileno())
        if info.st_uid != 0 or not stat.S_ISREG(info.st_mode):
            handle.close(); raise ValueError('invalid synchronization lock')
        return handle
    with open_lock('/run/lock/30na-install.lock') as install_lock:
        try: fcntl.flock(install_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('Installer is active; account synchronization deferred.')
            return
        with open_lock('/run/lock/30na-account-sync.lock') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            count=sync('/etc/30na','/var/lib/30na/dashboard',account.pw_uid,account.pw_gid)
    print(f'Account credentials synchronized: {count} enabled accounts.')


if __name__ == '__main__': main()
