#!/usr/bin/env python3
"""Render installer-owned configuration; never print generated credentials."""
import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import pwd
import re
import secrets
import tempfile

OWNER = 'customer'


def validate(domain, image, sandbox_uid):
    try:ipaddress.ip_address(domain)
    except ValueError:pass
    else:raise ValueError('A domain is required')
    if len(domain)>253 or '.' not in domain or any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',x) for x in domain.split('.')):
        raise ValueError('Invalid domain')
    if not re.fullmatch(r'sha256:[0-9a-f]{64}',image) or type(sandbox_uid) is not int or sandbox_uid<1:
        raise ValueError('Immutable image and non-root sandbox UID required')


def atomic(path, content, *, mode=0o640, uid=0, gid=0):
    """Replace one owned file atomically with final permissions before rename."""
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:
            os.fchmod(f.fileno(),mode)
            os.fchown(f.fileno(),uid,gid)
            f.write(content)
            f.flush();os.fsync(f.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)


def nginx_config(domain, public_tls=False):
    if not re.fullmatch(r'[a-z0-9.-]+',domain):raise ValueError('Invalid domain')
    locations='''
    location ^~ /.well-known/acme-challenge/ { root /var/lib/30na/acme; }
    location / { return 308 https://$host$request_uri; }
'''
    parts=['# Managed by the 30nA installer. Do not put credentials here.\n',
        'server {\n    listen 80;\n    listen [::]:80;\n    server_name '+domain+';\n'+locations+'}\n']
    proxy='''
    client_max_body_size 30m;
    access_log off;
    error_log /var/log/nginx/30na-error.log crit;
    location / {
        proxy_pass http://127.0.0.1:PORT;
        proxy_set_header Host $host;
        proxy_set_header Authorization $http_authorization;
        proxy_set_header X-30na-Client-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_connect_timeout 10s;
        proxy_read_timeout 360s;
        proxy_send_timeout 360s;
    }
'''
    for tls_port,upstream in [(18443,8099),(18444,8101),(18445,8102),(18446,8020)]:
        parts += [f'''server {{
    listen 127.0.0.1:{tls_port} ssl;
    server_name localhost;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_certificate /etc/30na/ca/internal.crt;
    ssl_certificate_key /etc/30na/ca/internal.key;
''',proxy.replace('PORT',str(upstream)),'}\n']
    if public_tls:
        parts += ['''server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name '''+domain+''';
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_certificate /etc/letsencrypt/live/30na-dashboard/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/30na-dashboard/privkey.pem;
    add_header X-Content-Type-Options nosniff always;
    add_header Referrer-Policy same-origin always;
''',proxy.replace('PORT','8020'),'}\n']
    return ''.join(parts)


def environments(image, sandbox_uid):
    docker=f'DOCKER_HOST=unix:///run/user/{sandbox_uid}/docker.sock\nXDG_RUNTIME_DIR=/run/user/{sandbox_uid}\n'
    ca='SSL_CERT_FILE=/etc/30na/ca/trust.pem\n'
    return {
        'code-manager': 'CODE_MANAGER_BLOB_ROOT=/var/lib/30na/code\nDATA_MANAGER_DB=/var/lib/30na/data/data.sqlite3\nCODE_MANAGER_CREDENTIAL_FILE=/etc/30na/code-incoming.json\nCODE_MANAGER_BUILD_SANDBOX_IMAGE='+image+'\n'+docker+ca,
        'worker-runtime': 'WORKER_RUNTIME_STATE_ROOT=/var/lib/30na/runtime\nWORKER_RUNTIME_CREDENTIAL_FILE=/etc/30na/runtime-incoming.json\nWORKER_RUNTIME_CODE_CREDENTIALS=/etc/30na/runtime-code.json\nWORKER_RUNTIME_SANDBOX_IMAGE='+image+'\n'+docker+ca,
        'worker-manager': 'WORKER_MANAGER_DB=/var/lib/30na/manager/manager.sqlite3\nWORKER_MANAGER_CREDENTIAL_FILE=/etc/30na/manager-incoming.json\nWORKER_MANAGER_RUNTIME_CREDENTIALS=/etc/30na/manager-runtime.json\n'+ca,
        'dashboard': 'DASHBOARD_CREDENTIAL_FILE=/etc/30na/dashboard-incoming.json\nDASHBOARD_WORKER_MANAGER_URL=https://localhost:18444\nDASHBOARD_CODE_MANAGER_URL=https://localhost:18443\n'+ca,
    }


def provision(config, nginx_path, *, domain, image, sandbox_uid, service_gid, sandbox_gid, owner_uid=0, public_tls=False):
    validate(domain,image,sandbox_uid)
    config=Path(config)
    state=config/'installer-secrets.json'
    if state.exists():
        if state.is_symlink() or state.stat().st_mode & 0o077:raise ValueError('Installer secret store is not private')
        tokens=json.loads(state.read_text())
        if set(tokens)!= {'customer','manager_runtime','runtime_code'} or any(not re.fullmatch(r'[A-Za-z0-9_-]{64}',v) for v in tokens.values()):
            raise ValueError('Invalid existing installer secrets')
    else:
        # Refuse partial credential state without the source of truth.
        if any(config.glob('*incoming.json')) or (config/'customer-token').exists():
            raise ValueError('Partial credential state; operator recovery required')
        tokens={name:secrets.token_urlsafe(48) for name in ('customer','manager_runtime','runtime_code')}
        atomic(state,json.dumps(tokens)+'\n',mode=0o600,uid=owner_uid,gid=0 if owner_uid==0 else service_gid)
    digest=lambda value:hashlib.sha256(value.encode('ascii')).hexdigest()
    files={
        'code-incoming.json':({digest(tokens['customer']):OWNER,digest(tokens['runtime_code']):OWNER},sandbox_gid),
        'manager-incoming.json':({digest(tokens['customer']):OWNER},service_gid),
        'dashboard-incoming.json':({digest(tokens['customer']):OWNER},service_gid),
        'runtime-incoming.json':({digest(tokens['manager_runtime']):OWNER},sandbox_gid),
        'manager-runtime.json':({OWNER:{'url':'https://localhost:18445','token':tokens['manager_runtime'],'ca_file':'/etc/30na/ca/internal.crt'}},service_gid),
        'runtime-code.json':({OWNER:{'url':'https://localhost:18443','token':tokens['runtime_code']}},sandbox_gid),
    }
    for name,(value,gid) in files.items():atomic(config/name,json.dumps(value)+'\n',uid=owner_uid,gid=gid)
    atomic(config/'customer-token',tokens['customer']+'\n',mode=0o600,uid=owner_uid,gid=service_gid)
    for service,content in environments(image,sandbox_uid).items():
        gid=sandbox_gid if service in ('code-manager','worker-runtime') else service_gid
        atomic(config/(service+'.env'),content,uid=owner_uid,gid=gid)
    atomic(nginx_path,nginx_config(domain,public_tls),mode=0o644,uid=owner_uid,gid=service_gid)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--domain',required=True)
    parser.add_argument('--image',required=True)
    parser.add_argument('--sandbox-uid',required=True,type=int)
    parser.add_argument('--public-tls',action='store_true')
    args=parser.parse_args()
    if os.geteuid()!=0:parser.error('Only root can provision an installation')
    service=pwd.getpwnam('30na');sandbox=pwd.getpwnam('30na-sandbox')
    for name,account in [('code',sandbox),('data',sandbox),('runtime',sandbox),('manager',service),('dashboard',service)]:
        target=Path('/var/lib/30na')/name
        target.mkdir(parents=True,exist_ok=True)
        os.chown(target,account.pw_uid,account.pw_gid);os.chmod(target,0o700)
    provision('/etc/30na','/etc/nginx/sites-available/30na',domain=args.domain,image=args.image,
              sandbox_uid=args.sandbox_uid,service_gid=service.pw_gid,sandbox_gid=sandbox.pw_gid,public_tls=args.public_tls)

if __name__=='__main__':main()
