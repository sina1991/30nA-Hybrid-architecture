"""Owner-scoped state shared by trusted server modules and local operators."""
import json
import os
from pathlib import Path
import re
import sqlite3


def change(owner, module, slot, default, operation):
    if (not isinstance(owner, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', owner)
            or owner == '__legacy__' or not isinstance(slot, str)
            or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', slot)):
        raise ValueError('invalid owner or slot')
    directory = Path(os.environ.get('DASHBOARD_MODULE_STATE_DIR', '/var/lib/30na/dashboard'))
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    db = sqlite3.connect(directory / 'module-state.sqlite3', timeout=10, isolation_level=None)
    try:
        db.execute('BEGIN IMMEDIATE')
        db.execute('CREATE TABLE IF NOT EXISTS module_state (owner TEXT NOT NULL, module TEXT NOT NULL, slot TEXT NOT NULL, value TEXT NOT NULL, PRIMARY KEY(owner,module,slot))')
        row = db.execute('SELECT value FROM module_state WHERE owner=? AND module=? AND slot=?', (owner, module, slot)).fetchone()
        old = json.loads(row[0]) if row else default
        new, write = operation(old)
        if write:
            db.execute('INSERT INTO module_state(owner,module,slot,value) VALUES(?,?,?,?) ON CONFLICT(owner,module,slot) DO UPDATE SET value=excluded.value',
                       (owner, module, slot, json.dumps(new, ensure_ascii=False, allow_nan=False)))
        db.commit()
        return new
    finally:
        db.close()
