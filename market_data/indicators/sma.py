"""Simple moving average of observed candle closes."""
from collections import deque
from decimal import Decimal, localcontext


def normalize(options):
    if set(options) - {'period'}: raise ValueError('unknown SMA parameter')
    period = options.get('period', 20)
    if type(period) is not int or not 1 <= period <= 500: raise ValueError('period must be between 1 and 500')
    return {'period':period}


def calculate(candles, options):
    period = options['period']
    points, window = [], deque()
    with localcontext() as context:
        context.prec = 340
        total = Decimal(0)
        for bar in candles:
            close = Decimal(str(bar['close']))
            window.append(close)
            total += close
            if len(window) > period:
                total -= window.popleft()
            if len(window) == period:
                points.append({'time':bar['time'], 'value':float(round(total / period, 8)),
                               'is_open':bar['is_open']})
    return points
