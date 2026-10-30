"""Helpers for trusted, standalone server-side modules."""
import argparse
import json
import sys


def main(run):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='{}', help='JSON object passed to the module')
    args = parser.parse_args()
    try:
        value = json.loads(args.input)
        if not isinstance(value, dict):
            raise ValueError('input must be a JSON object')
        print(json.dumps(run(value), ensure_ascii=False, allow_nan=False))
    except (ValueError, TypeError, KeyError, OverflowError, ZeroDivisionError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0
