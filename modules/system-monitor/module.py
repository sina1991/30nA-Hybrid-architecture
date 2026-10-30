"""Standalone read-only server monitor."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from module_support import main
from host_monitor import system as run

if __name__ == '__main__':
    sys.exit(main(run))
