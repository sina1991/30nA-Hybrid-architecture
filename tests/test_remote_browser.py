"""Independent authentication, lifecycle, fixed proxy target and network policy."""
import asyncio
import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch,AsyncMock
import pytest
pytest.importorskip('aiohttp')
from aiohttp import web,WSServerHandshakeError
from aiohttp.test_utils import TestClient,TestServer

ROOT=Path(__file__).resolve().parents[1]
SERVICE=ROOT/'standalone/remote-browser'


def load():
    sys.path.insert(0,str(SERVICE))
    try:
        spec=importlib.util.spec_from_file_location('independent_browser_server',SERVICE/'server.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
    finally:sys.path.pop(0)


server=load()


def config(limit=1):
    salt='aa'*16;digest=server.password_hash('fixture-password ',salt)
    return {'installation':'1234567890abcdef','origin':'https://browser.example:9443','hostname':'browser.example',
            'users':{str(i):{'salt':salt,'hash':digest} for i in range(1,10)},'max_sessions':limit}


class Runtime:
    def __init__(self,port=1):self.started=[];self.stopped=[];self.port=port
    async def recover(self):pass
    async def launch(self,user):self.started.append(user);return {'port':self.port,'user':user}
    async def stop(self,item):self.stopped.append(item['user'])


async def login(client,user='1',password='fixture-password '):
    return await client.post('/rb/login',json={'username':user,'password':password},headers={'Origin':'https://browser.example:9443'})


def test_separate_login_exact_password_limit_and_explicit_origin():
    async def run():
        runtime=Runtime();client=TestClient(TestServer(server.create_app(config(),runtime)))
        await client.start_server()
        try:
            assert (await client.get('/rb/')).status==200 and not runtime.started
            assert (await client.get('/rb/desktop/')).status==401
            assert (await client.post('/rb/login',json={'username':'1','password':'fixture-password '})).status==403
            assert (await login(client,password='fixture-password')).status==401
            response=await login(client);assert response.status==200
            cookie=response.cookies[server.COOKIE];assert cookie['secure'] and cookie['httponly'] and cookie['path']=='/rb/' and cookie['samesite']=='Strict'
            assert (await login(client,user='۲')).status==409
            assert runtime.started==['1']
            # Other project session/token formats have no authority in this service.
            assert (await client.get('/rb/desktop/',headers={'Authorization':'Bearer fixture-project-token'})).status==401
        finally:await client.close()
        assert runtime.stopped==['1']
    asyncio.run(run())


def test_nine_usernames_and_rate_limit_without_executing_browser():
    assert [server.username(chr(0x6f0+i)) for i in range(1,10)]==[str(i) for i in range(1,10)]
    async def run():
        runtime=Runtime();client=TestClient(TestServer(server.create_app(config(),runtime)));await client.start_server()
        try:
            for _ in range(5):assert (await login(client,user='10')).status==401
            assert (await login(client)).status==429
            assert runtime.started==[]
        finally:await client.close()
    asyncio.run(run())


def test_websocket_disconnect_stops_only_its_browser_and_nonce_is_account_bound():
    async def run():
        runtime=Runtime();app=server.create_app(config(2),runtime);client=TestClient(TestServer(app));await client.start_server()
        try:
            one=await login(client,'1');two=await login(client,'2')
            token1=one.cookies[server.COOKIE].value;token2=two.cookies[server.COOKIE].value
            nonce1=app['sessions'][token1]['nonce'];nonce2=app['sessions'][token2]['nonce']
            headers={'Origin':config()['origin'],'Cookie':server.COOKIE+'='+token1}
            with pytest.raises(WSServerHandshakeError) as denied:await client.ws_connect('/rb/lease/'+nonce2,headers=headers)
            assert denied.value.status==403
            ws=await client.ws_connect('/rb/lease/'+nonce1,headers=headers);await ws.send_str('alive');await ws.close()
            for _ in range(20):
                if runtime.stopped:break
                await asyncio.sleep(.01)
            assert runtime.stopped==['1'] and token2 in app['sessions'] and token1 not in app['sessions']
        finally:await client.close()
        assert sorted(runtime.stopped)==['1','2']
    asyncio.run(run())


def test_gui_proxy_strips_credentials_and_streams_websocket():
    async def run():
        received=[]
        async def gui(request):
            received.append(dict(request.headers))
            if request.headers.get('Upgrade','').lower()=='websocket':
                ws=web.WebSocketResponse();await ws.prepare(request)
                async for message in ws:await ws.send_str(message.data)
                return ws
            return web.Response(text='GUI',headers={'Set-Cookie':'untrusted=1'})
        upstream=web.Application();upstream.router.add_route('*','/{tail:.*}',gui);up=TestServer(upstream);await up.start_server()
        runtime=Runtime(up.port);client=TestClient(TestServer(server.create_app(config(),runtime)));await client.start_server()
        try:
            response=await login(client);token=response.cookies[server.COOKIE].value;headers={'Cookie':server.COOKIE+'='+token,'Authorization':'Bearer private-project-token','Origin':config()['origin']}
            response=await client.get('/rb/desktop/',headers=headers)
            assert response.status==200 and await response.text()=='GUI' and not response.cookies
            ws=await client.ws_connect('/rb/desktop/ws',headers=headers);await ws.send_str('hello');assert (await ws.receive()).data=='hello';await ws.close()
            for request in received:assert not {'Cookie','Authorization'} & request.keys()
        finally:await client.close();await up.close()
    asyncio.run(run())


def test_pinned_proxy_rejects_private_and_mixed_dns_results():
    sys.path.insert(0,str(SERVICE))
    try:import egress
    finally:sys.path.pop(0)
    async def run():
        loop=asyncio.get_running_loop()
        for address in ('127.0.0.1','169.254.169.254','10.0.0.1','172.18.0.1','192.168.1.1','224.0.0.1'):
            with patch.object(loop,'getaddrinfo',AsyncMock(return_value=[(2,1,6,'',(address,443))])):
                with pytest.raises(ValueError):await egress.public_addresses('example.com')
        with patch.object(loop,'getaddrinfo',AsyncMock(return_value=[(2,1,6,'',('8.8.8.8',443))])):assert await egress.public_addresses('example.com')==['8.8.8.8']
    asyncio.run(run())


def test_configure_uses_private_file_and_all_nine_accounts(tmp_path):
    sys.path.insert(0,str(SERVICE))
    try:
        spec=importlib.util.spec_from_file_location('independent_browser_setup',SERVICE/'configure.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    finally:sys.path.pop(0)
    path=tmp_path/'config.json';cfg=module.configure(path,'browser.example','image','proxy','cert','key',password='fixture-password ')
    assert set(cfg['users'])==set('123456789') and path.stat().st_mode&0o777==0o600
    assert 'fixture-password' not in path.read_text()
    for item in cfg['users'].values():assert item['hash']==server.password_hash('fixture-password ',item['salt'])


def test_connect_proxy_streams_only_after_validating_and_pinning_target(monkeypatch):
    sys.path.insert(0,str(SERVICE))
    try:import egress
    finally:sys.path.pop(0)
    async def run():
        async def echo(reader,writer):
            try:writer.write(await reader.readexactly(5));await writer.drain()
            finally:writer.close();await writer.wait_closed()
        target=await asyncio.start_server(echo,'127.0.0.1',0);port=target.sockets[0].getsockname()[1]
        real_connect=asyncio.open_connection;connected=[]
        async def connect(host,value):connected.append((host,value));return await real_connect('127.0.0.1',port)
        with patch.object(egress,'public_addresses',AsyncMock(return_value=['8.8.8.8'])),patch.object(egress.asyncio,'open_connection',connect):
            proxy=await asyncio.start_server(egress.tunnel,'127.0.0.1',0)
            try:
                reader,writer=await real_connect('127.0.0.1',proxy.sockets[0].getsockname()[1])
                writer.write(b'CONNECT example.com:443 HTTP/1.1\r\nHost: example.com\r\n\r\n');await writer.drain()
                assert b'200 Connection Established' in await reader.readuntil(b'\r\n\r\n')
                writer.write(b'hello');await writer.drain();assert await reader.readexactly(5)==b'hello'
                writer.close();await writer.wait_closed();assert connected==[('8.8.8.8',443)]
            finally:proxy.close();await proxy.wait_closed();target.close();await target.wait_closed()
    asyncio.run(run())


def test_idle_controller_requests_shutdown_without_starting_chrome():
    async def run():
        done=asyncio.Event();runtime=Runtime();cfg=config();cfg['idle_exit_seconds']=.01
        client=TestClient(TestServer(server.create_app(cfg,runtime,idle_callback=done.set)))
        await client.start_server()
        try:
            assert (await client.get('/rb/')).status==200
            await asyncio.wait_for(done.wait(),6)
            assert runtime.started==[]
        finally:await client.close()
    asyncio.run(run())


def test_shutdown_cancels_inflight_browser_launch_and_clears_reservation():
    async def run():
        entered=asyncio.Event();cancelled=asyncio.Event()
        class Slow(Runtime):
            async def launch(self,user):
                entered.set()
                try:await asyncio.Event().wait()
                finally:cancelled.set()
        app=server.create_app(config(),Slow());client=TestClient(TestServer(app));await client.start_server()
        pending=asyncio.create_task(login(client))
        try:
            await asyncio.wait_for(entered.wait(),2)
            await asyncio.wait_for(client.server.close(),3)
            assert cancelled.is_set() and app['sessions']=={}
        finally:
            pending.cancel();await asyncio.gather(pending,return_exceptions=True);await client.close()
    asyncio.run(run())
