"""MACD with SMA-seeded exponential moving averages."""
from math import fsum


def normalize(options):
    if set(options) - {'fast', 'slow', 'signal'}: raise ValueError('unknown MACD parameter')
    values = {key:options.get(key, default) for key,default in (('fast',12),('slow',26),('signal',9))}
    if any(type(value) is not int or not 1 <= value <= 500 for value in values.values()) or values['fast'] >= values['slow']:
        raise ValueError('MACD requires 1 <= fast < slow <= 500 and signal 1..500')
    return values


def ema(values, period):
    result = [None] * len(values)
    if len(values) < period: return result
    current = fsum(values[:period]) / period
    result[period-1] = current
    alpha = 2 / (period + 1)
    for i in range(period, len(values)):
        current += alpha * (values[i] - current)
        result[i] = current
    return result


def calculate(candles, options):
    closes = [bar['close'] for bar in candles]
    fast, slow = ema(closes, options['fast']), ema(closes, options['slow'])
    positions = [i for i in range(len(closes)) if fast[i] is not None and slow[i] is not None]
    values = [fast[i] - slow[i] for i in positions]
    signals = ema(values, options['signal'])
    points = []
    for position, value, signal in zip(positions, values, signals):
        if signal is None: continue
        points.append({'time':candles[position]['time'], 'macd':round(value, 8),
                       'signal':round(signal, 8), 'histogram':round(value-signal, 8),
                       'is_open':candles[position]['is_open']})
    return points
