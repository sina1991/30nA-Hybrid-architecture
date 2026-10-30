"""A trusted module runnable by Python or the Dashboard service."""
from pathlib import Path
import sys
module_root = str(Path(__file__).resolve().parents[2])
if module_root not in sys.path:
    sys.path.insert(0, module_root)
from module_support import main

def run(data):
    text = data.get('text', '')
    if not isinstance(text, str) or len(text) > 10000:
        raise ValueError('text must be a string of at most 10000 characters')
    return {'text': text}

if __name__ == '__main__':
    sys.exit(main(run))
