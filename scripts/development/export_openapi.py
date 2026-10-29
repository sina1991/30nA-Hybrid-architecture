#!/usr/bin/env python3
"""Export HTTP contracts from the same factories used by the services."""
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
for unit in ('worker-manager','worker-runtime'):
    sys.path.insert(0,str(ROOT/'units'/unit))
from worker_manager.api import create_app as manager_app
from worker_manager.control_service import ControlService
from worker_runtime.api import create_app as runtime_app

with tempfile.TemporaryDirectory() as directory:
    service=ControlService(Path(directory)/'db',lambda owner:None)
    try:
        for name,app in [('manager',manager_app(service,Path(directory)/'unused-credentials')),
                         ('runtime',runtime_app(Path(directory)/'unused-credentials',lambda owner:None))]:
            path=ROOT/'contracts'/'worker'/f'{name}.openapi.json'
            path.write_text(json.dumps(app.openapi(),indent=2,sort_keys=True)+'\n')
    finally:
        service.close()
