"""Compute a simple moving average from the server's XAUUSD candles."""
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / 'modules'))
from module_support import main
from market_data.data import chart


def run(data):
    if set(data) - {'limit', 'period', 'include_open'}:
        raise ValueError('unknown indicator input')
    period = data.get('period', 20)
    result = chart(limit=data.get('limit', max(200, period) if type(period) is int else 200), period=period, include_open=data.get('include_open', True))
    return {'symbol':result['symbol'], 'interval':result['interval'], 'type':'SMA',
            'period':result['moving_average']['period'], 'points':result['moving_average']['points'],
            'last_success':result['last_success'], 'collector_error':result['collector_error']}


if __name__ == '__main__':
    sys.exit(main(run))
