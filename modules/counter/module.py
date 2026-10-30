"""A trusted module runnable by Python or the Dashboard service."""
from pathlib import Path
import sys
module_root = str(Path(__file__).resolve().parents[1])
if module_root not in sys.path:
    sys.path.insert(0, module_root)
from module_support import main
from module_state import change

def run(data):
    if '_state_owner' in data:
        action = data.get('action', 'get')
        if action not in ('get', 'increment', 'decrement', 'reset'):
            raise ValueError('unknown counter action')
        def apply(value):
            if type(value) is not int or abs(value) > 1000000000:
                raise ValueError('invalid saved counter')
            result = 0 if action == 'reset' else value + (1 if action == 'increment' else -1 if action == 'decrement' else 0)
            if abs(result) > 1000000000:
                raise ValueError('counter limit exceeded')
            return result, action != 'get'
        return {'value': change(data['_state_owner'], 'counter', data['_state_slot'], 0, apply)}
    value = data.get('value', 0)
    action = data.get('action', 'get')
    if type(value) is not int or abs(value) > 1000000000:
        raise ValueError('value must be an integer between -1000000000 and 1000000000')
    if action not in ('get', 'increment', 'decrement', 'reset'):
        raise ValueError('unknown counter action')
    result = 0 if action == 'reset' else value + (1 if action == 'increment' else -1 if action == 'decrement' else 0)
    if abs(result) > 1000000000:
        raise ValueError('counter limit exceeded')
    return {'value': result}

if __name__ == '__main__':
    sys.exit(main(run))
