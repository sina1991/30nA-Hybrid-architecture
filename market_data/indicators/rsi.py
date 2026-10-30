"""Wilder RSI, seeded with the first complete period of price changes."""
from math import fsum


def normalize(options):
    if set(options) - {'period'}: raise ValueError('unknown RSI parameter')
    period = options.get('period', 14)
    if type(period) is not int or not 1 <= period <= 500: raise ValueError('period must be between 1 and 500')
    return {'period':period}


def calculate(candles, options):
    period = options['period']
    if len(candles) <= period: return []
    changes = [candles[i]['close'] - candles[i-1]['close'] for i in range(1, period+1)]
    gain = fsum(max(change, 0) for change in changes) / period
    loss = fsum(max(-change, 0) for change in changes) / period
    result = []
    for i in range(period, len(candles)):
        if i > period:
            delta = candles[i]['close'] - candles[i-1]['close']
            gain = (gain * (period-1) + max(delta, 0)) / period
            loss = (loss * (period-1) + max(-delta, 0)) / period
        value = 50.0 if gain == 0 and loss == 0 else 100.0 if loss == 0 else 100 - 100 / (1 + gain/loss)
        result.append({'time':candles[i]['time'], 'value':round(value, 8), 'is_open':candles[i]['is_open']})
    return result
