"""Public nginx must permit the same file size as the Dashboard application."""
import importlib.util
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def load(name):
    spec=importlib.util.spec_from_file_location('upload_'+name,ROOT/'scripts/deployment'/f'{name}.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_new_install_and_existing_public_one_megabyte_limit(tmp_path):
    provision=load('provision');configure=load('configure_client_ip').configure
    fresh=provision.nginx_config('example.com',public_tls=True)
    assert 'client_max_body_size 1m;' not in fresh
    # Reproduce the exact previous public configuration that caused 2 MiB files
    # to fail before reaching the tested ASGI application.
    old=fresh.replace('client_max_body_size 30m;','client_max_body_size 1m;')
    path=tmp_path/'nginx.conf';path.write_text(old)
    configure(path);updated=path.read_text();configure(path);assert path.read_text()==updated
    blocks=re.findall(r'location / \{[^{}]*\}',updated)
    dashboards=[block for block in blocks if 'proxy_pass http://127.0.0.1:8020;' in block]
    assert len(dashboards)==2
    for block in dashboards:assert block.count('client_max_body_size 30m;')==1
    for block in blocks:
        if 'proxy_pass' in block and '8020' not in block:assert 'client_max_body_size' not in block
    assert 'configure_client_ip.py' in (ROOT/'scripts/deployment/update_dashboard.sh').read_text()
