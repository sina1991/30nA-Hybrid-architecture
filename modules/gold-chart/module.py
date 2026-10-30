"""Read XAUUSD one-minute candles and an SMA for chart consumers."""
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / 'modules'))
from module_support import main
from market_data.data import chart


def run(data):
    if set(data) - {'limit', 'period', 'include_open', 'end_time', 'interval'}:
        raise ValueError('unknown chart input')
    period = data.get('period', 20)
    return chart(limit=data.get('limit', max(200, period) if type(period) is int else 200), period=period, include_open=data.get('include_open', True), end_time=data.get('end_time'), interval=data.get('interval', '1m'))


if __name__ == '__main__':
    sys.exit(main(run))
