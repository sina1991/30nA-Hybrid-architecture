#!/usr/bin/env python3
"""Check repository Markdown links, local anchors and handbook source coverage.

No network requests and no imports of application modules are performed.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parents[2]


def repository_files():
    output=subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT)
    return sorted({name.decode() for name in output.split(b'\0') if name})


def prose(text):
    result=[];fence=None
    for line in text.splitlines():
        match=re.match(r'^\s*(`{3,}|~{3,})',line)
        if match:
            marker=match.group(1)[0]
            if fence is None:fence=marker
            elif fence==marker:fence=None
            result.append('');continue
        result.append('' if fence else line)
    return '\n'.join(result),fence


def anchors(path):
    text,_=prose(path.read_text())
    found=set(re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)',text))
    counts={}
    for heading in re.findall(r'^#{1,6}\s+(.+?)\s*#*$',text,re.M):
        title=re.sub(r'<[^>]*>','',heading).strip().lower().replace('`','')
        title=re.sub(r'[^\w\-\s]','',title)
        slug=re.sub(r'\s','-',title)
        count=counts.get(slug,0);counts[slug]=count+1
        found.add(slug+('' if count==0 else '-'+str(count)))
    return found


def main():
    names=repository_files()
    failures=[];checked=0;anchor_cache={}
    for name in names:
        path=ROOT/name
        if path.suffix.lower()!='.md' or not path.is_file():continue
        text,fence=prose(path.read_text())
        if fence:failures.append(name+': unclosed code fence')
        targets=re.findall(r'!?\[[^\]\n]*\]\(([^)\n]+)\)',text)
        targets += re.findall(r'^\s*\[[^\]]+\]:\s*(\S+)',text,re.M)
        for raw in targets:
            target=raw.strip().strip('<>')
            if ' "' in target:target=target.split(' "',1)[0]
            parts=urlsplit(target)
            if parts.scheme or parts.netloc:continue
            checked+=1
            relative=unquote(parts.path)
            destination=(path.parent/relative).resolve() if relative else path
            if not destination.is_relative_to(ROOT):
                failures.append(name+': link escapes repository: '+target);continue
            if not destination.exists():
                failures.append(name+': missing target: '+target);continue
            fragment=unquote(parts.fragment)
            if fragment and destination.suffix.lower()=='.md':
                if destination not in anchor_cache:anchor_cache[destination]=anchors(destination)
                if fragment not in anchor_cache[destination]:failures.append(name+': missing anchor: '+target)
            elif fragment and re.fullmatch(r'L\d+(?:-L\d+)?',fragment) and destination.is_file():
                end=int(fragment.rsplit('L',1)[-1])
                if end>len(destination.read_text().splitlines()):failures.append(name+': source line out of range: '+target)
    manifest=json.loads((ROOT/'docs/manual/manifest.json').read_text())
    for chapter in manifest['chapters']:
        path=ROOT/'docs/manual'/chapter
        if not path.is_file() or not path.read_text().startswith('# '):failures.append('Missing chapter/title: '+chapter)
    inventory=json.loads((ROOT/'docs/manual/source-inventory.json').read_text())
    covered={entry['path'] for entry in inventory['files']}
    expected={name for name in names if not name.startswith('docs/') and (ROOT/name).is_file()}
    for missing in sorted(expected-covered):failures.append('Not covered by source inventory: '+missing)
    pdf_manifest=ROOT/'docs/manual/pdf-manifest.json'
    if pdf_manifest.exists():
        pdf=json.loads(pdf_manifest.read_text())
        for filename,key in [('PROJECT_MANUAL.html','html_sha256'),('PROJECT_MANUAL.pdf','pdf_sha256')]:
            path=ROOT/'docs/manual'/filename
            if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=pdf[key]:
                failures.append('PDF/source checksum mismatch: '+filename)
    else:failures.append('Missing PDF checksum manifest')
    if failures:
        print('\n'.join(failures));return 1
    print(f"Documentation checked: {sum(name.endswith('.md') for name in names)} Markdown files, {checked} local links, {len(manifest['chapters'])} chapters, {len(covered)} technical files covered")
    return 0

if __name__=='__main__':sys.exit(main())
