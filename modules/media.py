"""Browser-played media descriptors. No transcoding or arbitrary server paths."""
from pathlib import Path
import os
from urllib.parse import urlsplit,quote
from . import uploads

KINDS=('media-player','media-image','media-audio','media-video')
MAX_BYTES=32*1024*1024
FORMATS={'jpg':('image','image/jpeg'),'jpeg':('image','image/jpeg'),'png':('image','image/png'),'gif':('image','image/gif'),'webp':('image','image/webp'),
         'mp3':('audio','audio/mpeg'),'wav':('audio','audio/wav'),'ogg':('audio','audio/ogg'),'m4a':('audio','audio/mp4'),
         'mp4':('video','video/mp4'),'webm':('video','video/webm')}
DEFAULTS={'source':'external','url':'','file_id':'','filename':'','format':'auto','loop':False}


def settings(raw=None):
    if raw is None:raw={}
    if not isinstance(raw,dict) or set(raw)-set(DEFAULTS):raise ValueError('Invalid media settings')
    cfg={**DEFAULTS,**raw}
    if cfg['source'] not in ('external','upload','server') or cfg['format'] not in ('auto',*FORMATS) or type(cfg['loop']) is not bool:raise ValueError('Invalid media source or format')
    for key in ('url','file_id','filename'):
        if not isinstance(cfg[key],str) or len(cfg[key])>2048 or any(ord(c)<32 for c in cfg[key]):raise ValueError('Invalid media reference')
    if cfg['url']:
        parsed=urlsplit(cfg['url'])
        if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password:raise ValueError('Use a direct HTTPS media link without credentials')
    if cfg['filename'] and (Path(cfg['filename']).name!=cfg['filename'] or '/' in cfg['filename'] or '\\' in cfg['filename'] or cfg['filename'] in ('.','..')):raise ValueError('Invalid media filename')
    return cfg


def extension(name):
    fmt=Path(name).suffix.lower().lstrip('.')
    if fmt not in FORMATS:raise ValueError('Unsupported media format')
    return fmt


def signature(fmt,head):
    if fmt in ('jpg','jpeg'):return head.startswith(b'\xff\xd8\xff')
    if fmt=='png':return head.startswith(b'\x89PNG\r\n\x1a\n')
    if fmt=='gif':return head[:6] in (b'GIF87a',b'GIF89a')
    if fmt=='webp':return head[:4]==b'RIFF' and head[8:12]==b'WEBP'
    if fmt=='wav':return head[:4]==b'RIFF' and head[8:12]==b'WAVE'
    if fmt=='mp3':return head.startswith(b'ID3') or (len(head)>1 and head[0]==255 and head[1]&224==224)
    if fmt=='ogg':return head.startswith(b'OggS')
    if fmt in ('mp4','m4a'):return head[4:8]==b'ftyp'
    if fmt=='webm':return head.startswith(b'\x1a\x45\xdf\xa3')
    return False


def root():
    folder=Path(os.environ.get('DASHBOARD_MODULE_STATE_DIR','/var/lib/30na/dashboard')).resolve()/'media'
    checkout=Path(__file__).resolve().parents[1]
    if folder==checkout or checkout in folder.parents:raise OSError('Media state must be outside checkout')
    if folder.is_symlink():raise OSError('Invalid media directory')
    folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    return folder


def server_file(name):
    if not isinstance(name,str) or not name or len(name)>180 or Path(name).name!=name or '/' in name or '\\' in name or any(ord(c)<32 for c in name):raise LookupError('Media file not found')
    path=root()/name
    if path.is_symlink() or not path.is_file():raise LookupError('Media file not found')
    size=path.stat().st_size
    if size>MAX_BYTES:raise ValueError('Server media files are limited to 32 MiB')
    fmt=extension(name)
    with path.open('rb') as stream:head=stream.read(32)
    if not signature(fmt,head):raise ValueError('File content does not match supported media')
    return path,fmt,size


def uploaded(owner,ident):
    item=uploads.access(owner,ident);fmt=extension(item['name'])
    if not signature(fmt,item['content'][:32]):raise ValueError('File content does not match supported media')
    return item,fmt


def library(owner):
    files=[]
    for path in sorted(root().iterdir()):
        try:_,fmt,size=server_file(path.name)
        except (LookupError,ValueError,OSError):continue
        files.append({'filename':path.name,'format':fmt,'kind':FORMATS[fmt][0],'size':size})
        if len(files)>=200:break
    try:items=uploads.list_files(owner)
    except PermissionError:items=[]
    own=[]
    for item in items:
        try:fmt=extension(item['name'])
        except ValueError:continue
        own.append({**item,'format':fmt,'kind':FORMATS[fmt][0]})
    return {'server_files':files,'uploads':own[:200],'max_server_bytes':MAX_BYTES}


def describe(owner,cfg,expected_kind=None):
    cfg=settings(cfg)
    if cfg['source']=='external':
        if not cfg['url']:return {'status':'needs_configuration','settings':cfg,'message':'Set a direct HTTPS media link or select a server file.'}
        fmt=extension(urlsplit(cfg['url']).path) if cfg['format']=='auto' else cfg['format']
        if expected_kind is not None and FORMATS[fmt][0]!=expected_kind:raise ValueError('Media format does not match this player')
        return {'status':'ok','source':'external','url':cfg['url'],'format':fmt,'kind':FORMATS[fmt][0],'mime':FORMATS[fmt][1],'settings':cfg}
    if cfg['source']=='server':
        if not cfg['filename']:return {'status':'needs_configuration','settings':cfg,'message':'Select a shared server media file.'}
        _,fmt,size=server_file(cfg['filename']);path='media/server/'+quote(cfg['filename'],safe='')
    else:
        if not owner:raise PermissionError('Authenticated owner required for uploaded media')
        if not cfg['file_id']:return {'status':'needs_configuration','settings':cfg,'message':'Select a media file from Upload Center.'}
        item,fmt=uploaded(owner,cfg['file_id']);size=item['size'];path='media/upload/'+item['id']
    if expected_kind is not None and FORMATS[fmt][0]!=expected_kind:raise ValueError('Media format does not match this player')
    return {'status':'ok','source':cfg['source'],'path':path,'format':fmt,'kind':FORMATS[fmt][0],'mime':FORMATS[fmt][1],'size':size,'settings':cfg}


def run(data,kind=None):
    if set(data)-{'settings','_state_owner','_state_slot'}:raise ValueError('Unknown media input')
    return describe(data.get('_state_owner'),data.get('settings'),kind)
