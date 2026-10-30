"""A trusted module runnable by Python or the Dashboard service."""
from pathlib import Path
import sys
module_root = str(Path(__file__).resolve().parents[1])
if module_root not in sys.path:
    sys.path.insert(0, module_root)
from module_support import main

def run(data):
    return {'message': 'Empty slot'}

if __name__ == '__main__':
    sys.exit(main(run))
