"""Standalone JSON economic calendar, independent of the browser."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from modules.module_support import main
from modules.economic_calendar import run

if __name__=='__main__':sys.exit(main(run))
