"""Update client IP and Dashboard upload limits in installer-managed nginx locations."""
from pathlib import Path
import sys
import os
import stat
import tempfile
import re


def configure(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file():raise ValueError('Managed nginx file required')
    text=path.read_text()
    if not text.startswith('# Managed by the 30nA installer. Do not put credentials here.\n'):raise ValueError('Refusing to change unowned nginx configuration')
    header='        proxy_set_header X-30na-Client-IP $remote_addr;'
    marker='        proxy_set_header Authorization $http_authorization;'
    if marker not in text:raise ValueError('Managed proxy locations not found')
    clean=re.sub(r'^\s*proxy_set_header X-30na-Client-IP [^\n]*;\n','',text,flags=re.MULTILINE|re.IGNORECASE)
    updated=clean.replace(marker,marker+'\n'+header)
    def upload_limit(match):
        block=match.group(0)
        if 'proxy_pass http://127.0.0.1:8020;' not in block:return block
        block=re.sub(r'^\s*client_max_body_size [^;]+;\n','',block,flags=re.MULTILINE)
        return block.replace('location / {','location / {\n        client_max_body_size 30m;',1)
    updated=re.sub(r'location / \{[^{}]*\}',upload_limit,updated)
    if updated==text:return
    info=path.stat();fd,name=tempfile.mkstemp(prefix='.30na-client-ip-',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as stream:
            stream.write(updated);stream.flush();os.fsync(stream.fileno())
            os.fchmod(stream.fileno(),stat.S_IMODE(info.st_mode));os.fchown(stream.fileno(),info.st_uid,info.st_gid)
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)


if __name__=='__main__':configure(sys.argv[1])
