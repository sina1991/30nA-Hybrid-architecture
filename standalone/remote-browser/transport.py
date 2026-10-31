"""Bounded HTTP/WebSocket forwarding to an explicit, trusted local GUI target."""
import asyncio
from aiohttp import web,ClientSession,ClientTimeout,WSMsgType

HOP={'connection','upgrade','keep-alive','proxy-authenticate','proxy-authorization','te','trailer','transfer-encoding','host','cookie','authorization'}


async def forward(request,target):
    headers={k:v for k,v in request.headers.items() if k.lower() not in HOP}
    if request.headers.get('Upgrade','').lower()=='websocket':
        protocols=tuple(p.strip() for p in request.headers.get('Sec-WebSocket-Protocol','').split(',') if p.strip())
        for key in list(headers):
            if key.lower().startswith('sec-websocket-'):headers.pop(key)
        async with ClientSession(timeout=ClientTimeout(total=None,sock_connect=10)) as client:
            async with client.ws_connect(target,headers=headers,protocols=protocols,max_msg_size=16*1024*1024,autoping=True) as upstream:
                downstream=web.WebSocketResponse(protocols=(upstream.protocol,) if upstream.protocol else (),max_msg_size=16*1024*1024)
                await downstream.prepare(request)
                async def relay(source,destination):
                    async for message in source:
                        if message.type==WSMsgType.BINARY:await destination.send_bytes(message.data)
                        elif message.type==WSMsgType.TEXT:await destination.send_str(message.data)
                        elif message.type in (WSMsgType.CLOSE,WSMsgType.ERROR):break
                tasks=[asyncio.create_task(relay(upstream,downstream)),asyncio.create_task(relay(downstream,upstream))]
                try:await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
                finally:
                    for task in tasks:task.cancel()
                    await asyncio.gather(*tasks,return_exceptions=True)
                    await downstream.close()
                return downstream
    async with ClientSession(timeout=ClientTimeout(total=None,sock_connect=10,sock_read=60),auto_decompress=False) as client:
        async with client.request(request.method,target,headers=headers,data=request.content,allow_redirects=False) as upstream:
            result=web.StreamResponse(status=upstream.status,headers={k:v for k,v in upstream.headers.items() if k.lower() not in HOP|{'set-cookie','content-length'}})
            result.headers['Cache-Control']='no-store'
            await result.prepare(request)
            async for chunk in upstream.content.iter_chunked(65536):await result.write(chunk)
            await result.write_eof();return result
