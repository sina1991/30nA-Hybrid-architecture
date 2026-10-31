"""Typed standalone media descriptor; playback uses browser-native controls."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from modules.module_support import main
from modules.media import run as describe
def run(data):return describe(data,'audio')
if __name__=='__main__':sys.exit(main(run))
