"""Compatibility alias; the trusted registry is owned by the root modules package."""
import sys
from modules import registry as _registry
sys.modules[__name__] = _registry
