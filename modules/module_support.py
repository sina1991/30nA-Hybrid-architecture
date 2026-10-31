"""Helpers for trusted, standalone server-side modules."""
import argparse
import json
import sys


def main(run):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='{}', help='JSON object passed to the module')
    parser.add_argument('--owner', help='Owner for shared server state')
    parser.add_argument('--slot', help='Slot identifier for shared server state')
    args = parser.parse_args()
    try:
        raw=sys.stdin.read(1000001) if args.input=='-' else args.input
        if len(raw.encode('utf-8'))>1000000:raise ValueError('input too large')
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError('input must be a JSON object')
        if any(str(key).startswith('_') for key in value):
            raise ValueError('reserved input field')
        if bool(args.owner) != bool(args.slot):
            raise ValueError('--owner and --slot must be provided together')
        if args.owner:
            value['_state_owner'], value['_state_slot'] = args.owner, args.slot
        print(json.dumps(run(value), ensure_ascii=False, allow_nan=False))
    except (ValueError, TypeError, LookupError, OverflowError, ZeroDivisionError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except (OSError, UnicodeError):
        print(json.dumps({'error': 'resource unavailable'}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0
