"""Runs inside a separate Python interpreter; NOT a security sandbox."""
import importlib
import json
import sys

def main():
    archive, entrypoint = sys.argv[1:3]
    sys.path.insert(0, archive)
    data = json.load(sys.stdin)
    try:
        module, function = entrypoint.split(':', 1)
        result = getattr(importlib.import_module(module), function)(data['input'], data['configuration'])
        print(json.dumps({'ok': True, 'result': result}, allow_nan=False))
    except BaseException as exc:
        print(json.dumps({'ok': False, 'error': {'code': 'EXECUTION_ERROR', 'message': str(exc)[:512]}}))
if __name__ == '__main__':
    main()
