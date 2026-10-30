"""Independent chat module; the trusted caller supplies the owner identity."""
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root)); sys.path.insert(0, str(root / 'modules'))
from module_support import main
from modules import chat_store


def run(data):
    if not isinstance(data, dict) or set(data) - {'_state_owner','_state_slot','room','action','text','limit','before'}:
        raise ValueError('invalid chat input')
    owner = data.get('_state_owner')
    if not owner: raise ValueError('authenticated owner is required')
    room, action = data.get('room','public'), data.get('action','read')
    if action == 'read': return {'room':room,'messages':chat_store.messages(owner,room,data.get('limit',50),data.get('before'))}
    if action == 'send': return {'message':chat_store.send(owner,room,data.get('text'))}
    if action == 'rooms': return {'rooms':chat_store.list_rooms(owner)}
    if action == 'requests': return {'requests':chat_store.list_requests(owner)}
    raise ValueError('unknown chat action')


if __name__ == '__main__': sys.exit(main(run))
