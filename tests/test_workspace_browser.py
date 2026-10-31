"""Dashboard workspace controls and new modules in Chromium."""
import json
from pathlib import Path
import subprocess
from dashboard.app import create_app,load_themes,api_modules


def test_workspace_header_and_slot_controls(tmp_path):
    app=create_app(credential_path=tmp_path/'unused',upstream_factory=lambda owner,token:{})
    html=next(route.endpoint() for route in app.routes if getattr(route,'path',None)=='/')
    script=Path(__file__).resolve().parents[1]/'units/consumers/dashboard-core/browser-tests/workspaces.cjs'
    result=subprocess.run(['node',str(script)],input=json.dumps(dict(html=html,themes=load_themes(),modules=api_modules()['modules'])),text=True,capture_output=True,timeout=60)
    assert result.returncode==0,result.stdout+'\n'+result.stderr
    assert 'PASS: shared Save/Load' in result.stdout
