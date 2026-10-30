"""Identity and private chat boundaries, isolated from any live state."""
import time
import pytest
from modules import accounts, chat_store


@pytest.fixture
def users(tmp_path, monkeypatch):
    monkeypatch.setenv('DASHBOARD_MODULE_STATE_DIR', str(tmp_path))
    admin = accounts.bootstrap_admin('administrator', 'admin passphrase long enough')
    alice = accounts.create_user('alice', 'alice passphrase long enough')
    bob = accounts.create_user('bob', 'bob passphrase long enough')
    return admin, alice, bob


def test_sessions_are_owner_bound_and_revoked(users):
    admin, alice, _ = users
    session = accounts.login('alice', 'alice passphrase long enough')
    assert accounts.authenticate(session['token'])['id'] == alice['id']
    with pytest.raises(ValueError): accounts.login('alice', 'wrong passphrase value')
    with pytest.raises(ValueError): accounts.set_enabled(admin['id'], False)
    accounts.set_enabled(alice['id'], False)
    assert accounts.authenticate(session['token']) is None
    with pytest.raises(ValueError): accounts.login('alice', 'alice passphrase long enough')
    accounts.set_enabled(alice['id'], True)
    assert accounts.authenticate(session['token']) is None


def test_private_room_requires_acceptance_and_membership(users):
    admin, alice, bob = users
    invitation = chat_store.request_private(alice['id'], bob['id'])
    with pytest.raises(LookupError): chat_store.respond(admin['id'], invitation['id'], True)
    with pytest.raises(LookupError): chat_store.respond(alice['id'], invitation['id'], True)
    with pytest.raises(ValueError): chat_store.request_private(bob['id'], alice['id'])
    room = chat_store.respond(bob['id'], invitation['id'], True)['room_id']
    assert room in {item['id'] for item in chat_store.list_rooms(alice['id'])}
    assert room not in {item['id'] for item in chat_store.list_rooms(admin['id'])}
    with pytest.raises(PermissionError): chat_store.send(admin['id'], room, 'not a member')
    with pytest.raises(PermissionError): chat_store.messages(admin['id'], room)
    sent = chat_store.send(alice['id'], room, 'hello')
    assert chat_store.messages(bob['id'], room)[0]['id'] == sent['id']
    with pytest.raises(ValueError): chat_store.respond(bob['id'], invitation['id'], True)


def test_public_messages_pagination_and_disabled_accounts(users):
    _, alice, bob = users
    one = chat_store.send(alice['id'], 'public', 'first')
    chat_store.send(bob['id'], 'public', 'second')
    assert [item['body'] for item in chat_store.messages(bob['id'], 'public', before=one['id'] + 1)] == ['first']
    accounts.set_enabled(bob['id'], False)
    with pytest.raises(PermissionError): chat_store.messages(bob['id'], 'public')
    with pytest.raises(PermissionError): chat_store.request_private(alice['id'], bob['id'])
    with pytest.raises(ValueError): chat_store.send(alice['id'], 'public', ' ')


def test_rejected_request_does_not_grant_access(users):
    _, alice, bob = users
    invitation = chat_store.request_private(alice['id'], bob['id'])
    assert chat_store.respond(bob['id'], invitation['id'], False)['room_id'] is None
    assert [room['id'] for room in chat_store.list_rooms(alice['id'])] == ['public']
    assert chat_store.request_private(alice['id'], bob['id'])['status'] == 'pending'


def test_session_expires_and_logout_is_independent(users, monkeypatch):
    now = int(time.time())
    monkeypatch.setattr(accounts.time, 'time', lambda: now)
    first = accounts.login('alice', 'alice passphrase long enough')
    second = accounts.login('alice', 'alice passphrase long enough')
    accounts.logout(first['token'])
    assert accounts.authenticate(first['token']) is None
    assert accounts.authenticate(second['token'])['id'] == users[1]['id']
    monkeypatch.setattr(accounts.time, 'time', lambda: now + accounts.SESSION_SECONDS)
    assert accounts.authenticate(second['token']) is None


def test_existing_customer_workspace_cannot_be_rebootstrapped(users):
    with pytest.raises(ValueError):
        accounts.bootstrap_admin('anotheradmin', 'another long password here')
    assert accounts.get_user('customer')['id'] == users[0]['id']
    with pytest.raises(ValueError):
        accounts.create_user('ALICE', 'another long password here')
