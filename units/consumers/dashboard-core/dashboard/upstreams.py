"""Authenticated Dashboard BFF for explicit owner-scoped Manager operations."""
from uuid import UUID
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, Response, FileResponse
from pydantic import BaseModel, ConfigDict, Field
from worker_manager.api import RegisterBody, ConfigureBody
from worker_manager.http_common import ERROR_RESPONSES, envelope, identifier, owner_dependency
from public_api import ConsumerAPIError, _identifier
from modules.execution import run_module
from modules import slots, uploads, technical, chart_overlays, workspaces, client_ip, demo_trading, demo_components, media
from modules import slot_workers, indicator_profiles, signal_rules, accounts, chat_store
from market_data.data import chart as gold_chart
from market_data.data import indicator as market_indicator, database_table


class RunRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    input_payload: dict = Field(default_factory=dict)
    timeout_seconds: float = Field(default=30, gt=0, le=300, allow_inf_nan=False)
    idempotency_key: str = Field(min_length=1, max_length=256)


def create_router(credential_path, upstream_factory):
    """Authenticate before forwarding the caller's credential to configured services.

    No credential substitution, redirects, arbitrary proxy paths or source upload.
    Worker metadata mutations use the Manager schemas and caller identity.
    """
    router = APIRouter(prefix='/api/upstreams', responses=ERROR_RESPONSES)
    legacy_owner = owner_dependency(credential_path)

    def owner(request: Request):
        auth = request.headers.get('authorization', '')
        token = auth[7:] if auth.startswith('Bearer ') else ''
        try:
            identity = legacy_owner(request)
        except HTTPException as exc:
            if exc.status_code != 401 or not accounts.is_session_token(token): raise
            try: user = accounts.authenticate(token)
            except (OSError, sqlite3.Error): raise HTTPException(503, 'Identity configuration unavailable') from None
            if user is None: raise HTTPException(401, 'Unauthorized', headers={'WWW-Authenticate':'Bearer'})
            request.state.account_session = True
            return user['id']
        if identity == 'customer':
            import os
            from pathlib import Path
            database = Path(os.environ.get('DASHBOARD_MODULE_STATE_DIR', '/var/lib/30na/dashboard')) / 'accounts.sqlite3'
            if database.exists():
                try: existing = accounts.get_user(identity)
                except (OSError, sqlite3.Error): raise HTTPException(503, 'Identity configuration unavailable') from None
                if existing is not None and not existing['enabled']:
                    raise HTTPException(401, 'Unauthorized', headers={'WWW-Authenticate':'Bearer'})
        request.state.account_session = False
        return identity

    def admin_identity(request: Request, identity=Depends(owner)):
        if not request.state.account_session and identity == 'customer': return identity
        user = accounts.get_user(identity)
        if user is None or not user['enabled'] or user['role'] != 'admin':
            raise HTTPException(403, 'Administrator required')
        return identity
    routes = {'workers': ('worker-manager', '/api/v1/workers'),
              'executions': ('worker-manager', '/api/v1/executions'),
              'sources': ('code-manager', '/api/v1/sources')}

    def forward(request, identity, name, method, path, payload=None, status=200):
        credential = accounts.upstream_credential(identity) if request.state.account_session else request.headers['authorization'][7:]
        if credential is None:
            raise HTTPException(503, 'Separate Worker credentials are not provisioned for this account')
        adapters = upstream_factory(identity, credential)
        adapter = adapters.get(name)
        if adapter is None:
            raise HTTPException(503, 'Upstream is not configured')
        try:
            if method == 'GET': result = adapter.get(path)
            elif method == 'DELETE': result = adapter.delete(path)
            else: result = getattr(adapter, method.lower())(path, payload)
            response = JSONResponse(envelope(result), status_code=status)
        except ValueError:
            raise HTTPException(422, 'Invalid upstream request') from None
        except ConsumerAPIError as exc:
            code = exc.status if exc.status in (401, 403, 404, 409, 413, 422) else 503
            response = JSONResponse({'contract_version': '1.0.0', 'error': {
                'code': exc.code, 'message': 'Upstream request failed'}}, status_code=code)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    def worker_path(worker_id):
        try:
            identifier(worker_id)
            if '..' in worker_id: raise ValueError()
        except ValueError:
            raise HTTPException(422, 'Invalid worker identifier') from None
        return '/api/v1/workers/' + _identifier(worker_id)

    @router.post('/account/bootstrap')
    def account_bootstrap(body: dict, request: Request, identity=Depends(owner)):
        token = request.headers.get('authorization', '')[7:]
        if request.state.account_session or identity != 'customer': raise HTTPException(403, 'Legacy customer credential required')
        if set(body) != {'username','password'}: raise HTTPException(422, 'Invalid account')
        try: user = accounts.bootstrap_admin(body['username'], body['password'])
        except ValueError: raise HTTPException(422, 'Account cannot be initialized') from None
        response=JSONResponse(envelope({'user':user})); response.headers['Cache-Control']='no-store'; return response

    @router.post('/account/login')
    def account_login(body: dict):
        if set(body) != {'username','password'}: raise HTTPException(422, 'Invalid account')
        try: session=accounts.login(body['username'],body['password'])
        except ValueError: raise HTTPException(401, 'Invalid credentials') from None
        except (OSError,sqlite3.Error): raise HTTPException(503, 'Identity unavailable') from None
        response=JSONResponse(envelope(session)); response.headers['Cache-Control']='no-store'; return response

    @router.get('/account/me')
    def account_me(request: Request, identity=Depends(owner)):
        token=request.headers.get('authorization','')[7:]
        user=accounts.get_user(identity)
        response=JSONResponse(envelope({'user':user or {'id':identity,'username':identity,'role':'admin' if identity == 'customer' else 'user','enabled':True},
                                        'client_ip':client_ip.address(request), 'legacy':not request.state.account_session,'worker_access':not request.state.account_session or accounts.upstream_credential(identity) is not None}))
        response.headers['Cache-Control']='no-store'; return response

    @router.post('/account/logout')
    def account_logout(request: Request, identity=Depends(owner)):
        token=request.headers.get('authorization','')[7:]
        if request.state.account_session: accounts.logout(token)
        response=JSONResponse(envelope({'logged_out':True})); response.headers['Cache-Control']='no-store'; return response

    @router.get('/accounts')
    def account_users(identity=Depends(admin_identity)):
        response=JSONResponse(envelope({'users':accounts.list_users()})); response.headers['Cache-Control']='no-store'; return response

    @router.post('/accounts')
    def account_create(body: dict, identity=Depends(admin_identity)):
        if set(body) != {'username','password','role'}: raise HTTPException(422, 'Invalid account')
        try: user=accounts.create_user(body['username'],body['password'],body['role'])
        except ValueError: raise HTTPException(422, 'Account cannot be created') from None
        response=JSONResponse(envelope({'user':user})); response.headers['Cache-Control']='no-store'; return response

    @router.post('/accounts/{user_id}/enabled')
    def account_enable(user_id: str, body: dict, identity=Depends(admin_identity)):
        if set(body) != {'enabled'} or type(body['enabled']) is not bool: raise HTTPException(422, 'Invalid status')
        try: accounts.set_enabled(user_id, body['enabled'])
        except LookupError: raise HTTPException(404, 'Account not found') from None
        except ValueError: raise HTTPException(422, 'Account cannot be disabled') from None
        response=JSONResponse(envelope({'enabled':body['enabled']})); response.headers['Cache-Control']='no-store'; return response

    def upload_error(exc):
        status = 404 if isinstance(exc, LookupError) else 403 if isinstance(exc, PermissionError) else 413 if isinstance(exc, OverflowError) else 422 if isinstance(exc, ValueError) else 503
        raise HTTPException(status, {404:'File not found',403:'Account setup required',413:'File exceeds the upload size limit (binary: 20 MiB; legacy JSON: 512 KiB)',422:'Invalid upload',503:'Upload storage unavailable'}[status]) from None

    @router.get('/uploads')
    def upload_list(identity=Depends(owner)):
        try: items = uploads.list_files(identity)
        except (PermissionError, OSError, sqlite3.Error) as exc: upload_error(exc)
        return JSONResponse(envelope({'files':items,'max_bytes':uploads.MAX_BYTES}), headers={'Cache-Control':'no-store','Vary':'Authorization'})

    @router.post('/uploads')
    def upload_create(body: dict, identity=Depends(owner)):
        if set(body) != {'name','visibility','recipient','content'}: raise HTTPException(422, 'Invalid upload')
        try: item = uploads.create(identity, **body)
        except (ValueError, OverflowError, PermissionError, OSError, sqlite3.Error) as exc: upload_error(exc)
        return JSONResponse(envelope({'file':item}), headers={'Cache-Control':'no-store'})

    @router.post('/uploads/raw')
    async def upload_binary(request: Request, name: str, visibility: str, recipient: str | None = None, identity=Depends(owner)):
        if request.headers.get('content-type', '').split(';')[0] != 'application/octet-stream':
            raise HTTPException(422, 'Use application/octet-stream')
        data = bytearray()
        async for chunk in request.stream():
            if len(data) + len(chunk) > uploads.MAX_BYTES: raise HTTPException(413, 'File exceeds 20 MiB')
            data.extend(chunk)
        from starlette.concurrency import run_in_threadpool
        try: item = await run_in_threadpool(uploads.create_bytes, identity, name, visibility, recipient, bytes(data))
        except (ValueError, OverflowError, PermissionError, OSError, sqlite3.Error) as exc: upload_error(exc)
        return JSONResponse(envelope({'file':item}), headers={'Cache-Control':'no-store'})

    @router.post('/uploads/from-url')
    def upload_from_url(body: dict, identity=Depends(owner)):
        from modules import upload_download
        if set(body) != {'url','name','visibility','recipient'}: raise HTTPException(422, 'Invalid download request')
        try: item = upload_download.import_url(identity, **body)
        except upload_download.DownloadBusy: raise HTTPException(429, 'Download capacity is busy. Try again later.') from None
        except upload_download.DownloadError as exc: raise HTTPException(502, str(exc)) from None
        except (ValueError, OverflowError, PermissionError, OSError, sqlite3.Error) as exc: upload_error(exc)
        return JSONResponse(envelope({'file':item}), headers={'Cache-Control':'no-store'})

    @router.get('/uploads/{file_id}/content')
    def upload_download(file_id: str, identity=Depends(owner)):
        from urllib.parse import quote
        try: item = uploads.access(identity, file_id)
        except (LookupError, PermissionError, OSError, sqlite3.Error) as exc: upload_error(exc)
        return Response(item['content'], media_type='application/octet-stream', headers={
            'Content-Disposition': "attachment; filename=download; filename*=UTF-8''" + quote(item['name'], safe=''),
            'X-Content-Type-Options':'nosniff', 'Content-Security-Policy':"sandbox; default-src 'none'",
            'Cache-Control':'no-store', 'Vary':'Authorization'})

    @router.delete('/uploads/{file_id}')
    def upload_delete(file_id: str, identity=Depends(owner)):
        try: uploads.access(identity, file_id, delete=True)
        except (LookupError, PermissionError, OSError, sqlite3.Error) as exc: upload_error(exc)
        return JSONResponse(envelope({'deleted':True}), headers={'Cache-Control':'no-store'})

    @router.get('/chat/users')
    def chat_users(identity=Depends(owner)):
        if not accounts.get_user(identity): raise HTTPException(403, 'Account setup required')
        response=JSONResponse(envelope({'users':[{'id':u['id'],'username':u['username']} for u in accounts.list_users() if u['enabled'] and u['id'] != identity]}))
        response.headers['Cache-Control']='no-store'; return response

    @router.get('/chat/rooms')
    def chat_rooms(identity=Depends(owner)):
        try: result=chat_store.list_rooms(identity)
        except (PermissionError,ValueError): raise HTTPException(403, 'Account unavailable') from None
        response=JSONResponse(envelope({'rooms':result})); response.headers['Cache-Control']='no-store'; return response

    @router.get('/chat/requests')
    def chat_requests(identity=Depends(owner)):
        try: result=chat_store.list_requests(identity)
        except (PermissionError,ValueError): raise HTTPException(403, 'Account unavailable') from None
        response=JSONResponse(envelope({'requests':result})); response.headers['Cache-Control']='no-store'; return response

    @router.post('/chat/requests')
    def chat_request(body: dict, identity=Depends(owner)):
        if set(body) != {'recipient'}: raise HTTPException(422, 'Invalid request')
        try: result=chat_store.request_private(identity,body['recipient'])
        except PermissionError: raise HTTPException(403, 'Account unavailable') from None
        except ValueError: raise HTTPException(422, 'Request cannot be created') from None
        response=JSONResponse(envelope({'request':result})); response.headers['Cache-Control']='no-store'; return response

    @router.post('/chat/requests/{request_id}/respond')
    def chat_respond(request_id: str, body: dict, identity=Depends(owner)):
        if set(body) != {'accept'} or type(body['accept']) is not bool: raise HTTPException(422, 'Invalid response')
        try: result=chat_store.respond(identity,request_id,body['accept'])
        except LookupError: raise HTTPException(404, 'Request not found') from None
        except PermissionError: raise HTTPException(403, 'Account unavailable') from None
        except ValueError: raise HTTPException(422, 'Request cannot be resolved') from None
        response=JSONResponse(envelope({'request':result})); response.headers['Cache-Control']='no-store'; return response

    @router.get('/chat/rooms/{room_id}/messages')
    def chat_messages(room_id: str, limit: int = Query(default=50, ge=1, le=200), before: int | None = Query(default=None,gt=0), identity=Depends(owner)):
        try: result=chat_store.messages(identity,room_id,limit,before)
        except PermissionError: raise HTTPException(403, 'Room unavailable') from None
        except ValueError: raise HTTPException(422, 'Invalid room or pagination') from None
        response=JSONResponse(envelope({'messages':result})); response.headers['Cache-Control']='no-store'; return response

    @router.post('/chat/rooms/{room_id}/messages')
    def chat_send(room_id: str, body: dict, identity=Depends(owner)):
        if set(body) != {'text'}: raise HTTPException(422, 'Invalid message')
        try: result=chat_store.send(identity,room_id,body['text'])
        except PermissionError: raise HTTPException(403, 'Room unavailable') from None
        except ValueError: raise HTTPException(422, 'Invalid message') from None
        response=JSONResponse(envelope({'message':result})); response.headers['Cache-Control']='no-store'; return response

    @router.get('/market/candles')
    def market_candles(limit: int = Query(default=200, ge=1, le=1000),
                       period: int = Query(default=20, ge=1, le=500),
                       include_open: bool = True, end_time: int | None = Query(default=None, ge=0),
                       interval: str = '1m', include_indicators: bool = False, slot_id: str | None = None, identity=Depends(owner)):
        try:
            profiles = indicator_profiles.list_profiles(identity)
            if slot_id is not None:
                config=slots.binding(identity,slot_id)
                if not config or config['module_id']!='gold-chart':raise HTTPException(404,'Chart slot not found')
                meta=slots.change(identity,'slot-meta',slot_id,None,lambda old:(old,False))
                if meta is None:raise HTTPException(404,'Chart slot not found')
                visibility=meta.get('profile_visibility',{})
                profiles=[{**p,'enabled':visibility.get(p['id'],p['enabled'])} for p in profiles]
            profiles = [profile for profile in profiles if profile['enabled']]
            result = gold_chart(limit=limit, period=period, include_open=include_open, end_time=end_time, interval=interval, include_indicators=include_indicators, profiles=[profile for profile in profiles if profile['type'] not in technical.KINDS] if include_indicators else None)
            if include_indicators: result['technical_overlays']=chart_overlays.calculate(identity,profiles,result,end_time)
            if include_indicators:
                try:
                    demo_state=demo_trading.state(identity)
                    result['demo_trades']=[trade for trade in demo_state['orders'] if trade['status'] in ('open','pending') and trade['show_on_chart']]
                except (OSError,sqlite3.Error,ValueError):result['demo_trades']=[]
        except (ValueError, OSError, sqlite3.Error):
            raise HTTPException(503, 'Market data is unavailable') from None
        response = JSONResponse(envelope(result))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    def demo_call(operation,*args,**kwargs):
        try:return operation(*args,**kwargs)
        except demo_trading.RateLimited as exc:raise HTTPException(429,str(exc)) from None
        except PermissionError as exc:raise HTTPException(403,str(exc)) from None
        except LookupError:raise HTTPException(404,'Demo account or trade not found') from None
        except demo_trading.Unavailable as exc:raise HTTPException(503,str(exc)) from None
        except demo_trading.Conflict as exc:raise HTTPException(409,str(exc)) from None
        except (ValueError,TypeError):raise HTTPException(422,'Invalid demo request; check prices, settings and request_id') from None
        except (sqlite3.Error,OSError):raise HTTPException(503,'Demo storage unavailable') from None

    def demo_slot(identity,slot_id,kind=None):
        if slot_id is None:return None
        try:binding=slots.binding(identity,slot_id)
        except ValueError:raise HTTPException(422,'Invalid slot') from None
        if not binding or binding['module_id'] not in ((kind,) if kind else demo_components.KINDS):raise HTTPException(404,'Demo slot not found')
        return slot_id

    @router.get('/demo/state')
    def demo_state(account_id: str | None=None,slot_id: str | None=None,identity=Depends(owner)):
        result=demo_call(demo_trading.state,identity,account_id,demo_slot(identity,slot_id))
        return JSONResponse(envelope(result),headers={'Cache-Control':'no-store','Vary':'Authorization'})

    @router.post('/demo/accounts')
    def demo_create(body: dict,identity=Depends(owner)):
        if set(body)-{'name','initial_balance','tradePIN','settings'}:raise HTTPException(422,'Invalid account')
        return envelope({'account':demo_call(demo_trading.create_account,identity,body.get('name'),body.get('initial_balance'),body.get('tradePIN'),body.get('settings'))})

    @router.post('/demo/accounts/{account_id}/select')
    def demo_select(account_id: str,identity=Depends(owner)):
        return envelope({'account':demo_call(demo_trading.select_account,identity,account_id)})

    @router.put('/demo/accounts/{account_id}/settings')
    def demo_settings(account_id: str,body: dict,identity=Depends(owner)):
        if set(body)!={'settings'}:raise HTTPException(422,'Invalid settings')
        return envelope({'account':demo_call(demo_trading.update_settings,identity,account_id,body['settings'])})

    @router.post('/demo/accounts/{account_id}/pin')
    def demo_pin(account_id: str,body: dict,identity=Depends(owner)):
        if set(body)!={'tradePIN'}:raise HTTPException(422,'Invalid PIN request')
        return envelope(demo_call(demo_trading.set_pin,identity,account_id,body['tradePIN']))

    @router.post('/demo/trades')
    def demo_manual(body: dict,request: Request,identity=Depends(owner)):
        data=dict(body);slot=demo_slot(identity,data.pop('slot_id',None),'demo-trade')
        if 'request_id' not in data and request.headers.get('idempotency-key'):data['request_id']=request.headers['idempotency-key']
        return envelope(demo_call(demo_trading.submit,identity,data,'manual',slot))

    @router.post('/demo/bot')
    def demo_bot(body: dict,request: Request,identity=Depends(owner)):
        data=dict(body);slot=demo_slot(identity,data.pop('slot_id',None),'demo-bot')
        if 'request_id' not in data and request.headers.get('idempotency-key'):data['request_id']=request.headers['idempotency-key']
        return envelope(demo_call(demo_trading.submit,identity,data,'bot',slot))

    @router.post('/demo/trades/{trade_id}/{action}')
    def demo_trade_action(trade_id: str,action: str,body: dict,identity=Depends(owner)):
        if action not in ('close','cancel','chart') or set(body)-{'show_on_chart'}:raise HTTPException(422,'Invalid trade action')
        return envelope({'trade':demo_call(demo_trading.alter_order,identity,trade_id,action,body.get('show_on_chart'))})

    @router.get('/demo/reports')
    def demo_reports(account_id: str | None=None,since: float=0,until: float | None=None,identity=Depends(owner)):
        return JSONResponse(envelope(demo_call(demo_trading.report,identity,account_id,since,until)),headers={'Cache-Control':'no-store','Vary':'Authorization'})

    @router.get('/demo/report.csv')
    def demo_csv(account_id: str | None=None,since: float=0,until: float | None=None,identity=Depends(owner)):
        import csv,io
        report=demo_call(demo_trading.report,identity,account_id,since,until)
        if report['history_truncated']:raise HTTPException(422,'Narrow the date range to at most 5000 closed trades for CSV export')
        stream=io.StringIO();writer=csv.writer(stream)
        columns=('id','side','source','entry_fill','close_price','sl','tp','volume','profit','commission','swap','opened_at','closed_at','close_reason')
        writer.writerow(columns)
        for trade in report['history']:writer.writerow([trade.get(key,'') for key in columns])
        return Response(stream.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="demo-report.csv"','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})

    @router.post('/demo/from-execution')
    def demo_execution(body: dict,request: Request,identity=Depends(owner)):
        if set(body)-{'execution_id','account_id','tradePIN','show_on_chart'}:raise HTTPException(422,'Invalid Worker trade request')
        try:execution=str(UUID(body['execution_id']))
        except (KeyError,ValueError,TypeError):raise HTTPException(422,'Invalid execution ID') from None
        credential=accounts.upstream_credential(identity) if request.state.account_session else request.headers['authorization'][7:]
        if credential is None:raise HTTPException(503,'Worker credentials are not provisioned')
        adapter=upstream_factory(identity,credential).get('worker-manager')
        if adapter is None:raise HTTPException(503,'Worker Manager unavailable')
        try:job=adapter.get('/api/v1/executions/'+execution)
        except ConsumerAPIError as exc:raise HTTPException(exc.status if exc.status in (401,403,404) else 503,'Worker execution unavailable') from None
        if not isinstance(job,dict):raise HTTPException(503,'Invalid Worker execution response')
        if job.get('status')!='succeeded':raise HTTPException(409,'Worker execution must succeed before submitting its intent')
        result=job.get('result')
        if isinstance(result,dict) and result.get('status')=='succeeded' and 'result' in result:result=result['result']
        intent=result.get('demo_trade',result) if isinstance(result,dict) else None
        if not isinstance(intent,dict) or set(intent)-{'price','entry','sl','tp','ACTION','action','side'}:raise HTTPException(422,'Worker must return a price or ACTION with SL and TP; no PIN in Worker output')
        data={**intent,'account_id':body.get('account_id'),'tradePIN':body.get('tradePIN'),'request_id':'worker:'+execution,'show_on_chart':body.get('show_on_chart',True)}
        return envelope(demo_call(demo_trading.submit,identity,data,'worker'))

    def media_error(exc):
        status=404 if isinstance(exc,LookupError) else 403 if isinstance(exc,PermissionError) else 422 if isinstance(exc,ValueError) else 503
        raise HTTPException(status,{404:'Media not found',403:'Media access denied',422:'Unsupported media or invalid source',503:'Media storage unavailable'}[status]) from None

    @router.post('/media/describe')
    def media_describe(body: dict,identity=Depends(owner)):
        if set(body)-{'settings','kind'} or body.get('kind') not in (None,'image','audio','video'):raise HTTPException(422,'Invalid media descriptor')
        try:result=media.describe(identity,body.get('settings'),body.get('kind'))
        except (ValueError,LookupError,PermissionError,OSError,sqlite3.Error) as exc:media_error(exc)
        return JSONResponse(envelope(result),headers={'Cache-Control':'no-store','Vary':'Authorization'})

    @router.get('/media/library')
    def media_library(identity=Depends(owner)):
        try:result=media.library(identity)
        except (ValueError,LookupError,PermissionError,OSError,sqlite3.Error) as exc:media_error(exc)
        return JSONResponse(envelope(result),headers={'Cache-Control':'no-store','Vary':'Authorization'})

    @router.get('/media/server/{filename}')
    def media_server(filename: str,identity=Depends(owner)):
        try:path,fmt,size=media.server_file(filename)
        except (ValueError,LookupError,OSError) as exc:media_error(exc)
        return FileResponse(path,media_type=media.FORMATS[fmt][1],headers={'Cache-Control':'no-store','Vary':'Authorization','X-Content-Type-Options':'nosniff','Content-Security-Policy':"sandbox; default-src 'none'"})

    @router.get('/media/upload/{file_id}')
    def media_upload(file_id: str,request: Request,identity=Depends(owner)):
        try:item,fmt=media.uploaded(identity,file_id)
        except (ValueError,LookupError,PermissionError,OSError,sqlite3.Error) as exc:media_error(exc)
        content=item['content'];total=len(content);headers={'Cache-Control':'no-store','Vary':'Authorization','X-Content-Type-Options':'nosniff','Accept-Ranges':'bytes','Content-Security-Policy':"sandbox; default-src 'none'"}
        requested=request.headers.get('range')
        if requested:
            import re
            match=re.fullmatch(r'bytes=(\d*)-(\d*)',requested)
            if not match or not any(match.groups()):raise HTTPException(416,'Invalid media range',headers={'Content-Range':f'bytes */{total}'})
            left,right=match.groups();start=int(left) if left else max(0,total-int(right));end=min(total-1,int(right)) if left and right else total-1
            if start>end or start>=total:raise HTTPException(416,'Invalid media range',headers={'Content-Range':f'bytes */{total}'})
            headers['Content-Range']=f'bytes {start}-{end}/{total}'
            return Response(content[start:end+1],status_code=206,media_type=media.FORMATS[fmt][1],headers=headers)
        return Response(content,media_type=media.FORMATS[fmt][1],headers=headers)

    @router.get('/myip')
    def my_ip(request: Request, identity=Depends(owner)):
        return JSONResponse(envelope(run_module('myip',{'_request_ip':client_ip.address(request)})),headers={'Cache-Control':'no-store','Vary':'Authorization'})

    @router.get('/dashboards')
    def dashboard_list(identity=Depends(owner)):
        return JSONResponse(envelope({'dashboards':workspaces.catalog(identity)}),headers={'Cache-Control':'no-store','Vary':'Authorization'})

    @router.post('/dashboards')
    def dashboard_save(body: dict, identity=Depends(owner)):
        if set(body)!={'name','theme'}:raise HTTPException(422,'Invalid dashboard')
        try:result=workspaces.save(identity,body['name'],body['theme'])
        except ValueError as exc:raise HTTPException(422,str(exc)) from None
        return envelope({'dashboard':result})

    @router.post('/dashboards/{dashboard_id}/load')
    def dashboard_load(dashboard_id: str, identity=Depends(owner)):
        try:result=workspaces.load(identity,dashboard_id)
        except LookupError:raise HTTPException(404,'Dashboard not found') from None
        except ValueError as exc:raise HTTPException(422,str(exc)) from None
        return envelope(result)

    @router.delete('/dashboards/{dashboard_id}')
    def dashboard_delete(dashboard_id: str, identity=Depends(owner)):
        try:workspaces.delete(identity,dashboard_id)
        except LookupError:raise HTTPException(404,'Dashboard not found') from None
        return envelope({'deleted':True})

    @router.get('/indicator-presets')
    def indicator_presets(identity=Depends(owner)):
        return envelope({'presets':{kind:technical.settings(kind) for kind in ('session-clock','session-windows')}})

    @router.get('/indicator-profiles')
    def profile_list(identity=Depends(owner)):
        return envelope({'profiles': indicator_profiles.list_profiles(identity)})

    @router.post('/indicator-profiles')
    def profile_create(body: dict, identity=Depends(owner)):
        try: result = indicator_profiles.save(identity, body)
        except (ValueError, TypeError): raise HTTPException(422, 'Invalid indicator configuration') from None
        return envelope({'profile':result})

    @router.put('/indicator-profiles/{profile_id}')
    def profile_save(profile_id: str, body: dict, identity=Depends(owner)):
        try: result = indicator_profiles.save(identity, body, profile_id)
        except LookupError: raise HTTPException(404, 'Indicator not found') from None
        except (ValueError, TypeError): raise HTTPException(422, 'Invalid indicator configuration') from None
        return envelope({'profile':result})

    @router.delete('/indicator-profiles/{profile_id}')
    def profile_delete(profile_id: str, identity=Depends(owner)):
        try: indicator_profiles.delete(identity, profile_id)
        except LookupError: raise HTTPException(404, 'Indicator not found') from None
        return envelope({'deleted':True})

    @router.get('/signal-rules')
    def signal_list(identity=Depends(owner)):
        return envelope({'rules':[{**rule, 'latest':signal_rules.latest(identity, rule['id'])} for rule in signal_rules.list_rules(identity)]})

    @router.post('/signal-rules')
    def signal_create(body: dict, identity=Depends(owner)):
        try: result = signal_rules.save(identity, body)
        except (ValueError, TypeError, KeyError): raise HTTPException(422, 'Invalid signal rule') from None
        return envelope({'rule':result})

    @router.put('/signal-rules/{rule_id}')
    def signal_save(rule_id: str, body: dict, identity=Depends(owner)):
        try: result = signal_rules.save(identity, body, rule_id)
        except LookupError: raise HTTPException(404, 'Signal not found') from None
        except (ValueError, TypeError, KeyError): raise HTTPException(422, 'Invalid signal rule') from None
        return envelope({'rule':result})

    @router.delete('/signal-rules/{rule_id}')
    def signal_delete(rule_id: str, identity=Depends(owner)):
        try: signal_rules.delete(identity, rule_id)
        except LookupError: raise HTTPException(404, 'Signal not found') from None
        return envelope({'deleted':True})

    @router.post('/signal-rules/{rule_id}/evaluate')
    def signal_evaluate(rule_id: str, identity=Depends(owner)):
        try: result = signal_rules.evaluate_and_save(identity, rule_id)
        except LookupError: raise HTTPException(404, 'Signal not found') from None
        except (ValueError, OSError, sqlite3.Error): raise HTTPException(503, 'Signal data unavailable') from None
        return envelope({'result':result})

    @router.post('/signal-workers/{worker_id}/executions', status_code=202)
    def signal_worker(worker_id: str, body: dict, request: Request, identity=Depends(owner)):
        if set(body) != {'interval', 'idempotency_key'} or body['interval'] not in ('1m','5m','15m') or not isinstance(body['idempotency_key'], str) or not 1 <= len(body['idempotency_key']) <= 256:
            raise HTTPException(422, 'Invalid signal worker request')
        try:
            payload = signal_rules.market_input(identity, body['interval'])
            latest_time = payload['candles'][-1]['time']
            if any(not any(point['time'] == latest_time for point in item['points']) for item in payload['indicators']):
                raise ValueError('indicator data is incomplete')
            path = worker_path(worker_id) + '/executions'
        except ValueError:
            raise HTTPException(409, 'Indicator data unavailable') from None
        except (OSError, sqlite3.Error):
            raise HTTPException(503, 'Indicator data unavailable') from None
        return forward(request, identity, 'worker-manager', 'POST', path,
                       {'input_payload':payload, 'timeout_seconds':30, 'idempotency_key':body['idempotency_key']}, status=202)

    @router.get('/{operation}')
    def read(operation: str, request: Request, identity=Depends(owner)):
        if operation not in routes:
            raise HTTPException(404, 'Unsupported upstream operation')
        name, path = routes[operation]
        return forward(request, identity, name, 'GET', path)

    @router.get('/market/indicators/sma')
    def market_sma(limit: int = Query(default=200, ge=1, le=1000),
                   period: int = Query(default=20, ge=1, le=500),
                   include_open: bool = True, identity=Depends(owner)):
        try:
            result = gold_chart(limit=max(limit, period), period=period, include_open=include_open)
        except (ValueError, OSError, sqlite3.Error):
            raise HTTPException(503, 'Market data is unavailable') from None
        response = JSONResponse(envelope({'symbol':result['symbol'], 'interval':result['interval'],
            'indicator':result['moving_average'], 'last_success':result['last_success'],
            'collector_error':result['collector_error']}))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.get('/market/indicators/{name}')
    def indicators_endpoint(name: str, limit: int = Query(default=200, ge=1, le=1000),
                            period: int = Query(default=14, ge=1, le=500),
                            fast: int = Query(default=12, ge=1, le=500),
                            slow: int = Query(default=26, ge=1, le=500),
                            signal: int = Query(default=9, ge=1, le=500),
                            include_open: bool = True, identity=Depends(owner)):
        if name not in ('rsi', 'macd'): raise HTTPException(404, 'Indicator not found')
        try:
            result = market_indicator(name, {'period':period} if name == 'rsi' else {'fast':fast, 'slow':slow, 'signal':signal}, limit, include_open)
        except ValueError:
            raise HTTPException(422, 'Invalid indicator parameters') from None
        except (OSError, sqlite3.Error):
            raise HTTPException(503, 'Indicator data is unavailable') from None
        response = JSONResponse(envelope(result))
        response.headers['Cache-Control'] = 'no-store'; response.headers['Vary'] = 'Authorization'
        return response

    @router.get('/market/database/{table}')
    def market_database(table: str, limit: int = Query(default=50, ge=1, le=200),
                        offset: int = Query(default=0, ge=0, le=1000000), candle_state: str = 'all',
                        indicator_name: str = 'all', identity=Depends(owner)):
        try:
            result = database_table(table, limit, offset, candle_state, indicator_name)
        except ValueError:
            raise HTTPException(404, 'Table not found') from None
        except (OSError, sqlite3.Error):
            raise HTTPException(503, 'Market database is unavailable') from None
        response = JSONResponse(envelope(result))
        response.headers['Cache-Control'] = 'no-store'; response.headers['Vary'] = 'Authorization'
        return response

    @router.post('/modules/{module_id}/state')
    def module_state(module_id: str, body: dict, request: Request, identity=Depends(owner)):
        if module_id not in ('counter', 'slot-note'):
            raise HTTPException(404, 'Unsupported stateful module')
        if any(str(key).startswith('_') or key == 'owner' for key in body):
            raise HTTPException(422, 'Invalid module input')
        slot = body.get('slot')
        try:
            result = run_module(module_id, {**body, '_state_owner': identity, '_state_slot': slot})
        except (ValueError, TypeError, KeyError, OverflowError):
            raise HTTPException(422, 'Invalid module input') from None
        response = JSONResponse(envelope(result))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.post('/modules/{module_id}/run')
    def run_independent_module(module_id: str, body: dict, request: Request, identity=Depends(owner)):
        if set(body) != {'input'} or not isinstance(body['input'], dict) or any(
                str(key).startswith('_') or key in ('owner', 'slot') for key in body['input']):
            raise HTTPException(422, 'Invalid module input')
        try:
            slots._authorize_host_monitor(identity, module_id)
            result = (lambda data: demo_call(run_module,module_id,data) if module_id in demo_components.KINDS else run_module(module_id,data))({**body['input'],**({'_request_ip':client_ip.address(request)} if module_id=='myip' else {}),**({'_state_owner':identity} if module_id in demo_components.KINDS or module_id in media.KINDS else {})})
        except LookupError:
            raise HTTPException(404, 'Unknown module') from None
        except (ValueError, TypeError, OverflowError, KeyError, ZeroDivisionError):
            raise HTTPException(422, 'Invalid module input or unavailable resource') from None
        response = JSONResponse(envelope({'result': result}))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.get('/slots/active')
    def list_active_slots(identity=Depends(owner)):
        response = JSONResponse(envelope({'slots': slots.list_active(identity), 'owner': identity}))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.post('/slots')
    def create_slot(body: dict, identity=Depends(owner)):
        if set(body) - {'type'}: raise HTTPException(422, 'Invalid slot request')
        try:
            value = slots.create(identity, body.get('type', 'standard'))
        except ValueError:
            raise HTTPException(422, 'Cannot create slot') from None
        response = JSONResponse(envelope({'slot': value}))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.post('/slots/{slot_id}/duplicate')
    def duplicate_slot(slot_id: str, identity=Depends(owner)):
        try: value = slots.duplicate(identity, slot_id)
        except LookupError: raise HTTPException(404, 'Slot not found') from None
        except ValueError: raise HTTPException(422, 'Cannot duplicate slot') from None
        response = JSONResponse(envelope({'slot':value}))
        response.headers['Cache-Control'] = 'no-store'; response.headers['Vary'] = 'Authorization'
        return response

    @router.post('/slots/{slot_id}/overview')
    def update_slot_overview(slot_id: str, body: dict, identity=Depends(owner)):
        if set(body) != {'visible'} or type(body['visible']) is not bool:
            raise HTTPException(422, 'Invalid slot request')
        try:
            slots.set_overview(identity, slot_id, body['visible'])
        except LookupError:
            raise HTTPException(404, 'Slot not found') from None
        response = JSONResponse(envelope({'slot': slot_id, 'visible': body['visible']}))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.delete('/slots/{slot_id}')
    def delete_slot(slot_id: str, identity=Depends(owner)):
        try:
            slots.delete(identity, slot_id)
        except LookupError:
            raise HTTPException(404, 'Slot not found') from None
        response = JSONResponse(envelope({'deleted': slot_id}))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.post('/slots/{slot_id}/appearance')
    def update_slot_appearance(slot_id: str, body: dict, identity=Depends(owner)):
        try:
            value = slots.update_appearance(identity, slot_id, body)
        except PermissionError:
            raise HTTPException(403, 'Room unavailable') from None
        except LookupError:
            raise HTTPException(404, 'Slot not found') from None
        except (ValueError, TypeError):
            raise HTTPException(422, 'Invalid slot appearance') from None
        response = JSONResponse(envelope({'appearance': value}))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.post('/slots/{slot_id}/worker')
    def configure_slot_worker(slot_id: str, body: dict, identity=Depends(owner)):
        try:
            value = slot_workers.configure(identity, slot_id, body)
        except LookupError:
            raise HTTPException(404, 'Slot not found') from None
        except (ValueError, TypeError):
            raise HTTPException(422, 'Invalid slot worker configuration') from None
        response = JSONResponse(envelope({'worker': value}))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.post('/slots/{slot_id}/binding')
    def bind_slot(slot_id: str, body: dict, identity=Depends(owner)):
        if set(body) - {'module_id', 'context', 'only_if_missing'} or type(body.get('only_if_missing', False)) is not bool:
            raise HTTPException(422, 'Invalid slot binding')
        try:
            value = slots.bind_active(identity, slot_id, body.get('module_id'), body.get('context', {}), body.get('only_if_missing', False))
        except LookupError:
            raise HTTPException(404, 'Slot not found') from None
        except (ValueError, TypeError):
            raise HTTPException(422, 'Invalid slot binding') from None
        response = JSONResponse(envelope({'binding':value}))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.post('/slots/{slot_id}/read')
    def read_slot(slot_id: str, body: dict, request: Request, identity=Depends(owner)):
        if set(body) != {'module_id'} or not isinstance(body['module_id'], str):
            raise HTTPException(422, 'Invalid slot request')
        try:
            value = demo_call(slots.read,identity,slot_id,request_ip=client_ip.address(request)) if body['module_id'] in demo_components.KINDS else slots.read(identity,slot_id,request_ip=client_ip.address(request))
            if value['module_id'] != body['module_id']:
                raise ValueError('slot binding changed')
        except PermissionError:
            raise HTTPException(403, 'Room unavailable') from None
        except LookupError:
            raise HTTPException(404, 'Slot not configured') from None
        except (ValueError, TypeError, OverflowError, KeyError):
            raise HTTPException(422, 'Invalid slot request') from None
        response = JSONResponse(envelope(value))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.post('/slots/{slot_id}/execute')
    def execute_slot(slot_id: str, body: dict, request: Request, identity=Depends(owner)):
        if set(body) != {'module_id', 'input'} or not isinstance(body['input'], dict):
            raise HTTPException(422, 'Invalid module input')
        try:
            value = demo_call(slots.execute,identity,slot_id,body['input'],expected_module=body['module_id'],request_ip=client_ip.address(request)) if body['module_id'] in demo_components.KINDS else slots.execute(identity,slot_id,body['input'],expected_module=body['module_id'],request_ip=client_ip.address(request))
        except PermissionError:
            raise HTTPException(403, 'Room unavailable') from None
        except LookupError:
            raise HTTPException(404, 'Slot not configured') from None
        except (ValueError, TypeError, OverflowError, KeyError):
            raise HTTPException(422, 'Invalid module input') from None
        response = JSONResponse(envelope(value))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.post('/workers', status_code=201)
    def register(body: RegisterBody, request: Request, identity=Depends(owner)):
        worker_path(body.worker_id)
        return forward(request, identity, 'worker-manager', 'POST', '/api/v1/workers', body.model_dump(), status=201)

    @router.get('/workers/{worker_id}')
    def worker(worker_id: str, request: Request, identity=Depends(owner)):
        return forward(request, identity, 'worker-manager', 'GET', worker_path(worker_id))

    @router.patch('/workers/{worker_id}')
    def configure(worker_id: str, body: ConfigureBody, request: Request, identity=Depends(owner)):
        if body.configuration is None and body.schedule is None:
            raise HTTPException(422, 'Configuration or schedule is required')
        return forward(request, identity, 'worker-manager', 'PATCH', worker_path(worker_id), body.model_dump(exclude_none=True))

    @router.delete('/workers/{worker_id}')
    def remove(worker_id: str, request: Request, identity=Depends(owner)):
        return forward(request, identity, 'worker-manager', 'DELETE', worker_path(worker_id))

    @router.post('/workers/{worker_id}/enable')
    def enable(worker_id: str, request: Request, identity=Depends(owner)):
        return forward(request, identity, 'worker-manager', 'POST', worker_path(worker_id) + '/enable', {})

    @router.post('/workers/{worker_id}/disable')
    def disable(worker_id: str, request: Request, identity=Depends(owner)):
        return forward(request, identity, 'worker-manager', 'POST', worker_path(worker_id) + '/disable', {})

    @router.post('/workers/{worker_id}/executions', status_code=202)
    def run(worker_id: str, body: RunRequest, request: Request, identity=Depends(owner)):
        try:
            identifier(worker_id)
            if '..' in worker_id:
                raise ValueError()
            path = '/api/v1/workers/' + _identifier(worker_id) + '/executions'
        except ValueError:
            raise HTTPException(422, 'Invalid worker identifier') from None
        return forward(request, identity, 'worker-manager', 'POST', path, body.model_dump(), status=202)

    @router.get('/executions/{execution_id}')
    def execution(execution_id: UUID, request: Request, identity=Depends(owner)):
        return forward(request, identity, 'worker-manager', 'GET', '/api/v1/executions/' + str(execution_id))

    @router.post('/executions/{execution_id}/cancel')
    def cancel(execution_id: UUID, request: Request, identity=Depends(owner)):
        return forward(request, identity, 'worker-manager', 'POST', '/api/v1/executions/' + str(execution_id) + '/cancel', {})

    return router
