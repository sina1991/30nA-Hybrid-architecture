"""Standalone media descriptor; actual playback takes place in the browser."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from modules.module_support import main
from modules.media import run

if __name__=='__main__':sys.exit(main(run))
