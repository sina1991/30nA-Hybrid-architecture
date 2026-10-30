"""Exercise password sign-in and chat rendering in Chromium."""
import json
from pathlib import Path
import subprocess
from dashboard.app import create_app, load_themes, api_modules


def test_password_login_and_public_chat(tmp_path):
    app = create_app(credential_path=tmp_path/'unused', upstream_factory=lambda owner,token:{})
    html = next(route.endpoint() for route in app.routes if getattr(route,'path',None)=='/')
    script = Path(__file__).resolve().parents[1] / 'units/consumers/dashboard-core/browser-tests/accounts_chat.cjs'
    result = subprocess.run(['node',str(script)],input=json.dumps({'html':html,'themes':load_themes(),'modules':api_modules()['modules']}),
                            text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45)
    assert result.returncode == 0, result.stdout + '\n' + result.stderr
    assert 'PASS: password login and public/private chat' in result.stdout
