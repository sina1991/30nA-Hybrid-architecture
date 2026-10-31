"""Standalone trusted indicator. Input/output are JSON."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from modules.module_support import main
from modules.technical import run as calculate

def run(data):
    return calculate('round-levels', data)

if __name__ == '__main__':
    sys.exit(main(run))
