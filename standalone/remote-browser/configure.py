"""Local operator setup. Never places passwords or hashes in the repository."""
import argparse
import getpass
import json
import os
from pathlib import Path
import re
import secrets
import tempfile
from server import password_hash


def configure(path,hostname,browser_image,egress_image,cert,key,password=None):
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9.-]{0,252}',hostname):raise ValueError('Invalid hostname')
    hostname=hostname.lower().rstrip('.')
    path=Path(path)
    if path.is_symlink():raise ValueError('Config must not be a symlink')
    existing=json.loads(path.read_text()) if path.exists() else {}
    users=existing.get('users')
    if users is None or password is not None:
        if password is None:password=getpass.getpass('Password for users 1-9 (spaces are significant): ')
        if not 1<=len(password)<=128:raise ValueError('Invalid password length')
        users={}
        for number in range(1,10):
            salt=secrets.token_hex(16);users[str(number)]={'salt':salt,'hash':password_hash(password,salt)}
    config={'installation':existing.get('installation',secrets.token_hex(8)),'hostname':hostname,'origin':'https://'+hostname+':9443','port':9443,
            'users':users,'browser_image':browser_image,'egress_image':egress_image,'cert':str(cert),'key':str(key),'max_sessions':1,'idle_exit_seconds':30}
    path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(dir=path.parent,prefix='.remote-browser-')
    try:
        with os.fdopen(fd,'w') as stream:json.dump(config,stream);stream.flush();os.fsync(stream.fileno());os.fchmod(stream.fileno(),0o600)
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)
    return config


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('config','hostname','browser-image','egress-image','cert','key'):parser.add_argument('--'+name,required=True)
    args=vars(parser.parse_args());args['path']=args.pop('config');configure(**args)
