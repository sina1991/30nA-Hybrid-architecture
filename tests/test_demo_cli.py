"""Terminal entrypoints use the same demo ledger and accept PIN on stdin."""
import json
import os
from pathlib import Path
import subprocess
import sys
from modules import demo_trading

ROOT=Path(__file__).resolve().parents[1]


def run(args,root,data=None):
    env={**os.environ,'DASHBOARD_MODULE_STATE_DIR':str(root)}
    return subprocess.run([sys.executable,*args],input=json.dumps(data) if data is not None else None,text=True,capture_output=True,env=env)


def test_standalone_account_and_reports(tmp_path):
    result=run([str(ROOT/'modules/demo-account/module.py'),'--owner','fixture','--slot','cli','--input','-'],tmp_path,{'action':'create','name':'CLI','initial_balance':5000,'tradePIN':'0123'})
    assert result.returncode==0,result.stderr
    account=json.loads(result.stdout)['account'];assert account['balance']==5000 and 'pin_hash' not in account
    result=run([str(ROOT/'30na'),'modules','run','demo-reports','--owner','fixture','--slot','report','--input','{}'],tmp_path)
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)['trades']==0
    missing=run([str(ROOT/'modules/demo-reports/module.py'),'--owner','another','--slot','cli'],tmp_path)
    assert missing.returncode==2 and 'Traceback' not in missing.stderr


def test_bot_module_uses_simple_action_contract_and_real_quote_fixture(tmp_path):
    env={**os.environ,'DASHBOARD_MODULE_STATE_DIR':str(tmp_path)}
    # Seed a separate disposable market using the same source schema.
    code="""import time
from market_data.data import connect
q=connect()
with q:
 q.execute('INSERT INTO candles(time,open,high,low,close,is_open) VALUES(?,?,?,?,?,?)',(int(time.time())//60*60,2000,2000,2000,2000,1))
 q.execute(\"INSERT OR REPLACE INTO collector_status VALUES('last_success',?)\",(str(time.time()),))
q.close()
"""
    subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=env,check=True)
    created=run([str(ROOT/'modules/demo-account/module.py'),'--owner','fixture','--slot','cli','--input','-'],tmp_path,{'action':'create','name':'CLI','initial_balance':1000,'tradePIN':'0123'})
    assert created.returncode==0
    request={'ACTION':'BUY','sl':1990,'tp':2010,'tradePIN':'0123','request_id':'cli-demo-order'}
    result=run([str(ROOT/'modules/demo-bot/module.py'),'--owner','fixture','--slot','bot-cli','--input','-'],tmp_path,request)
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)['trade']['status']=='open'
    replay=run([str(ROOT/'modules/demo-bot/module.py'),'--owner','fixture','--slot','bot-cli','--input','-'],tmp_path,request)
    assert json.loads(replay.stdout)['replayed']
    assert 'tradePIN' not in result.stdout


def test_media_descriptors_run_without_browser(tmp_path):
    for kind,url,expected in [('media-image','https://example.com/pic.png','image'),('media-audio','https://example.com/audio.mp3','audio'),('media-video','https://example.com/movie.mp4','video')]:
        result=run([str(ROOT/'modules'/kind/'module.py'),'--input','-'],tmp_path,{'settings':{'url':url}})
        assert result.returncode==0,result.stderr
        assert json.loads(result.stdout)['kind']==expected
