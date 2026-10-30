"""Execute only explicit trusted server modules, never arbitrary submitted code."""
import importlib.util
from functools import lru_cache
from pathlib import Path

PACKAGES = Path(__file__).resolve().parent
MODULE_FILES = {
    'clock': 'clock/clock.py', 'calculator': 'calculator/module.py',
    'counter': 'counter/module.py', 'dice-roller': 'dice-roller/module.py',
    'slot-note': 'slot-note/module.py', 'theme-summary': 'theme-summary/module.py',
    'dashboard-health': 'dashboard-health/module.py', 'empty': 'empty/module.py',
}


class UnknownModule(LookupError):
    pass


@lru_cache(maxsize=8)
def _load(module_id):
    spec = importlib.util.spec_from_file_location('trusted_module_' + module_id.replace('-', '_'), PACKAGES / MODULE_FILES[module_id])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_module(module_id, data):
    if module_id not in MODULE_FILES:
        raise UnknownModule('Unknown module')
    if not isinstance(data, dict):
        raise ValueError('input must be a JSON object')
    return _load(module_id).run(data)
