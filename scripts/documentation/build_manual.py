#!/usr/bin/env python3
"""Build deterministic Persian reference, single-volume Markdown and printable HTML.

Read tracked/source files only; never import application modules, read runtime
credentials, inspect a process environment, or query a live database.
"""
import argparse
import ast
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
MANUAL = ROOT / 'docs/manual'


def files():
    output = subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT)
    return sorted({name.decode() for name in output.split(b'\0') if name
                   and not name.decode().startswith('docs/')})


def literal(node):
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        return None


def escape(value):
    return str(value).replace('|','\\|').replace('\n',' ')


def link(path, line=None):
    return '['+path+'](../../'+path+('' if line is None else '#L'+str(line))+')'


def collect():
    records, variables, symbols, tables, commands, errors = [], [], [], [], [], []
    for name in files():
        path = ROOT/name
        if not path.is_file():
            continue
        data = path.read_bytes()
        records.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        if path.suffix != '.py':
            continue
        tree = ast.parse(data,filename=name)
        class Visitor(ast.NodeVisitor):
            def __init__(self):self.scope=[]
            def visit_ClassDef(self,node):
                symbols.append((name,node.lineno,'.'.join(self.scope+[node.name]),'class'))
                self.scope.append(node.name);self.generic_visit(node);self.scope.pop()
            def visit_FunctionDef(self,node):
                symbols.append((name,node.lineno,'.'.join(self.scope+[node.name]),'('+ast.unparse(node.args)+')'))
                self.scope.append(node.name);self.generic_visit(node);self.scope.pop()
            visit_AsyncFunctionDef=visit_FunctionDef
        Visitor().visit(tree)
        for node in ast.walk(tree):
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='code' for t in node.targets):
                value=literal(node.value)
                if isinstance(value,str) and re.fullmatch(r'[A-Z][A-Z0-9_]+',value):errors.append((value,name,node.lineno))
            if isinstance(node,ast.Call):
                function=ast.unparse(node.func).rsplit('.',1)[-1]
                index=1 if function in ('APIError','fail') else 0
                if function in ('APIError','fail','ExecutionError','ConsumerAPIError') and len(node.args)>index:
                    value=literal(node.args[index])
                    if isinstance(value,str) and re.fullmatch(r'[A-Z][A-Z0-9_]+',value):errors.append((value,name,node.lineno))
            if isinstance(node,ast.Subscript) and ast.unparse(node.value)=='os.environ':
                key=literal(node.slice)
                if isinstance(key,str):variables.append((key,name,node.lineno,'tooling assignment' if isinstance(node.ctx,ast.Store) else 'required lookup'))
            if isinstance(node,ast.Call):
                func=ast.unparse(node.func)
                if func in ('os.getenv','os.environ.get') and node.args:
                    key=literal(node.args[0])
                    if isinstance(key,str):variables.append((key,name,node.lineno,'optional lookup'))
                if isinstance(node.func,ast.Attribute) and node.func.attr=='add_argument':
                    flags=[literal(arg) for arg in node.args]
                    flags=[flag for flag in flags if isinstance(flag,str)]
                    if flags:commands.append((name,node.lineno,', '.join(flags)))
            if isinstance(node,ast.Constant) and isinstance(node.value,str):
                match=re.search(r'CREATE TABLE(?: IF NOT EXISTS)?\s+(\w+)\s*\(',node.value,re.I)
                if match:tables.append((name,node.lineno,match.group(1),node.value.strip()))
    return {'files':records,'environment':sorted(set(variables)),
            'symbols':sorted(symbols),'tables':sorted(tables),'cli':sorted(set(commands)),'errors':sorted(set(errors))}


def reference(facts):
    rows=['# مرجع ماشینی و پوشش فایل‌ها','',
          'این فصل از فایل‌های Git، AST کد و OpenAPI ساخته شده است. هیچ env، credential یا DB عملیاتی خوانده نمی‌شود.',
          'فایل‌های documentation از manifest فنی زیر کنار گذاشته شده‌اند تا خروجی به خودش وابسته نشود؛ checker همه صفحات Markdown را جداگانه بررسی می‌کند.',
          '',f"تعداد فایل‌های فنی و پشتیبان: **{len(facts['files'])}**؛ تعداد نمادهای Python: **{len(facts['symbols'])}**.",'',
          '## موجودی کامل فایل‌های فنی','', '| فایل | byte | SHA-256 |','|---|---:|---|']
    for record in facts['files']:
        rows.append('| '+link(record['path'])+' | '+str(record['bytes'])+' | `'+record['sha256']+'` |')
    rows+=['','## محل خواندن متغیرهای محیطی','','فهرست، نام و محل خواندن را نشان می‌دهد؛ secret value یا env جاری در آن وجود ندارد. defaults، پیشوندهای پویا و الزامات عملیاتی در فصل تنظیمات توضیح داده شده‌اند.','','| نام | منبع | شیوه |','|---|---|---|']
    for key,path,line,kind in facts['environment']:rows.append(f'| `{key}` | {link(path,line)} | {kind} |')
    rows+=['','## همه CLI flagهای Python','','| script | flag یا positional argument |','|---|---|']
    for path,line,flags in facts['cli']:rows.append(f'| {link(path,line)} | `{escape(flags)}` |')
    rows+=['','## error codeهای literal در Python','','codeهای پویا، پیام‌های UI و status HTTP با این فهرست یکسان نیستند؛ معنی عملیاتی خطاها در فصل عیب‌یابی است.','','| code | منبع |','|---|---|']
    for code,path,line in facts['errors']:rows.append(f'| `{code}` | {link(path,line)} |')
    rows+=['','## DDL موجود در کد' ,'','این SQLها مرجع ساختارند، دستور migration دستی نیستند. یک نام جدول در چند store مستقل می‌تواند معنای متفاوت داشته باشد.']
    for path,line,name,sql in facts['tables']:
        rows+=['',f'### جدول {name} در {path}','',link(path,line),'','```sql',sql,'```']
    rows+=['','## نمادهای Python','','این فهرست شامل classها، توابع، متدها و توابع تو‌در‌تو است؛ public API بودن از حضور در این جدول نتیجه نمی‌شود.','','| منبع | نماد | signature |','|---|---|---|']
    for path,line,name,signature in facts['symbols']:rows.append(f'| {link(path,line)} | `{escape(name)}` | `{escape(signature)}` |')
    for name in ('contracts/worker/manager.openapi.json','contracts/worker/runtime.openapi.json','contracts/dashboard/openapi.json'):
        api=json.loads((ROOT/name).read_text())
        rows+=['','## HTTP مرجع '+api['info']['title'],'',link(name),'','| method | path | operation | پاسخ‌های تعریف‌شده |','|---|---|---|---|']
        for path,item in sorted(api['paths'].items()):
            for method,operation in sorted(item.items()):
                if method not in ('get','post','put','patch','delete','options','head'):continue
                rows.append('| '+method.upper()+' | `'+path+'` | `'+operation.get('operationId','')+'` | '+', '.join(operation.get('responses',{}))+' |')
        for model,schema in sorted(api.get('components',{}).get('schemas',{}).items()):
            rows+=['',f'### Schema: {model} — {api["info"]["title"]}','','```json',json.dumps(schema,ensure_ascii=False,indent=2,sort_keys=True),'```']
    return '\n'.join(rows)+'\n'


def agent_guide(facts):
    rows=[(ROOT/'docs/AGENT_GUIDE.source.md').read_text().rstrip(),
          '', '<!-- Generated contract snapshots and Python/OpenAPI index. Do not edit. -->',
          '', '## تنظیمات فعلی و limitهای مسیر اجرا', '',
          (MANUAL/'10-configuration.md').read_text().replace('# ۱۰ — مرجع تنظیمات و limitها',
              '### مرجع تنظیمات').replace('](../../','](../').rstrip()]
    for record in facts['files']:
        name=record['path']
        if name.startswith('contracts/') and name.endswith(('.yaml','.yml')):
            rows += ['', '## Contract: '+name, '', '['+name+'](../'+name+')',
                     '', '```yaml', (ROOT/name).read_text().rstrip(), '```']
    rows += ['', reference(facts).replace('](../../','](../').rstrip()]
    return '\n'.join(rows)+'\n'


def book(manifest,contents):
    rows=['# '+manifest['title'],'', 'تاریخ بررسی: `'+manifest['date']+'`؛ مبنای رفتار برنامه: `'+manifest['application_commit']+'`.',
          '', 'این کتاب نسخه یک‌جلدی فصل‌های همین پوشه است. فصل‌ها و مرجع ماشینی منبع نگهداری هستند؛ BOOK.md و HTML را دستی ویرایش نکنید.', '', '## فهرست مطالب','']
    for index,name in enumerate(manifest['chapters']):
        title=contents[name].splitlines()[0].removeprefix('# ')
        rows.append(f'- [{title}](#chapter-{index:02d})')
    for index,name in enumerate(manifest['chapters']):
        text=contents[name]
        for other_index,other_name in enumerate(manifest['chapters']):
            text=text.replace(']('+other_name+')',f'](#chapter-{other_index:02d})')
        rows+=['',f'<a id="chapter-{index:02d}"></a>','',text.rstrip()]
    return '\n'.join(rows)+'\n'


def render_html(markdown_text,manifest):
    import markdown
    body=markdown.markdown(markdown_text,extensions=['tables','fenced_code','toc'],output_format='html')
    # Keep source links useful when the HTML is downloaded without a repository.
    def remote(match):
        path=match.group(1)
        return 'href="https://github.com/sina1991/30nA-Hybrid-architecture/blob/'+manifest['repository_ref']+'/'+html.escape(path,quote=True)+'"'
    body=re.sub(r'href="\.\./\.\./([^\"]+)"',remote,body)
    return '<!doctype html>\n<html lang="fa" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(manifest['title'])+'''</title>
<style>
body{font:16px/1.95 Tahoma,Arial,sans-serif;margin:0 auto;padding:32px;max-width:1100px;color:#172033;background:#fff}
h1,h2,h3{line-height:1.5;color:#0b3153}h1{margin-top:2em;border-bottom:2px solid #acc3d6;padding-bottom:.4em}
a{color:#07599b;overflow-wrap:anywhere}table{border-collapse:collapse;width:100%;font-size:13px;margin:16px 0}
td,th{border:1px solid #cbd5e1;padding:7px;text-align:right;vertical-align:top;overflow-wrap:anywhere}
th{background:#eff5fa}pre{direction:ltr;text-align:left;background:#f1f5f9;padding:14px;white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}
code{direction:ltr;unicode-bidi:isolate;font-family:monospace;overflow-wrap:anywhere}.nowrap{white-space:nowrap;direction:ltr;unicode-bidi:isolate}blockquote{border-right:4px solid #c48a11;padding:8px 16px;margin:16px 0;background:#fff8e7}
@media print{body{font-size:10pt;padding:0;max-width:none}h1{break-before:page}pre,table{font-size:8pt}tr{break-inside:avoid}a{color:inherit;text-decoration:none}@page{size:A4;margin:16mm}}
</style><body>'''+body+'</body></html>\n'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    manifest=json.loads((MANUAL/'manifest.json').read_text())
    facts=collect()
    outputs={'20-generated-reference.md':reference(facts),'source-inventory.json':json.dumps(facts,ensure_ascii=False,indent=2,sort_keys=True)+'\n'}
    contents={name:outputs.get(name,(MANUAL/name).read_text() if (MANUAL/name).exists() else '') for name in manifest['chapters']}
    missing=[name for name,text in contents.items() if not text.strip()]
    if missing:raise SystemExit('Missing chapters: '+', '.join(missing))
    outputs['../AGENT_GUIDE.md']=agent_guide(facts)
    outputs['BOOK.md']=book(manifest,contents)
    outputs['PROJECT_MANUAL.html']=render_html(outputs['BOOK.md'],manifest)
    stale=[]
    for name,value in outputs.items():
        path=MANUAL/name
        if args.check:
            if not path.exists() or path.read_text()!=value:stale.append(str(path.relative_to(ROOT)))
        else:path.write_text(value)
    if stale:raise SystemExit('Regenerate documentation: '+', '.join(stale))
    print(f"Manual {'checked' if args.check else 'built'}: {len(manifest['chapters'])} chapters, {len(facts['files'])} technical files, {len(facts['symbols'])} Python symbols")

if __name__=='__main__':main()
