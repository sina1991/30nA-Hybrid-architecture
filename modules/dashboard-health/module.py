"""A trusted module runnable by Python or the Dashboard service."""
from pathlib import Path
import sys
module_root = str(Path(__file__).resolve().parents[1])
if module_root not in sys.path:
    sys.path.insert(0, module_root)
from module_support import main

import json
from urllib.request import build_opener, ProxyHandler
from urllib.error import URLError

def run(data):
    port = 8020
    try:
        with build_opener(ProxyHandler({})).open('http://127.0.0.1:' + str(port) + '/health', timeout=3) as response:
            result = json.loads(response.read(4097))
            if not isinstance(result, dict):
                raise ValueError('invalid health response')
    except (OSError, URLError, ValueError):
        return {'service': 'dashboard-core', 'status': 'unavailable'}
    return {'service': str(result.get('service', 'dashboard-core')), 'status': str(result.get('status', 'unknown'))}

if __name__ == '__main__':
    sys.exit(main(run))
