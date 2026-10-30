"""Drive the actual account UI in the host Chromium browser."""
import json
import os
from pathlib import Path
import subprocess

import pytest
from dashboard.app import create_app, load_themes, api_modules


def test_account_execution_ui_in_chromium(tmp_path):
    if os.environ.get('DASHBOARD_SKIP_BROWSER')=='1':
        pytest.skip('Explicit unit-only run excludes browser validation')
    app=create_app(credential_path=tmp_path/'unused',upstream_factory=lambda owner,token:{})
    html=next(route.endpoint() for route in app.routes if getattr(route,'path',None)=='/')
    script=Path(__file__).resolve().parents[1]/'browser-tests/check.cjs'
    result=subprocess.run(['node',str(script)],input=json.dumps({'html':html,'themes':load_themes(),'modules':api_modules()['modules'],
                                         'layoutScreenshot':os.environ.get('DASHBOARD_LAYOUT_SCREENSHOT')}),
        text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
    assert result.returncode==0,result.stdout+'\n'+result.stderr
    assert 'PASS: Chromium' in result.stdout
