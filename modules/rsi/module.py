"""Wilder RSI runnable independently or through a slot."""
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root)); sys.path.insert(0, str(root / 'modules'))
from module_support import main
from market_data.data import indicator


def run(data):
    if set(data) - {'limit', 'period', 'include_open', 'latest', 'end_time'}: raise ValueError('unknown indicator input')
    latest = data.get('latest', False)
    if type(latest) is not bool: raise ValueError('latest must be boolean')
    result = indicator('rsi', {'period':data.get('period', 14)}, limit=1 if latest else data.get('limit', 200), include_open=data.get('include_open', True), end_time=data.get('end_time'))
    result['period'] = result['parameters']['period']
    if latest: result['latest'] = result['points'][-1] if result['points'] else None
    return result


if __name__ == '__main__': sys.exit(main(run))
