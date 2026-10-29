"""Trusted demonstration Worker; no filesystem, network or external dependencies."""
import math


def run(data, configuration):
    values = data.get('values')
    if not isinstance(values, list) or not 1 <= len(values) <= 1000:
        raise ValueError('values must contain 1 to 1000 numbers')
    if any(isinstance(value, bool) or not isinstance(value, (int, float))
           or not math.isfinite(value) or abs(value) > 1e12 for value in values):
        raise ValueError('values must contain finite numbers between -1e12 and 1e12')
    total = sum(values)
    return {'count': len(values), 'sum': total, 'min': min(values),
            'max': max(values), 'mean': total / len(values)}
