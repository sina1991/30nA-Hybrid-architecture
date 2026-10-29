#!/usr/bin/env python3
"""Disposable loopback DATA MANAGER used by the repository test runner."""
import argparse
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from wsgiref.simple_server import make_server, WSGIRequestHandler

parser=argparse.ArgumentParser()
parser.add_argument('--database',required=True)
parser.add_argument('--ready-file',required=True)
args=parser.parse_args()
os.environ['DATA_MANAGER_ALLOW_INSECURE_HEADER']='1'
os.environ['DATA_MANAGER_DB']=args.database
unit=Path(__file__).resolve().parents[2]/'units'/'data-manager'
spec=importlib.util.spec_from_file_location('data_manager',unit/'__init__.py',submodule_search_locations=[str(unit)])
package=importlib.util.module_from_spec(spec)
sys.modules['data_manager']=package
spec.loader.exec_module(package)
application=importlib.import_module('data_manager.api.app').application
class QuietHandler(WSGIRequestHandler):
    def log_message(self,*args):pass
with make_server('127.0.0.1',0,application,handler_class=QuietHandler) as server:
    Path(args.ready_file).write_text(json.dumps({'port':server.server_port}))
    server.serve_forever()
