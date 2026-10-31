"""Named shared dashboard templates; loading always creates receiver-owned slots."""
import json
import re
import time
from uuid import uuid4
from . import slots,indicator_profiles,accounts,uploads,media

META_KEYS = {'overview','layout','minimized','output_settings','frame_color','display_theme','slot_type','chat_room',
             'chart_period','chart_interval','indicator_period','chart_overlay','chart_live','chart_indicators',
             'technical_settings','profile_visibility','calendar_settings','media_settings'}


def connect(owner):
    db=slots._layout_db(owner)
    db.execute('CREATE TABLE IF NOT EXISTS shared_dashboards (id TEXT PRIMARY KEY, sender TEXT NOT NULL, name TEXT NOT NULL, created_at INTEGER NOT NULL, payload TEXT NOT NULL, UNIQUE(sender,name))')
    return db


def catalog(owner):
    db=connect(owner)
    try:
        rows=[dict(zip(('id','sender','name','created_at'),row)) for row in db.execute('SELECT id,sender,name,created_at FROM shared_dashboards ORDER BY created_at DESC,name')]
        db.commit()
    finally:db.close()
    for row in rows:
        user=accounts.get_user(row['sender']);row['sender_name']=user['username'] if user else row['sender']
    return rows


def save(owner,name,theme):
    if not isinstance(name,str) or not name.strip() or len(name)>80 or any(ord(ch)<32 for ch in name):raise ValueError('Invalid dashboard name')
    if not isinstance(theme,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}',theme):raise ValueError('Invalid theme')
    db=connect(owner)
    try:
        rows=db.execute("SELECT b.slot,b.value,m.value FROM module_state b JOIN module_state m ON m.owner=b.owner AND m.slot=b.slot AND m.module='slot-meta' WHERE b.owner=? AND b.module='slot-binding' ORDER BY b.slot",(owner,)).fetchall()
        snapshot=[]
        for slot,raw_binding,raw_meta in rows:
            binding=json.loads(raw_binding);meta={key:value for key,value in json.loads(raw_meta).items() if key in META_KEYS}
            # Private room membership, credentials, worker input, results and
            # execution history are deliberately not transferable templates.
            if binding['module_id']=='chat-box':meta['chat_room']='public'
            media_cfg=meta.get('media_settings',{})
            if binding['module_id'] in media.KINDS and media_cfg.get('source')=='upload':
                try:visible=next((item for item in uploads.list_files(owner) if item['id']==media_cfg.get('file_id')),None)
                except PermissionError:visible=None
                if not visible or visible['recipient'] is not None:meta.pop('media_settings',None)
            state={}
            for module in ('counter','slot-note'):
                if module==binding['module_id']:
                    row=db.execute('SELECT value FROM module_state WHERE owner=? AND module=? AND slot=?',(owner,module,slot)).fetchone()
                    if row:state[module]=json.loads(row[0])
            if binding['module_id'] in ('calculator','dice-roller'):
                row=db.execute("SELECT value FROM module_state WHERE owner=? AND module='slot-output' AND slot=?",(owner,slot)).fetchone()
                if row:
                    output=json.loads(row[0])
                    if output.get('module_id')==binding['module_id'] and output.get('binding_revision')==binding.get('revision'):state['slot-output']=output
            snapshot.append({'binding':{'module_id':binding['module_id'],'context':binding.get('context',{})},'meta':meta,'state':state})
        row=db.execute("SELECT value FROM module_state WHERE owner=? AND module='indicator-profiles' AND slot='catalog'",(owner,)).fetchone()
        profiles=json.loads(row[0]) if row else indicator_profiles.DEFAULTS
        payload=json.dumps({'version':1,'theme':theme,'slots':snapshot,'profiles':profiles},ensure_ascii=False,allow_nan=False)
        if len(payload.encode())>900000:raise ValueError('Dashboard template is too large')
        existing=db.execute('SELECT id FROM shared_dashboards WHERE sender=? AND name=?',(owner,name.strip())).fetchone()
        if not existing and db.execute('SELECT count(*) FROM shared_dashboards WHERE sender=?',(owner,)).fetchone()[0]>=20:raise ValueError('Dashboard template limit reached')
        if not existing and db.execute('SELECT count(*) FROM shared_dashboards').fetchone()[0]>=500:raise ValueError('Shared template limit reached')
        ident=existing[0] if existing else 'dashboard-'+uuid4().hex
        db.execute('INSERT INTO shared_dashboards VALUES(?,?,?,?,?) ON CONFLICT(sender,name) DO UPDATE SET created_at=excluded.created_at,payload=excluded.payload',(ident,owner,name.strip(),int(time.time()),payload));db.commit()
        return {'id':ident,'name':name.strip(),'slot_count':len(snapshot)}
    finally:db.close()


def load(owner,ident):
    if not isinstance(ident,str) or not re.fullmatch(r'dashboard-[0-9a-f]{32}',ident):raise LookupError('Dashboard not found')
    db=connect(owner)
    try:
        row=db.execute('SELECT name,payload FROM shared_dashboards WHERE id=?',(ident,)).fetchone()
        if not row:raise LookupError('Dashboard not found')
        name,payload=row[0],json.loads(row[1]);items=payload['slots']
        count=db.execute("SELECT count(*) FROM module_state WHERE owner=? AND module='slot-meta'",(owner,)).fetchone()[0]
        if count+len(items)>100:raise ValueError('Slot limit reached; remove unused slots first')
        existing=db.execute("SELECT value FROM module_state WHERE owner=? AND module='indicator-profiles' AND slot='catalog'",(owner,)).fetchone()
        profiles=json.loads(existing[0]) if existing else [dict(p) for p in indicator_profiles.DEFAULTS]
        profile_map={}
        for source in payload['profiles']:
            matched=next((p for p in profiles if p['type']==source['type'] and p['name']==source['name'] and p['parameters']==source['parameters']),None)
            if not matched:
                if len(profiles)>=24:raise ValueError('Indicator limit reached; remove unused profiles first')
                matched={**source,'id':'ind-'+uuid4().hex[:12],'enabled':False};profiles.append(matched)
            profile_map[source['id']]=matched['id']
        prepared=[];unavailable=[]
        for item in items:
            module=item['binding']['module_id']
            if module not in slots.MODULE_FILES:unavailable.append(module);module='empty'
            try:slots._authorize_host_monitor(owner,module)
            except ValueError:unavailable.append(module);module='empty'
            meta=dict(item['meta']);meta.pop('worker',None)
            if module=='gold-chart':
                old=meta.get('profile_visibility',{})
                meta['profile_visibility']={p['id']:False for p in profiles}
                for source in payload['profiles']:meta['profile_visibility'][profile_map[source['id']]]=old.get(source['id'],source['enabled'])
            if module=='chat-box':meta['chat_room']='public'
            prepared.append((item,module,meta))
        # Existing data and workers stay owned by this user in Slots. Loading
        # changes which layout is pinned, without deleting existing state.
        for slot,value in db.execute("SELECT slot,value FROM module_state WHERE owner=? AND module='slot-meta'",(owner,)).fetchall():
            old=json.loads(value);old['overview']=False
            db.execute("UPDATE module_state SET value=? WHERE owner=? AND module='slot-meta' AND slot=?",(json.dumps(old),owner,slot))
        created=[]
        for item,module,meta in prepared:
            slot='slot-'+uuid4().hex[:12];created.append(slot)
            binding={'module_id':module,'context':item['binding']['context'],'revision':str(uuid4())}
            for key,value in [('slot-binding',binding),('slot-meta',meta),*item['state'].items()]:
                if key=='slot-output':value={**value,'binding_revision':binding['revision']}
                db.execute('INSERT INTO module_state(owner,module,slot,value) VALUES(?,?,?,?)',(owner,key,slot,json.dumps(value,ensure_ascii=False,allow_nan=False)))
        db.execute("INSERT INTO module_state(owner,module,slot,value) VALUES(?,'indicator-profiles','catalog',?) ON CONFLICT(owner,module,slot) DO UPDATE SET value=excluded.value",(owner,json.dumps(profiles)))
        db.commit()
        return {'name':name,'theme':payload['theme'],'slots':created,'unavailable_modules':unavailable}
    finally:db.close()


def delete(owner,ident):
    db=connect(owner)
    try:
        if not db.execute('DELETE FROM shared_dashboards WHERE id=? AND sender=?',(ident,owner)).rowcount:raise LookupError('Dashboard not found')
        db.commit()
    finally:db.close()
