"""Personal playlist limits, private sources, slot/CLI consistency and Login assets."""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
from modules import slots,uploads,workspaces
from test_account_chat_api import client,create_accounts,auth


def track(url='https://example.com/music.mp3'):
    return {'title':'Night sky','settings':{'source':'external','url':url}}


def test_personal_playlist_limits_and_no_owner_override(client):
    (alice,a),(bob,b),_=create_accounts(client)
    assert client.get('/api/upstreams/music').status_code==401
    for bad in (None,[track()]*11,[track('javascript:alert(1)')],[track('https://example.com/a.mp4')]):
        assert client.put('/api/upstreams/music',headers=auth(a),json={'tracks':bad}).status_code==422
    assert client.put('/api/upstreams/music',headers=auth(a),json={'tracks':[track()]*10}).status_code==200
    assert len(client.get('/api/upstreams/music',headers=auth(a)).json()['payload']['tracks'])==10
    assert client.get('/api/upstreams/music',headers=auth(b)).json()['payload']['tracks']==[]
    assert client.post('/api/upstreams/modules/music-player/run',headers=auth(b),json={'input':{'_state_owner':alice['id']}}).status_code==422
    assert client.post('/api/modules/music-player/run',json={}).status_code==403


def test_direct_audio_does_not_transfer_via_shared_dashboard_and_cli_reads_same_playlist(client):
    (alice,a),(bob,b),(eve,e)=create_accounts(client)
    audio=uploads.create(alice['id'],'audio.mp3','direct',bob['id'],base64.b64encode(b'ID3audio').decode())
    private={'title':'Private audio','settings':{'source':'upload','file_id':audio['id']}}
    assert client.put('/api/upstreams/music',headers=auth(a),json={'tracks':[private]}).status_code==200
    assert client.put('/api/upstreams/music',headers=auth(e),json={'tracks':[private]}).status_code==404
    sid=slots.create(alice['id'])['slot'];slots.bind_active(alice['id'],sid,'music-player',{})
    assert slots.read(alice['id'],sid)['result']['tracks'][0]['title']=='Private audio'
    template=workspaces.save(alice['id'],'Music desk','midnight');loaded=workspaces.load(eve['id'],template['id'])
    assert slots.read(eve['id'],loaded['slots'][0])['result']['tracks']==[]
    root=Path(__file__).resolve().parents[1]
    result=subprocess.run([sys.executable,str(root/'modules/music-player/module.py'),'--owner',alice['id'],'--slot','cli','--input','{}'],text=True,capture_output=True,env=os.environ.copy())
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)['tracks'][0]['title']=='Private audio'
    uploads.access(alice['id'],audio['id'],delete=True)
    assert client.get('/api/upstreams/music',headers=auth(a)).json()['payload']['tracks'][0]['media'] is None


def test_login_routes_and_backgrounds_are_public_without_exposing_credentials(client):
    for route in ('/','/login'):
        response=client.get(route);assert response.status_code==200
        assert 'id="login-screen"' in response.text and 'name="password"' in response.text
        assert 'autocomplete="current-password"' in response.text
    for asset in ('login-galaxy.png','login-airless.png'):
        response=client.get('/assets/'+asset)
        assert response.status_code==200 and response.content.startswith(b'\x89PNG')


def test_login_ip_uses_trusted_request_without_authentication(client,monkeypatch):
    # Arbitrary forwarding headers are ignored outside the trusted loopback hop.
    response=client.get('/api/login/context',headers={'X-30na-Client-IP':'8.8.8.8','X-Forwarded-For':'8.8.8.8'})
    assert response.status_code==200 and response.json()=={'ip':None}
    assert response.headers['cache-control']=='no-store'
    from fastapi.testclient import TestClient
    monkeypatch.setenv('DASHBOARD_TRUST_LOCAL_PROXY','1')
    trusted=TestClient(client.app,client=('127.0.0.1',12345))
    response=trusted.get('/api/login/context',headers={'X-30na-Client-IP':'203.0.113.5'})
    assert response.json()=={'ip':'203.0.113.5'}


def test_note_slot_keeps_plain_text_owner_and_shared_copy(client):
    (alice,a),(bob,b),_=create_accounts(client)
    item=client.post('/api/upstreams/slots',headers=auth(a),json={'type':'note'}).json()['payload']['slot']
    assert item['module_id']=='slot-note' and item['slot_type']=='note'
    sid=item['slot'];slots.execute(alice['id'],sid,{'action':'set','text':'<script>literal</script>\nMy note'})
    assert slots.read(alice['id'],sid)['result']['text']=='<script>literal</script>\nMy note'
    assert client.post('/api/upstreams/slots/'+sid+'/read',headers=auth(b),json={'module_id':'slot-note'}).status_code==404
    template=workspaces.save(alice['id'],'Notes','midnight');loaded=workspaces.load(bob['id'],template['id'])
    assert slots.read(bob['id'],loaded['slots'][0])['result']['text']=='<script>literal</script>\nMy note'
