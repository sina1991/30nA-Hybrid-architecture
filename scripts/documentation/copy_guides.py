#!/usr/bin/env python3
"""Collect documentation copies; preserve paths and repair outgoing Markdown links."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'docs/guides'


def source_files():
    names=subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT).split(b'\0')
    return sorted({name.decode() for name in names if name and not name.decode().startswith('docs/guides/')
                   and (name.decode().startswith('docs/') or Path(name.decode()).suffix.lower() in ('.md','.rst','.adoc','.pdf')
                        or Path(name.decode()).name in ('LICENSE','LICENSE.txt'))})


def markdown_copy(text,source,destination,selected):
    def target(raw):
        value=raw.strip();angle=value.startswith('<')
        if angle:value=value[1:value.index('>')]
        elif ' "' in value:value=value.split(' "',1)[0]
        parts=urlsplit(value)
        if parts.scheme or parts.netloc or not parts.path:return raw
        path=(source.parent/unquote(parts.path)).resolve()
        if not path.is_relative_to(ROOT):return raw
        relative=path.relative_to(ROOT).as_posix()
        actual=DEST/'files'/relative if relative in selected else path
        updated=os.path.relpath(actual,destination.parent).replace(os.sep,'/')
        if parts.query:updated+='?'+parts.query
        if parts.fragment:updated+='#'+parts.fragment
        return raw.replace(value,updated,1)
    lines=[];fence=None
    for line in text.splitlines(keepends=True):
        match=re.match(r'^\s*(`{3,}|~{3,})',line)
        if match:
            marker=match[1][0]
            if fence is None:fence=marker
            elif fence==marker:fence=None
            lines.append(line);continue
        if fence is None:
            line=re.sub(r'(!?\[[^\]\n]*\]\()([^\n)]+)(\))',lambda m:m[1]+target(m[2])+m[3],line)
            line=re.sub(r'^(\s*\[[^\]]+\]:\s*)(\S+)',lambda m:m[1]+target(m[2]),line)
        lines.append(line)
    return ''.join(lines)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    names=source_files();selected=set(names);outputs={};records=[]
    for name in names:
        source=ROOT/name
        if source.is_symlink() or not source.is_file():continue
        data=source.read_bytes();destination=DEST/'files'/name
        copied=markdown_copy(data.decode('utf8'),source,destination,selected).encode('utf8') if source.suffix.lower()=='.md' else data
        outputs[destination]=copied
        records.append({'source':name,'copy':'files/'+name,'source_sha256':hashlib.sha256(data).hexdigest(),'copy_sha256':hashlib.sha256(copied).hexdigest()})
    outputs[DEST/'manifest.json']=(json.dumps({'format':1,'files':records},ensure_ascii=False,indent=2)+'\n').encode()
    pages=['# همهٔ راهنماها و مستندات','',
           'این پوشه یک کپی قابل مرور از مستندات پروژه است. ساختار مسیرها در files حفظ شده؛ لینک‌های Markdown به کپی‌ها یا کد اصلی تنظیم شده‌اند. محتوای آموزشی منبع اصلی همچنان در مسیر اولیه نگهداری می‌شود؛ برای اصلاح، منبع اصلی را تغییر دهید و کپی‌ها را دوباره بسازید.','',
           'شروع سریع: [راهنمای کاربر Dashboard](files/docs/dashboard/USER_GUIDE.md) · [Demo Trading](files/docs/dashboard/demo-trading.md) · [Signal Scripts](files/docs/dashboard/signal-scripts.md) · [دفترچهٔ کم‌توکن Agent](files/docs/DASHBOARD_AGENT.md) · [دفترچهٔ PDF](files/docs/manual/PROJECT_MANUAL.pdf).','',
           'بازتولید: `python scripts/documentation/copy_guides.py` از ریشهٔ مخزن. ابتدا منابع تولیدشدهٔ دفترچه را با build_manual.py و render_pdf.cjs به‌روز کنید. `--check` همسانی کپی‌ها و SHA-256ها را بدون تغییر فایل کنترل می‌کند. کد، credential، env و DB عملیاتی به این مجموعه اضافه نمی‌شوند.','',
           f'تعداد فایل‌های کپی‌شده: **{len(records)}**. JSON و تصاویر مستندات نیز همراه آن‌ها هستند.','',
           '| منبع اصلی | کپی |','|---|---|']
    for item in records:
        original=os.path.relpath(ROOT/item['source'],DEST).replace(os.sep,'/')
        pages.append(f"| [{item['source']}]({original}) | [Open]({item['copy']}) |")
    outputs[DEST/'README.md']=('\n'.join(pages)+'\n').encode()
    stale=[]
    for path,data in outputs.items():
        if args.check:
            if not path.is_file() or path.read_bytes()!=data:stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    if args.check:
        extras=set((DEST/'files').rglob('*'))-set(outputs) if (DEST/'files').exists() else set()
        stale.extend(str(path.relative_to(ROOT)) for path in extras if path.is_file())
    else:
        for path in (DEST/'files').rglob('*'):
            if path.is_file() and path not in outputs:path.unlink()
    if stale:raise SystemExit('Refresh documentation copies: '+', '.join(stale))
    print(f'Documentation copies {"checked" if args.check else "written"}: {len(records)} files')


if __name__=='__main__':main()
