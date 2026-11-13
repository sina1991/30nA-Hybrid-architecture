"""AKO FX P-Gap indicator entrypoint; browser-independent and trusted."""
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "modules"))

from modules.module_support import main
from modules.technical import run as run_technical


def run(data):
    return run_technical("akofx", data)


if __name__ == "__main__":
    sys.exit(main(run))
