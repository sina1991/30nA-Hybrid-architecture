"""Session-local GUI bridge and public-only pinned HTTP CONNECT egress.

The Chromium network is internal/isolated. Only this trusted sidecar has an
external interface; no Dashboard code, host path or Docker socket is mounted.
"""
import asyncio
import ipaddress
import os
import socket
from urllib.parse import urlsplit
from aiohttp import web,ClientError
from transport import forward


async def public_addresses(host):
    records=await asyncio.wait_for(asyncio.get_running_loop().getaddrinfo(host,443,family=socket.AF_INET,type=socket.SOCK_STREAM),8)
    addresses={item[4][0] for item in records}
    if not addresses:raise ValueError('No address')
    for value in addresses:
        ip=ipaddress.ip_address(value)
        if not ip.is_global or ip.is_multicast or ip.is_reserved:raise ValueError('Public addresses only')
    return sorted(addresses)


async def tunnel(reader,writer):
    remote=None
    try:
        raw=await asyncio.wait_for(reader.readuntil(b'\r\n\r\n'),10)
        if len(raw)>16384:raise ValueError('Headers too large')
        lines=raw.decode('latin1').split('\r\n');method,destination,version=lines[0].split(' ')
        if method=='CONNECT':
            host,port=destination.rsplit(':',1)
            if port!='443':raise ValueError('HTTPS port only')
            prefix=b''
        else:
            parsed=urlsplit(destination);host=parsed.hostname
            if parsed.scheme!='http' or not host or parsed.port not in (None,80) or parsed.username is not None:raise ValueError('Invalid HTTP target')
            port='80';path=parsed.path or '/'
            if parsed.query:path+='?'+parsed.query
            allowed=[]
            for line in lines[1:]:
                if not line:continue
                key,sep,value=line.partition(':')
                if not sep:raise ValueError('Invalid header')
                if key.lower() not in ('host','proxy-authorization','proxy-connection','connection'):allowed.append(line)
            prefix=(f'{method} {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n'+'\r\n'.join(allowed)+'\r\n\r\n').encode('latin1')
        if not host or len(host)>253 or any(c in host for c in '/\\@%\x00\r\n'):raise ValueError('Invalid host')
        if os.environ.get('DENY_ALL_EGRESS')=='1':raise ValueError('Public egress disabled')
        addresses=await public_addresses(host)
        denied=set()
        deny_host=os.environ.get('DENY_HOST','')
        if deny_host:
            if host.lower().rstrip('.')==deny_host.lower().rstrip('.'):raise ValueError('Protected host')
            try:denied=set(await public_addresses(deny_host))
            except (ValueError,OSError,asyncio.TimeoutError):pass
        if denied.intersection(addresses):raise ValueError('Protected server')
        upstream,remote=await asyncio.wait_for(asyncio.open_connection(addresses[0],int(port)),10)
        if method=='CONNECT':writer.write(b'HTTP/1.1 200 Connection Established\r\n\r\n')
        else:remote.write(prefix)
        await writer.drain()
        async def pipe(source,dest):
            while True:
                data=await asyncio.wait_for(source.read(65536),120)
                if not data:break
                dest.write(data);await dest.drain()
        tasks=[asyncio.create_task(pipe(reader,remote)),asyncio.create_task(pipe(upstream,writer))]
        try:await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
        finally:
            for task in tasks:task.cancel()
            await asyncio.gather(*tasks,return_exceptions=True)
    except (ValueError,OSError,asyncio.TimeoutError,asyncio.IncompleteReadError,asyncio.LimitOverrunError):
        try:writer.write(b'HTTP/1.1 403 Forbidden\r\nConnection: close\r\nContent-Length: 0\r\n\r\n');await writer.drain()
        except OSError:pass
    finally:
        for stream in (remote,writer):
            if stream:
                stream.close()
                try:await stream.wait_closed()
                except OSError:pass


async def start(app):
    app['proxy']=await asyncio.start_server(tunnel,'0.0.0.0',3128,limit=16384)


async def stop(app):
    app['proxy'].close();await app['proxy'].wait_closed()


def create_app():
    app=web.Application(client_max_size=16*1024*1024)
    async def gui(request):
        try:return await forward(request,'http://'+os.environ['BROWSER_HOST']+':3000'+request.rel_url.raw_path_qs)
        except (ClientError,OSError,asyncio.TimeoutError):raise web.HTTPBadGateway() from None
    app.router.add_route('*','/{tail:.*}',gui);app.on_startup.append(start);app.on_cleanup.append(stop)
    return app


if __name__=='__main__':web.run_app(create_app(),host='0.0.0.0',port=8080,access_log=None)
