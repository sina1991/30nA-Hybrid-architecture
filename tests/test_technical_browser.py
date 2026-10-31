"""Targeted Chromium rendering and configuration checks for trusted indicators."""
import json
from pathlib import Path
import subprocess
from datetime import datetime
from dashboard.app import create_app,load_themes,api_modules
from modules import technical


def test_five_independent_indicators_in_chromium(tmp_path):
    app=create_app(credential_path=tmp_path/'unused',upstream_factory=lambda owner,token:{})
    html=next(route.endpoint() for route in app.routes if getattr(route,'path',None)=='/')
    stamp=lambda value:int(datetime.fromisoformat(value).timestamp())
    now=stamp('2026-03-16T13:45:00+00:00')
    candles=[dict(time=stamp(day),open=100,high=110,low=90,close=105) for day in ('2026-03-13T13:30:00+00:00','2026-03-13T16:30:00+00:00','2026-03-16T13:30:00+00:00')]
    schedule=dict(winter_utc_minutes=120,clock_change='Europe',reference_timezone='America/New_York',windows=[dict(name='Example NY open',start='09:30',end='10:00',grade='A')],points=[dict(time='10:00')])
    results={kind:technical.run(kind,dict(price=4000) if kind=='round-levels' else dict(now=now,candles=candles,settings=schedule) if kind in ('session-clock','session-windows') else dict(now=now,candles=candles)) for kind in technical.KINDS}
    script=Path(__file__).resolve().parents[1]/'units/consumers/dashboard-core/browser-tests/technical.cjs'
    result=subprocess.run(['node',str(script)],input=json.dumps(dict(html=html,themes=load_themes(),modules=api_modules()['modules'],defaults=technical.DEFAULTS,results=results)),text=True,capture_output=True,timeout=60)
    assert result.returncode==0,result.stdout+'\n'+result.stderr
    assert 'PASS: five independent indicators' in result.stdout
