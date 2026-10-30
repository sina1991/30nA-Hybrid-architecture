"""A trusted module runnable by Python or the Dashboard service."""
from pathlib import Path
import sys
module_root = str(Path(__file__).resolve().parents[1])
if module_root not in sys.path:
    sys.path.insert(0, module_root)
from module_support import main

import json
import re

def run(data):
    theme = data.get('theme', 'midnight')
    if not isinstance(theme, str) or not re.fullmatch(r'[a-z0-9-]+', theme):
        raise ValueError('invalid theme')
    theme = {'compact-6': 'midnight', 'standard-8': 'midnight', 'wide-12': 'midnight'}.get(theme, theme)
    path = Path(__file__).resolve().parent / 'themes' / (theme + '.json')
    try:
        item = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        raise ValueError('theme not found') from None
    return {'name': item['name'], 'colors': item['colors']}

if __name__ == '__main__':
    sys.exit(main(run))
