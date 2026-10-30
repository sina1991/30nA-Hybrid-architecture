"""Compatibility alias for the independent module infrastructure."""
import sys
from modules import module_state as _implementation
sys.modules[__name__] = _implementation
