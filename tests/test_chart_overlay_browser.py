"""Actual price chart layers and profile enable/disable in Chromium."""
import json
from pathlib import Path
import subprocess
from datetime import datetime
from dashboard.app import create_app,load_themes,api_modules
from modules import technical


def test_actual_chart_overlays_and_profile_controls(tmp_path):
    app=create_app(credential_path=tmp_path/'unused',upstream_factory=lambda owner,token:{})
    html=next(route.endpoint() for route in app.routes if getattr(route,'path',None)=='/')
    stamp=lambda day:int(datetime.fromisoformat(day).timestamp())
    start=stamp('2026-03-16T13:30:00+00:00');now=start+3600
    candles=[dict(time=start+offset+i*60,open=100,high=110,low=90,close=105,is_open=False) for offset in (-3*86400,0) for i in range(40)]
    cfg=dict(winter_utc_minutes=0,windows=[dict(name='Example session',start='13:30',end='14:00',grade='A')],points=[dict(time='13:45')],clock_size=120)
    results={kind:technical.run(kind,dict(price=105) if kind=='round-levels' else dict(now=now,candles=candles,settings=cfg) if kind.startswith('session-') else dict(now=now,candles=candles,settings={'session_start':'13:30','session_end':'14:00'}) if kind=='previous-day-session-levels' else dict(now=now,candles=candles)) for kind in technical.KINDS}
    profiles=[dict(id='profile-'+kind,name=kind,type=kind,parameters=results[kind]['settings'],enabled=True) for kind in technical.KINDS]
    market=dict(symbol='XAUUSD',interval='1m',candles=candles,moving_average={'points':[]},series=[],indicators={},last_success=now,collector_error=None)
    script=Path(__file__).resolve().parents[1]/'units/consumers/dashboard-core/browser-tests/chart_overlays.cjs'
    result=subprocess.run(['node',str(script)],input=json.dumps(dict(html=html,themes=load_themes(),modules=api_modules()['modules'],results=results,profiles=profiles,market=market,defaults=technical.DEFAULTS)),text=True,capture_output=True,timeout=60)
    assert result.returncode==0,result.stdout+'\n'+result.stderr
    assert 'PASS: actual chart overlays' in result.stdout
