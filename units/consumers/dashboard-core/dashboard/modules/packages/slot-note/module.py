"""A trusted module runnable by Python or the Dashboard service."""
from pathlib import Path
import sys
module_root = str(Path(__file__).resolve().parents[2])
if module_root not in sys.path:
    sys.path.insert(0, module_root)
from module_support import main
from module_state import change

def run(data):
    if '_state_owner' in data:
        action = data.get('action', 'get')
        if action not in ('get', 'set'):
            raise ValueError('unknown note action')
        text = data.get('text', '')
        if not isinstance(text, str) or len(text) > 10000:
            raise ValueError('text must be a string of at most 10000 characters')
        return {'text': change(data['_state_owner'], 'slot-note', data['_state_slot'], '',
                               lambda old: (text, True) if action == 'set' else (old, False))}
    text = data.get('text', '')
    if not isinstance(text, str) or len(text) > 10000:
        raise ValueError('text must be a string of at most 10000 characters')
    return {'text': text}

if __name__ == '__main__':
    sys.exit(main(run))
