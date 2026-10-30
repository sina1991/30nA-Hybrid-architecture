"""A trusted module runnable by Python or the Dashboard service."""
from pathlib import Path
import sys
module_root = str(Path(__file__).resolve().parents[1])
if module_root not in sys.path:
    sys.path.insert(0, module_root)
from module_support import main

import secrets

def run(data):
    count, sides = data.get('count', 1), data.get('sides', 6)
    if type(count) is not int or type(sides) is not int or not 1 <= count <= 100 or not 2 <= sides <= 1000:
        raise ValueError('count must be 1..100 and sides 2..1000')
    rolls = [secrets.randbelow(sides) + 1 for _ in range(count)]
    return {'rolls': rolls, 'total': sum(rolls)}

if __name__ == '__main__':
    sys.exit(main(run))
