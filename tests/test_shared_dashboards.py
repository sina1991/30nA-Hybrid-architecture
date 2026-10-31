"""Share safe dashboard state and instantiate it under the receiving principal."""
import json
from modules import slots,workspaces,module_state,indicator_profiles
from test_account_chat_api import client,create_accounts,auth


def test_named_shared_dashboard_copies_layout_notes_and_profiles(client):
    (alice,a),(bob,b),_=create_accounts(client)
    note=slots.create(alice['id']);sid=note['slot'];slots.bind_active(alice['id'],sid,'slot-note',{})
    slots.execute(alice['id'],sid,{'action':'set','text':'Shared <b>note</b>'})
    slots.set_overview(alice['id'],sid,True)
    slots.update_appearance(alice['id'],sid,{'layout':{'x':0,'y':0,'w':4,'h':5},'output_settings':{'mode':'full','label':'NOTE','field':''}})
    # Private room content, outbound credentials and output history are not part
    # of the explicit transferable state allowlist.
    module_state.change(alice['id'],'slot-output',sid,None,lambda _ :({'result':'private-result-secret'},True))
    chart=slots.create(alice['id'],'fix-chart')['slot'];slots.set_overview(alice['id'],chart,True)
    profile=indicator_profiles.save(alice['id'],dict(name='Source Round',type='round-levels',parameters={'auto':False,'manual_step':20},enabled=True))
    slots.update_appearance(alice['id'],chart,{'profile_visibility':{profile['id']:True}})
    original=slots.create(bob['id'])['slot'];slots.set_overview(bob['id'],original,True)
    response=client.post('/api/upstreams/dashboards',headers=auth(a),json={'name':'Trading desk','theme':'midnight'})
    assert response.status_code==200,response.text
    saved=response.json()['payload']['dashboard']
    catalog=client.get('/api/upstreams/dashboards',headers=auth(b)).json()['payload']['dashboards']
    assert catalog[0]['id']==saved['id'] and catalog[0]['sender_name']=='alice'
    assert 'payload' not in catalog[0] and 'private-result-secret' not in json.dumps(catalog)
    result=client.post('/api/upstreams/dashboards/'+saved['id']+'/load',headers=auth(b))
    assert result.status_code==200,result.text
    created=result.json()['payload']['slots'];assert sid not in created and len(created)==2
    rows=slots.list_active(bob['id']);copy=next(row for row in rows if row['slot'] in created and row['module_id']=='slot-note')
    assert copy['layout']=={'x':0,'y':0,'w':4,'h':5} and copy['overview']
    assert slots.read(bob['id'],copy['slot'])['result']['text']=='Shared <b>note</b>'
    slots.execute(bob['id'],copy['slot'],{'action':'set','text':'Bob copy'})
    assert slots.read(alice['id'],sid)['result']['text']=='Shared <b>note</b>'
    assert not next(row for row in rows if row['slot']==original)['overview']
    assert next(row for row in slots.list_active(alice['id']) if row['slot']==sid)['overview']
    loaded_profile=next(p for p in indicator_profiles.list_profiles(bob['id']) if p['name']=='Source Round')
    assert loaded_profile['id']!=profile['id'] and loaded_profile['enabled'] is False
    loaded_chart=next(row for row in rows if row['slot'] in created and row['module_id']=='gold-chart')
    assert loaded_chart['profile_visibility'][loaded_profile['id']] is True
    assert client.delete('/api/upstreams/dashboards/'+saved['id'],headers=auth(b)).status_code==404
    assert client.delete('/api/upstreams/dashboards/'+saved['id'],headers=auth(a)).status_code==200
    assert client.get('/api/upstreams/dashboards').status_code==401


def test_restricted_modules_and_private_chat_do_not_grant_access_on_load(client):
    (alice,a),(bob,b),_=create_accounts(client)
    monitor=slots.create('customer')['slot'];slots.bind_active('customer',monitor,'system-monitor',{})
    saved=workspaces.save('customer','Admin dashboard','midnight')
    loaded=workspaces.load(bob['id'],saved['id'])
    assert loaded['unavailable_modules']==['system-monitor']
    assert slots.binding(bob['id'],loaded['slots'][0])['module_id']=='empty'
    chat=slots.create(alice['id'],'chat')['slot']
    # Populate a private room binding without needing to expose its content.
    module_state.change(alice['id'],'slot-meta',chat,None,lambda old:({**old,'chat_room':'private-room-id','worker':{'enabled':True,'input':{'password':'not-shared'}}},True))
    saved=workspaces.save(alice['id'],'Chat desk','midnight');loaded=workspaces.load(bob['id'],saved['id'])
    row=next(row for row in slots.list_active(bob['id']) if row['slot'] in loaded['slots'])
    assert row['chat_room']=='public' and not row['worker']


def test_failed_load_is_atomic_and_same_name_only_updates_own_template(client):
    (alice,a),(bob,b),_=create_accounts(client)
    slots.create(alice['id']);saved=workspaces.save(alice['id'],'Desk','midnight')
    same=workspaces.save(alice['id'],'Desk','midnight');assert same['id']==saved['id']
    other=workspaces.save(bob['id'],'Desk','midnight');assert other['id']!=saved['id']
    for _ in range(100):slots.create(bob['id'])
    before=slots.list_active(bob['id'])
    response=client.post('/api/upstreams/dashboards/'+saved['id']+'/load',headers=auth(b))
    assert response.status_code==422 and slots.list_active(bob['id'])==before


def test_portable_calculator_content_is_copied_with_a_new_revision(client):
    (alice,a),(bob,b),_=create_accounts(client)
    sid=slots.create(alice['id'])['slot'];slots.bind_active(alice['id'],sid,'calculator',{})
    before=slots.execute(alice['id'],sid,{'a':10,'b':5,'operation':'add'})['result']
    template=workspaces.save(alice['id'],'Calculator','midnight');loaded=workspaces.load(bob['id'],template['id'])
    assert slots.read(bob['id'],loaded['slots'][0])['result']==before
