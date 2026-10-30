"""Read-only host measurements for authenticated monitoring modules."""
import math
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import time


def _mem():
    values = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key, _, value = line.partition(':')
        if key in ('MemTotal', 'MemAvailable'):
            values[key] = int(value.split()[0]) * 1024
    total, available = values['MemTotal'], values['MemAvailable']
    return {'total_bytes': total, 'available_bytes': available, 'used_bytes': total - available,
            'used_percent': round((total - available) / total * 100, 1) if total else 0}


def _cpu_sample():
    fields = [int(x) for x in Path('/proc/stat').read_text().splitlines()[0].split()[1:9]]
    return sum(fields), fields[3] + fields[4]


def system(data):
    before, idle_before = _cpu_sample()
    time.sleep(0.25)
    after, idle_after = _cpu_sample()
    delta = after - before
    disk = shutil.disk_usage('/')
    return {'cpu_percent': round((1 - (idle_after - idle_before) / delta) * 100, 1) if delta else 0,
            'memory': _mem(), 'disk': {'path': '/', 'total_bytes': disk.total, 'used_bytes': disk.used,
                                      'free_bytes': disk.free},
            'uptime_seconds': float(Path('/proc/uptime').read_text().split()[0])}


def disk(data):
    path = data.get('path', '/')
    allowed = [Path(p).resolve() for p in os.environ.get('THIRTYNA_MONITOR_DISK_PATHS', '/').split(':') if p]
    if not isinstance(path, str) or len(path) > 4096 or Path(path).resolve() not in allowed:
        raise ValueError('path must be in THIRTYNA_MONITOR_DISK_PATHS')
    try:
        usage = shutil.disk_usage(path)
    except OSError:
        raise ValueError('disk path is unavailable') from None
    return {'path': path, 'total_bytes': usage.total, 'used_bytes': usage.used, 'free_bytes': usage.free,
            'used_percent': round(usage.used / usage.total * 100, 1) if usage.total else 0}


def network(data):
    requested = data.get('interface')
    if requested is not None and (not isinstance(requested, str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,32}', requested)):
        raise ValueError('invalid interface')
    rows = []
    for line in Path('/proc/net/dev').read_text().splitlines()[2:]:
        name, _, values = line.partition(':')
        name, fields = name.strip(), values.split()
        if len(fields) >= 16 and (requested is None or name == requested):
            rows.append({'interface': name, 'received_bytes': int(fields[0]), 'transmitted_bytes': int(fields[8])})
    if requested and not rows: raise ValueError('interface not found')
    return {'interfaces': rows, 'note': 'Counters since interface initialization; not a transfer rate.'}


def service(data):
    service_name = data.get('service', 'nginx.service')
    allowed = set(os.environ.get('THIRTYNA_MONITOR_SERVICES', 'nginx.service,docker.service').split(','))
    if not isinstance(service_name, str) or service_name not in allowed or not re.fullmatch(r'[A-Za-z0-9_.@-]+\.service', service_name):
        raise ValueError('service must be in THIRTYNA_MONITOR_SERVICES')
    try:
        result = subprocess.run(['systemctl', 'show', '--no-pager', '--property=LoadState,ActiveState,SubState', '--', service_name],
                                capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise ValueError('systemctl unavailable') from None
    if result.returncode: raise ValueError('service status unavailable')
    values = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    return {'service': service_name, 'load_state': values.get('LoadState', 'unknown'),
            'active_state': values.get('ActiveState', 'unknown'), 'sub_state': values.get('SubState', 'unknown')}


def process(data):
    name = data.get('name')
    if name is not None and (not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,15}', name)):
        raise ValueError('invalid process name')
    def sample():
        found = {}
        for item in Path('/proc').iterdir():
            if not item.name.isdigit(): continue
            try:
                if name is not None and (item / 'comm').read_text().strip() != name: continue
                stat = (item / 'stat').read_text()
                fields = stat[stat.rfind(')') + 2:].split()
                found[item.name] = (int(fields[11]) + int(fields[12]), int(fields[19]) * os.sysconf('SC_PAGE_SIZE'))
            except (OSError, UnicodeError, ValueError, IndexError): continue
        return found
    first = sample()
    started = time.monotonic()
    time.sleep(0.25)
    second = sample()
    elapsed = time.monotonic() - started
    ticks = sum(max(0, value[0] - first[pid][0]) for pid, value in second.items() if pid in first)
    cpu = ticks / os.sysconf('SC_CLK_TCK') / elapsed * 100 if elapsed else 0
    return {'name': name, 'matching_processes': len(second), 'cpu_percent': round(cpu, 1),
            'resident_memory_bytes': sum(value[1] for value in second.values()),
            'scope': 'processes visible to the executing user; CPU percent is relative to one core'}


def alerts(data):
    threshold = data.get('disk_used_percent', 90)
    if type(threshold) not in (int, float) or not math.isfinite(threshold) or not 0 <= threshold <= 100:
        raise ValueError('disk_used_percent must be between 0 and 100')
    state = disk(data)
    triggered = state['used_percent'] >= threshold
    entries = ([{'type': 'disk_usage', 'path': state['path'], 'used_percent': state['used_percent'],
                 'threshold_percent': threshold}] if triggered else [])
    service_state = None
    if 'service' in data:
        service_state = service(data)
        if service_state['active_state'] != 'active':
            entries.append({'type': 'service_inactive', 'service': service_state['service'],
                            'active_state': service_state['active_state']})
    return {'alerts': entries, 'disk': state, 'service': service_state}


def logs(data):
    path = data.get('path')
    allowed = [Path(p).resolve() for p in os.environ.get('THIRTYNA_MONITOR_LOG_PATHS', '').split(':') if p]
    if not isinstance(path, str) or len(path) > 4096 or Path(path).resolve() not in allowed:
        raise ValueError('path must be in THIRTYNA_MONITOR_LOG_PATHS')
    lines = data.get('lines', 20)
    query = data.get('query', '')
    if type(lines) is not int or not 1 <= lines <= 100 or not isinstance(query, str) or len(query) > 200:
        raise ValueError('lines must be 1-100 and query must be at most 200 characters')
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        with os.fdopen(fd, 'rb') as file:
            if not stat.S_ISREG(os.fstat(file.fileno()).st_mode):
                raise ValueError('log must be a regular file')
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(max(0, size - 262144))
            text = file.read(262144).decode('utf-8', errors='replace')
    except OSError:
        raise ValueError('log is unavailable to the executing user') from None
    matches = [line[:2000] for line in text.splitlines() if query in line]
    return {'path': path, 'lines': matches[-lines:], 'search_limited_to_last_bytes': 262144}


def docker(data):
    if os.environ.get('THIRTYNA_MONITOR_DOCKER') != '1':
        raise ValueError('Docker monitoring is disabled; set THIRTYNA_MONITOR_DOCKER=1 for the service')
    try:
        result = subprocess.run(['docker', 'ps', '--all', '--no-trunc', '--format', '{{json .}}'],
                                capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise ValueError('Docker CLI is unavailable') from None
    if result.returncode: raise ValueError('Docker is unavailable to the executing user')
    import json
    entries = []
    for line in result.stdout.splitlines()[:100]:
        try:
            row = json.loads(line)
            entries.append({key: str(row.get(key, ''))[:256] for key in ('ID', 'Names', 'Image', 'State', 'Status')})
        except (ValueError, AttributeError):
            raise ValueError('invalid Docker response') from None
    return {'containers': entries, 'limit': 100}
