"""Installer regression: identities, safe resumption, generated routes and gates."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess

import httpx
import pytest

ROOT=Path(__file__).resolve().parents[4]


def load(name):
    spec=importlib.util.spec_from_file_location('installer_'+name,ROOT/'scripts/deployment'/f'{name}.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


provision=load('provision')
verification=load('verify_install')
IMAGE='sha256:'+'a'*64


def test_provision_retains_credentials_and_binds_every_hop_to_customer(tmp_path):
    config=tmp_path/'etc';nginx=tmp_path/'nginx.conf'
    kwargs=dict(domain='dashboard.example.com',image=IMAGE,sandbox_uid=1001,
                service_gid=os.getgid(),sandbox_gid=os.getgid(),owner_uid=os.getuid())
    provision.provision(config,nginx,**kwargs)
    original=(config/'installer-secrets.json').read_text()
    provision.provision(config,nginx,public_tls=True,**kwargs)
    assert (config/'installer-secrets.json').read_text()==original
    tokens=json.loads(original)
    digest=provision.hashlib.sha256
    for service,token in [('dashboard',tokens['customer']),('manager',tokens['customer']),('runtime',tokens['manager_runtime'])]:
        incoming=json.loads((config/f'{service}-incoming.json').read_text())
        assert incoming=={digest(token.encode()).hexdigest():'customer'}
    for path in config.iterdir():
        assert path.stat().st_mode & 0o007 ==0
        if path.name.endswith('.env'):assert all(token not in path.read_text() for token in tokens.values())
    assert (config/'customer-token').stat().st_mode & 0o077 ==0
    outgoing=json.loads((config/'manager-runtime.json').read_text())['customer']
    assert outgoing['token']==tokens['manager_runtime'] and outgoing['ca_file']=='/etc/30na/ca/internal.crt'
    assert tokens['customer'] not in nginx.read_text()
    assert 'listen 127.0.0.1:18446 ssl' in nginx.read_text()
    assert 'listen 18443' not in nginx.read_text()  # Private upstreams stay private.
    assert '/etc/letsencrypt/live/30na-dashboard/fullchain.pem' in nginx.read_text()
    assert f'DOCKER_HOST=unix:///run/user/1001/docker.sock' in (config/'worker-runtime.env').read_text()


@pytest.mark.parametrize('domain',['127.0.0.1','a.example.com; touch /tmp/no','https://example.com','x\nserver {}','-bad.example.com'])
def test_untrusted_installer_values_cannot_generate_config(domain):
    with pytest.raises(ValueError):provision.validate(domain,IMAGE,1001)


def test_partial_credential_state_is_not_silently_rotated(tmp_path):
    (tmp_path/'customer-token').write_text('existing')
    with pytest.raises(ValueError,match='Partial'):
        provision.provision(tmp_path,tmp_path/'nginx',domain='a.example.com',image=IMAGE,
            sandbox_uid=1001,service_gid=os.getgid(),sandbox_gid=os.getgid(),owner_uid=os.getuid())
    assert (tmp_path/'customer-token').read_text()=='existing'


def test_verification_rejects_false_success_and_uses_bff_routes():
    submissions=[]
    def route(request):
        assert request.headers['authorization']=='Bearer ephemeral-installer-token'
        assert request.url.path.startswith('/api/upstreams/')
        if request.method=='POST':
            submissions.append(json.loads(request.content))
            payload={'execution_id':str(len(submissions))}
        elif request.url.path.endswith('/1'):
            payload={'status':'succeeded','result':{'result':{'count':3,'sum':60,'min':10,'max':30,'mean':20}}}
        else:payload={'status':'failed','result':{'error':{'code':'EXECUTION_ERROR'}}}
        return httpx.Response(200,json={'contract_version':'1.0.0','payload':payload})
    with httpx.Client(base_url='https://localhost:18446',transport=httpx.MockTransport(route),
                      headers={'Authorization':'Bearer ephemeral-installer-token'}) as client:
        assert verification.verify(verification.DashboardAPI(client))
    assert len(submissions)==2 and submissions[0]['idempotency_key']!=submissions[1]['idempotency_key']
    class WrongResult:
        def post(self,*args):return {'execution_id':'1'}
        def get(self,*args):return {'status':'succeeded','result':{'result':{'sum':0}}}
    with pytest.raises(RuntimeError,match='Unexpected demo result'):verification.verify(WrongResult())


def test_installer_shell_validation_and_help_do_not_provision():
    subprocess.run(['bash','-n',str(ROOT/'install.sh')],check=True)
    help_result=subprocess.run(['bash',str(ROOT/'install.sh'),'--help'],capture_output=True,text=True)
    assert help_result.returncode==0 and '--check-only' in help_result.stdout
    # Source functions only: no root, apt, daemon or filesystem provisioning.
    result=subprocess.run(['bash','-c','source "$1"; DOMAIN="bad;domain"; EMAIL="admin@example.com"; validate','probe',str(ROOT/'install.sh')],capture_output=True,text=True)
    assert result.returncode!=0
