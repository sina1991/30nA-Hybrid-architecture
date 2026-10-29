#!/usr/bin/env python3
"""Install the pinned official Linux amd64 release after checksum verification."""
import argparse
import hashlib
import io
from pathlib import Path
import tarfile
import urllib.request

VERSION='8.30.0'
parser=argparse.ArgumentParser()
parser.add_argument('--output',required=True)
args=parser.parse_args()
base=f'https://github.com/gitleaks/gitleaks/releases/download/v{VERSION}/'
name=f'gitleaks_{VERSION}_linux_x64.tar.gz'
with urllib.request.urlopen(base+f'gitleaks_{VERSION}_checksums.txt',timeout=30) as response:
    checks=response.read().decode('ascii')
expected=next(line.split()[0] for line in checks.splitlines() if line.split()[-1]==name)
with urllib.request.urlopen(base+name,timeout=30) as response:
    data=response.read(32*1024*1024+1)
if len(data)>32*1024*1024 or hashlib.sha256(data).hexdigest()!=expected:
    raise SystemExit('Official Gitleaks release checksum verification failed')
with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as archive:
    member=archive.getmember('gitleaks')
    if not member.isfile() or member.size>64*1024*1024:
        raise SystemExit('Invalid Gitleaks archive member')
    binary=archive.extractfile(member).read()
output=Path(args.output)
output.parent.mkdir(parents=True,exist_ok=True)
with output.open('xb') as stream:stream.write(binary)
output.chmod(0o700)
print('Official Gitleaks '+VERSION+' checksum verified')
