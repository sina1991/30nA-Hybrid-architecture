"""Typed media, server path boundaries, Range and Direct-file authorization."""
import base64
from pathlib import Path
import pytest
from modules import media,uploads,slots,workspaces
from modules.execution import run_module
from test_account_chat_api import client,create_accounts,auth

GIF=base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')


def test_external_media_is_a_descriptor_not_a_server_fetch():
    result=run_module('media-audio',{'settings':{'url':'https://example.com/file.mp3'}})
    assert result['kind']=='audio' and result['url']=='https://example.com/file.mp3'
    for bad in ('javascript:alert(1)','file:///etc/passwd','http://example.com/a.mp3','https://user:secret@example.com/a.mp3'):
        with pytest.raises(ValueError):media.describe(None,{'url':bad})
    with pytest.raises(ValueError):run_module('media-video',{'settings':{'url':'https://example.com/a.mp3'}})
    with pytest.raises(ValueError):media.describe(None,{'url':'https://example.com/image.svg'})
    assert media.describe(None,{})['status']=='needs_configuration'


def test_server_media_is_bounded_to_shared_folder_and_validated(client,tmp_path):
    (alice,a),_,_=create_accounts(client)
    root=media.root();(root/'safe.gif').write_bytes(GIF);(root/'fake.mp4').write_text('<script>evil</script>')
    outside=tmp_path/'private.gif';outside.write_bytes(GIF);(root/'link.gif').symlink_to(outside)
    files=client.get('/api/upstreams/media/library',headers=auth(a)).json()['payload']['server_files']
    assert [item['filename'] for item in files]==['safe.gif']
    assert client.get('/api/upstreams/media/server/safe.gif').status_code==401
    response=client.get('/api/upstreams/media/server/safe.gif',headers={**auth(a),'Range':'bytes=0-5'})
    assert response.status_code==206 and response.content==GIF[:6] and response.headers['content-type']=='image/gif'
    for name in ('../private.gif','link.gif'):
        with pytest.raises((LookupError,ValueError)):media.server_file(name)
    assert client.get('/api/upstreams/media/server/fake.mp4',headers=auth(a)).status_code==422
    with (root/'large.mp4').open('wb') as stream:stream.truncate(media.MAX_BYTES+1)
    with pytest.raises(ValueError):media.server_file('large.mp4')


def test_direct_media_checks_each_request_and_is_not_copied_into_shared_templates(client):
    (alice,a),(bob,b),(eve,e)=create_accounts(client)
    item=uploads.create(alice['id'],'image.gif','direct',bob['id'],base64.b64encode(GIF).decode())
    path='/api/upstreams/media/upload/'+item['id']
    assert client.get(path,headers=auth(e)).status_code==404 and client.get(path).status_code==401
    assert client.get(path,headers={**auth(b),'Range':'bytes=-4'}).content==GIF[-4:]
    assert client.get(path,headers={**auth(b),'Range':'bytes=500-800'}).status_code==416
    data={'settings':{'source':'upload','file_id':item['id']},'kind':'image'}
    assert client.post('/api/upstreams/media/describe',headers=auth(b),json=data).status_code==200
    assert client.post('/api/upstreams/media/describe',headers=auth(e),json=data).status_code==404
    slot=slots.create(alice['id'])['slot'];slots.bind_active(alice['id'],slot,'media-image',{});slots.update_appearance(alice['id'],slot,{'media_settings':data['settings']})
    saved=workspaces.save(alice['id'],'Private media layout','midnight');loaded=workspaces.load(eve['id'],saved['id'])
    row=next(row for row in slots.list_active(eve['id']) if row['slot'] in loaded['slots'])
    assert not row['media_settings']['file_id']
    assert client.post('/api/upstreams/modules/media-image/run',headers=auth(e),json={'input':data}).status_code==422
