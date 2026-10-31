"""Standalone demo component; --owner identifies a trusted local operator."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from modules.module_support import main
from modules.demo_components import run as dispatch

def run(data):return dispatch('demo-account',data)

if __name__=='__main__':sys.exit(main(run))
