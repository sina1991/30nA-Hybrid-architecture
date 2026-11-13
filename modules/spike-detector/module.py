"""Configurable All Spikes detector for XAUUSD chart candles."""
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root)); sys.path.insert(0, str(root / 'modules'))
from module_support import main
from technical import run as run_technical


def run(data):
    return run_technical('spike-detector', data)


if __name__ == '__main__': sys.exit(main(run))
