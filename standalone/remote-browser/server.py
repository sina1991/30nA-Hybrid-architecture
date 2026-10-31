"""Independent password login and disposable browser sessions. No project imports."""
import asyncio
from collections import OrderedDict
import hashlib
import hmac
import json
import secrets
import ssl
import os
import socket
import signal
import time
from aiohttp import web,WSMsgType,ClientError
from runtime import Runtime,CapacityError
from transport import forward
from ui import LOGIN,viewer

COOKIE='__Secure-remote-browser'


def password_hash(password,salt):
    return hashlib.scrypt(password.encode('utf8'),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()


def username(value):
    return value.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩','01234567890123456789')).strip() if isinstance(value,str) else ''


def create_app(config,runtime=None,recover=True,idle_callback=None):
    engine=runtime or Runtime(config);sessions={};attempts=OrderedDict();lock=asyncio.Lock();verification=asyncio.Semaphore(2)
    app=web.Application(client_max_size=2048)
    origin=config['origin'];limit=config.get('max_sessions',1);idle_since=time.monotonic()
    def check_origin(request):
        if request.headers.get('Origin')!=origin:raise web.HTTPForbidden(text='Invalid origin')
    def authorized(request):
        key=request.cookies.get(COOKIE,'');session=sessions.get(key)
        if not session or session.get('closing') or session['expires']<time.monotonic():raise web.HTTPUnauthorized()
        return key,session
    async def close(key):
        nonlocal idle_since
        session=sessions.get(key)
        if not session or session.get('closing'):return
        session['closing']=True
        try:
            starting=session.get('startup_task')
            if session.get('runtime') is None and starting and starting is not asyncio.current_task() and not starting.done():
                starting.cancel();await asyncio.gather(starting,return_exceptions=True)
            if session.get('lease'):await session['lease'].close()
            if session.get('runtime'):await engine.stop(session['runtime'])
        finally:
            sessions.pop(key,None)
            if not sessions:idle_since=time.monotonic()
    async def index(request):
        nonlocal idle_since
        idle_since=time.monotonic()
        return web.Response(text=LOGIN,content_type='text/html',headers={'Cache-Control':'no-store','Referrer-Policy':'no-referrer'})
    async def login(request):
        nonlocal idle_since
        idle_since=time.monotonic()
        check_origin(request)
        peer=request.remote or 'unknown';now=time.monotonic()
        history=attempts.setdefault(peer,[]);history[:]=[stamp for stamp in history if now-stamp<900]
        if len(history)>=5:return web.json_response({'error':'Too many attempts. Try later.'},status=429)
        history.append(now);attempts.move_to_end(peer)
        while len(attempts)>256:attempts.popitem(last=False)
        try:data=await request.json()
        except (ValueError,UnicodeError):return web.json_response({'error':'Invalid credentials'},status=401)
        if not isinstance(data,dict) or set(data)!={'username','password'} or not isinstance(data['password'],str) or len(data['password'])>128:return web.json_response({'error':'Invalid credentials'},status=401)
        user=username(data['username']);record=config['users'].get(user)
        # Hash even unknown users; raw password, including trailing spaces, is preserved.
        sample=record or config['users']['1']
        if verification.locked():return web.json_response({'error':'Try again shortly.'},status=429)
        async with verification:digest=await asyncio.to_thread(password_hash,data['password'],sample['salt'])
        if record is None or not hmac.compare_digest(digest,record['hash']):return web.json_response({'error':'Invalid credentials'},status=401)
        attempts.pop(peer,None)
        async with lock:
            if any(s['user']==user for s in sessions.values()) or len(sessions)>=limit:return web.json_response({'error':'Browser is in use. Try again after it closes.'},status=409)
            key=secrets.token_urlsafe(32);sessions[key]={'user':user,'runtime':None,'nonce':secrets.token_hex(24),'lease':None,'expires':now+3600,'seen':time.monotonic()}
        sessions[key]['startup_task']=asyncio.current_task()
        try:
            sessions[key]['runtime']=await engine.launch(user)
            sessions[key]['seen']=time.monotonic()
        except asyncio.CancelledError:
            await close(key);raise
        except CapacityError:
            await close(key);return web.json_response({'error':'Not enough free memory to start the browser safely.'},status=503)
        except (RuntimeError,OSError,asyncio.TimeoutError) as error:
            print('Remote browser startup failed: '+type(error).__name__,flush=True)
            await close(key);return web.json_response({'error':'Browser could not start. Contact the server operator.'},status=503)
        attempts.pop(peer,None)
        response=web.json_response({'ready':True})
        response.set_cookie(COOKIE,key,secure=True,httponly=True,samesite='Strict',path='/rb/',max_age=3600)
        response.headers['Cache-Control']='no-store';return response
    async def view(request):
        try:key,session=authorized(request)
        except web.HTTPUnauthorized:raise web.HTTPFound('/rb/')
        return web.Response(text=viewer(session['nonce']),content_type='text/html',headers={'Cache-Control':'no-store','Referrer-Policy':'no-referrer','X-Frame-Options':'DENY'})
    async def lease(request):
        check_origin(request);key,session=authorized(request)
        if request.match_info['nonce']!=session['nonce'] or session['lease'] is not None:raise web.HTTPForbidden()
        ws=web.WebSocketResponse(heartbeat=10,max_msg_size=64);await ws.prepare(request);session['lease']=ws
        try:
            async for message in ws:
                if message.type==WSMsgType.TEXT and message.data=='alive':session['seen']=time.monotonic()
                else:break
        finally:
            session['lease']=None
            await close(key)
        return ws
    async def desktop(request):
        key,session=authorized(request)
        if not session['runtime'] or session.get('closing'):raise web.HTTPUnauthorized()
        if request.headers.get('Upgrade','').lower()=='websocket':check_origin(request)
        target='http://127.0.0.1:'+str(session['runtime']['port'])+request.rel_url.raw_path_qs
        try:return await forward(request,target)
        except (OSError,asyncio.TimeoutError,ClientError):raise web.HTTPBadGateway() from None
    async def reap():
        while True:
            await asyncio.sleep(5);now=time.monotonic()
            if idle_callback and not sessions and now-idle_since>config.get('idle_exit_seconds',30):idle_callback();return
            for key,session in list(sessions.items()):
                if session['runtime'] and ((session['lease'] is None and now-session['seen']>35) or now>session['expires']):await close(key)
    async def start(app):
        if recover:await engine.recover()
        app['reaper']=asyncio.create_task(reap())
    async def stop(app):
        app['reaper'].cancel();await asyncio.gather(app['reaper'],return_exceptions=True)
        for key in list(sessions):await close(key)
    async def root(request):raise web.HTTPFound('/rb/')
    async def private_headers(request,response):
        response.headers['Cache-Control']='no-store';response.headers['Referrer-Policy']='no-referrer';response.headers['X-Content-Type-Options']='nosniff'
        if request.path.startswith('/rb/desktop/'):response.headers['Content-Security-Policy']="frame-ancestors 'self'"
    app.on_response_prepare.append(private_headers)
    app.router.add_get('/',root);app.router.add_get('/rb/',index);app.router.add_post('/rb/login',login);app.router.add_get('/rb/viewer',view)
    app.router.add_get('/rb/lease/{nonce}',lease);app.router.add_route('*','/rb/desktop/{tail:.*}',desktop)
    app.on_startup.append(start);app.on_shutdown.append(stop)
    app['sessions']=sessions
    return app


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);args=parser.parse_args()
    with open(args.config) as stream:config=json.load(stream)
    activated=os.environ.get('LISTEN_PID')==str(os.getpid()) and os.environ.get('LISTEN_FDS')=='1'
    listener=socket.socket(fileno=3) if activated else None
    async def serve():
        stop_event=asyncio.Event();loop=asyncio.get_running_loop()
        for sig in (signal.SIGTERM,signal.SIGINT):loop.add_signal_handler(sig,stop_event.set)
        tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);tls.minimum_version=ssl.TLSVersion.TLSv1_2;tls.load_cert_chain(config['cert'],config['key'])
        runner=web.AppRunner(create_app(config,idle_callback=stop_event.set if activated else None),access_log=None)
        await runner.setup()
        try:
            site=web.SockSite(runner,listener,ssl_context=tls) if activated else web.TCPSite(runner,config.get('bind','0.0.0.0'),config.get('port',9443),ssl_context=tls)
            await site.start();await stop_event.wait()
        finally:await runner.cleanup()
    asyncio.run(serve())
