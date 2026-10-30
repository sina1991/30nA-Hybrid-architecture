"""Calculate a small numerical summary without host or network access."""
import math


def run(data, configuration):
    values = data.get('values', [10, 20, 30])
    factor = configuration.get('multiplier', 1)
    if not isinstance(values, list) or not 1 <= len(values) <= 1000:
        raise ValueError('values must contain 1 to 1000 numbers')
    if any(type(value) not in (int, float) or not math.isfinite(value) or abs(value) > 1e9 for value in values):
        raise ValueError('values must be finite numbers within bounds')
    if type(factor) not in (int, float) or not math.isfinite(factor) or abs(factor) > 1e6:
        raise ValueError('multiplier must be a finite number within bounds')
    total = sum(values)
    return {'count': len(values), 'sum': total, 'average': total / len(values), 'multiplier': factor, 'scaled_sum': total * factor}
