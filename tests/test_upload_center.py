"""Upload authorization, safe downloads and owner-scoped presentation."""
import base64
from test_account_chat_api import client, create_accounts, auth
from modules import uploads
import pytest


def put(client, token, **updates):
    body=dict(name='report.html',visibility='direct',recipient=None,content=base64.b64encode(b'<script>alert(1)</script>').decode())
    body.update(updates)
    return client.post('/api/upstreams/uploads',headers=auth(token),json=body)


def test_direct_access_delete_and_safe_download(client):
    (alice,a),(bob,b),(eve,e)=create_accounts(client)
    response=put(client,a,recipient=bob['id'])
    assert response.status_code==200
    file=response.json()['payload']['file']; path='/api/upstreams/uploads/'+file['id']
    assert client.get(path+'/content').status_code==401
    assert client.get(path+'/content',headers=auth(e)).status_code==404
    assert client.get('/api/upstreams/uploads',headers=auth(e)).json()['payload']['files']==[]
    for token in (a,b):
        result=client.get(path+'/content',headers=auth(token))
        assert result.status_code==200 and result.content==b'<script>alert(1)</script>'
        assert result.headers['content-type']=='application/octet-stream'
        assert result.headers['content-disposition'].startswith('attachment;')
        assert result.headers['x-content-type-options']=='nosniff'
        assert result.headers['cache-control']=='no-store'
    assert client.delete(path,headers=auth(b)).status_code==404
    assert client.delete(path,headers=auth(e)).status_code==404
    assert client.delete(path,headers=auth(a)).status_code==200
    assert client.get(path+'/content',headers=auth(a)).status_code==404


def test_public_limits_names_and_disabled_accounts(client):
    (alice,a),(bob,b),_=create_accounts(client)
    for name in ('../evil','C:\\evil','x\r\nInjected: yes','..'):
        assert put(client,a,name=name,visibility='public').status_code==422
    assert put(client,a,recipient='unknown').status_code==422
    assert put(client,a,visibility='public',content='not base64').status_code==422
    assert put(client,a,visibility='public',content=base64.b64encode(b'x'*(uploads.MAX_BYTES+1)).decode()).status_code==413
    file=put(client,a,visibility='public').json()['payload']['file']
    assert client.get('/api/upstreams/uploads/'+file['id']+'/content',headers=auth(b)).status_code==200
    assert len(uploads.list_files(bob['id']))==1
    assert client.post('/api/upstreams/accounts/'+bob['id']+'/enabled',headers=auth('legacy-secret'),json={'enabled':False}).status_code==200
    assert client.get('/api/upstreams/uploads/'+file['id']+'/content',headers=auth(b)).status_code==401


def test_upload_state_cannot_live_in_checkout(monkeypatch):
    from pathlib import Path
    monkeypatch.setenv('DASHBOARD_MODULE_STATE_DIR',str(Path(uploads.__file__).resolve().parents[1]/'bad-state'))
    with pytest.raises(OSError):
        with uploads.database(): pass


def test_output_is_owner_scoped_and_does_not_change_result(client):
    (_,a),(_,b),_=create_accounts(client)
    slot=client.post('/api/upstreams/slots',headers=auth(a),json={'type':'standard'}).json()['payload']['slot']['slot']
    path='/api/upstreams/slots/'+slot
    assert client.post(path+'/binding',headers=auth(a),json={'module_id':'calculator','context':{}}).status_code==200
    execute=lambda: client.post(path+'/execute',headers=auth(a),json={'module_id':'calculator','input':{'a':5,'b':3,'operation':'add'}}).json()['payload']['result']
    before=execute()
    settings=dict(mode='summary',label='VALUE',field='value',font_size=24,text_color='#123456',background_color='#abcdef')
    assert client.post(path+'/appearance',headers=auth(a),json={'output_settings':settings}).status_code==200
    assert client.post(path+'/appearance',headers=auth(b),json={'output_settings':settings}).status_code==404
    rows=client.get('/api/upstreams/slots/active',headers=auth(a)).json()['payload']['slots']
    assert next(row for row in rows if row['slot']==slot)['output_settings']==settings
    assert execute()==before
