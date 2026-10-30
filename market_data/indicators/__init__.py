"""Explicit registry of indicator implementations."""
from . import sma, rsi, macd

REGISTRY = {'sma': sma, 'rsi': rsi, 'macd': macd}
DEFAULTS = {'sma': {'period': 20}, 'rsi': {'period': 14},
            'macd': {'fast': 12, 'slow': 26, 'signal': 9}}


def normalize(name, options):
    if name not in REGISTRY or not isinstance(options, dict):
        raise ValueError('unknown indicator')
    return REGISTRY[name].normalize(options)


def calculate(name, candles, options):
    return REGISTRY[name].calculate(candles, normalize(name, options))
