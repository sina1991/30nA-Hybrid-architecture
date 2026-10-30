"""Compatibility alias for the independent module infrastructure."""
import sys
from modules import module_support as _implementation
sys.modules[__name__] = _implementation
