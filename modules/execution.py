"""Execute only explicit trusted server modules, never arbitrary submitted code."""
import importlib.util
from functools import lru_cache
from pathlib import Path

PACKAGES = Path(__file__).resolve().parent
MODULE_FILES = {
    **{name: name + '/module.py' for name in ('session-windows','session-clock','round-levels','previous-day-levels','previous-day-session-levels')},
    **{name:name+'/module.py' for name in ('demo-account','demo-trade','demo-bot','demo-positions','demo-reports')},
    **{name:name+'/module.py' for name in ('media-image','media-audio','media-video')},
    'media-player':'media-player/module.py','music-player':'music-player/module.py',
    'myip':'myip/module.py','economic-calendar':'economic-calendar/module.py',
    'clock': 'clock/clock.py', 'calculator': 'calculator/module.py',
    'counter': 'counter/module.py', 'dice-roller': 'dice-roller/module.py',
    'slot-note': 'slot-note/module.py', 'theme-summary': 'theme-summary/module.py',
    'dashboard-health': 'dashboard-health/module.py', 'empty': 'empty/module.py',
    'system-monitor': 'system-monitor/module.py', 'service-monitor': 'service-monitor/module.py',
    'disk-usage': 'disk-usage/module.py', 'network-monitor': 'network-monitor/module.py',
    'process-monitor': 'process-monitor/module.py', 'alerts': 'alerts/module.py',
    'log-viewer': 'log-viewer/module.py', 'docker-monitor': 'docker-monitor/module.py',
    'gold-chart': 'gold-chart/module.py', 'moving-average': 'moving-average/module.py',
    'rsi': 'rsi/module.py', 'macd': 'macd/module.py', 'chat-box':'chat-box/module.py',
}

HOST_MONITORS = frozenset(('system-monitor', 'service-monitor', 'disk-usage', 'network-monitor', 'process-monitor', 'alerts', 'log-viewer', 'docker-monitor'))
MARKET_MODULES = frozenset(('gold-chart', 'moving-average', 'rsi', 'macd'))


class UnknownModule(LookupError):
    pass


@lru_cache(maxsize=64)
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
    try:
        return _load(module_id).run(data)
    except (OSError, UnicodeError) as error:
        if module_id in HOST_MONITORS:
            raise ValueError('monitor cannot access the requested resource') from error
        raise
