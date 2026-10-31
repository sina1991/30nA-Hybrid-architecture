"""Resolve actual local Git history without invoking installer/systemd code."""
from pathlib import Path
import subprocess
import pytest

SCRIPT=Path(__file__).resolve().parents[1]/'scripts/deployment/update_dashboard.sh'


def git(path,*args):
    return subprocess.check_output(['git','-C',str(path),*args],text=True,stderr=subprocess.PIPE).strip()


@pytest.fixture
def history(tmp_path):
    origin=tmp_path/'origin';origin.mkdir()
    git(origin,'init','-b','main')
    (origin/'example').write_text('first')
    git(origin,'add','example')
    git(origin,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','first')
    first=git(origin,'rev-parse','HEAD')
    git(origin,'tag','v1.0')
    (origin/'example').write_text('second')
    git(origin,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-am','second')
    latest=git(origin,'rev-parse','HEAD')
    checkout=tmp_path/'checkout'
    subprocess.run(['git','clone','--quiet','--no-checkout',str(origin),str(checkout)],check=True)
    source=SCRIPT.read_text();start=source.index('resolve_dashboard_ref() {');end=source.index('\n}',start)+2
    helper=tmp_path/'resolve.sh';helper.write_text(source[start:end])
    return checkout,helper,first,latest


@pytest.mark.parametrize('name',['short','full','branch','tag'])
def test_resolves_commit_branch_and_tag(history,name):
    checkout,helper,first,latest=history
    ref={'short':first[:7],'full':first,'branch':'main','tag':'v1.0'}[name]
    result=subprocess.run(['bash','-c','source "$1"; resolve_dashboard_ref "$2" "$3"','test',str(helper),str(checkout),ref],text=True,capture_output=True)
    assert result.returncode==0,result.stderr
    assert result.stdout.strip()==(latest if name=='branch' else first)


def test_missing_short_commit_fails_instead_of_using_head(history):
    checkout,helper,_,_=history
    result=subprocess.run(['bash','-c','source "$1"; resolve_dashboard_ref "$2" "$3"','test',str(helper),str(checkout),'0000000'],text=True,capture_output=True)
    assert result.returncode!=0 and not result.stdout.strip()
