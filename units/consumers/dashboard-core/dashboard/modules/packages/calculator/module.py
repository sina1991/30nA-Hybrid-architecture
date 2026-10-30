"""A trusted module runnable by Python or the Dashboard service."""
from pathlib import Path
import sys
module_root = str(Path(__file__).resolve().parents[2])
if module_root not in sys.path:
    sys.path.insert(0, module_root)
from module_support import main

import math

def run(data):
    a, b = data.get('a'), data.get('b')
    if type(a) not in (int, float) or type(b) not in (int, float) or not math.isfinite(a) or not math.isfinite(b):
        raise ValueError('a and b must be finite numbers')
    action = data.get('operation', 'add')
    if action not in ('add', 'subtract', 'multiply', 'divide'):
        raise ValueError('unknown operation')
    if action == 'divide' and b == 0:
        raise ValueError('division by zero')
    result = {'add': lambda: a + b, 'subtract': lambda: a - b, 'multiply': lambda: a * b, 'divide': lambda: a / b}[action]()
    if not math.isfinite(result):
        raise ValueError('result is not finite')
    return {'result': result}

if __name__ == '__main__':
    sys.exit(main(run))
