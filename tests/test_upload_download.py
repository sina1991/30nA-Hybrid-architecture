"""Public-link imports: bounded transfer, DNS pinning, redirects and ownership."""
from contextlib import contextmanager
import io
import socket
import pytest
from modules import upload_download as download, uploads
from test_account_chat_api import client, create_accounts, auth


class Response(io.BytesIO):
    def __init__(self, body=b'file', status=200, **headers):
        super().__init__(body); self.status=status; self.headers=headers
    def getheader(self, name, default=None): return self.headers.get(name,default)


def fake_response(monkeypatch, factory):
    @contextmanager
    def response(url):
        result=factory(url)
        try: yield result
        finally: result.close()
    monkeypatch.setattr(download,'response_for',response)


@pytest.mark.parametrize('url',[
    'http://example.com/file','file:///etc/passwd','ftp://example.com/a','https://user:pass@example.com/a',
    'https://example.com:444/a','https://example.com/a\r\nHeader:x','https://example.com\\@127.0.0.1/a'])
def test_reject_unsafe_url(url):
    with pytest.raises(ValueError): download.target(url)


@pytest.mark.parametrize('address',[
    '127.0.0.1','10.0.0.1','169.254.169.254','192.168.1.1','100.64.0.1','0.0.0.0','224.0.0.1',
    '::1','fc00::1','fe80::1','::ffff:127.0.0.1','2002:7f00:1::'])
def test_dns_blocks_internal_reserved_and_mapped_addresses(monkeypatch,address):
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**kw:[(socket.AF_INET6 if ':' in address else socket.AF_INET,1,6,'',(address,443))])
    with pytest.raises(ValueError): download.public_address('file.example')


def test_dns_is_pinned_without_forwarding_credentials(monkeypatch):
    resolutions=[]; connections=[]
    def resolve(*a,**kw):
        resolutions.append(a)
        return [(socket.AF_INET,1,6,'',('8.8.8.8' if len(resolutions)==1 else '127.0.0.1',443))]
    class Connection:
        def __init__(self,host,address):connections.append((host,address))
        def request(self,method,path,headers):
            assert method=='GET' and path=='/clip.mp4?x=1'
            assert not {'Cookie','Authorization','Proxy-Authorization'} & set(headers)
        def getresponse(self):return Response(b'file')
        def close(self):pass
    monkeypatch.setattr(socket,'getaddrinfo',resolve);monkeypatch.setattr(download,'PinnedHTTPS',Connection)
    assert download.download('https://file.example/clip.mp4?x=1')==b'file'
    assert connections==[('file.example','8.8.8.8')] and len(resolutions)==1


def test_redirect_to_private_host_is_revalidated(monkeypatch):
    connected=[]
    monkeypatch.setattr(socket,'getaddrinfo',lambda host,*a,**kw:[(socket.AF_INET,1,6,'',('127.0.0.1' if host=='localhost' else '8.8.8.8',443))])
    class Connection:
        def __init__(self,host,address):connected.append(address)
        def request(self,*a,**kw):pass
        def getresponse(self):return Response(status=302,Location='https://localhost/secret')
        def close(self):pass
    monkeypatch.setattr(download,'PinnedHTTPS',Connection)
    with pytest.raises(ValueError):download.download('https://file.example/a')
    assert connected==['8.8.8.8']


def test_redirect_limit_length_overflow_and_partial_download(monkeypatch):
    fake_response(monkeypatch,lambda url:Response(status=302,Location='/next'))
    with pytest.raises(download.DownloadError):download.download('https://file.example/a')
    fake_response(monkeypatch,lambda url:Response(status=302,Location='http://file.example/a'))
    with pytest.raises(ValueError):download.download('https://file.example/a')
    monkeypatch.setattr(uploads,'MAX_BYTES',10)
    for headers in ({'Content-Length':'11'},{}):
        fake_response(monkeypatch,lambda url:Response(b'x'*11,**headers))
        with pytest.raises(OverflowError):download.download('https://file.example/a')
    fake_response(monkeypatch,lambda url:Response(b'x',**{'Content-Length':'5'}))
    with pytest.raises(download.DownloadError):download.download('https://file.example/a')
    fake_response(monkeypatch,lambda url:Response(b'x',**{'Content-Encoding':'gzip'}))
    with pytest.raises(download.DownloadError):download.download('https://file.example/a')


def test_url_import_authorization_and_no_partial_records(client,monkeypatch):
    (alice,a),(bob,b),(eve,e)=create_accounts(client)
    content=b'\x00\x00\x00\x18ftypmp42'+b'x'*(2*1024*1024)
    fake_response(monkeypatch,lambda url:Response(content,**{'Content-Length':str(len(content))}))
    body={'url':'https://file.example/clip.mp4','name':'','visibility':'direct','recipient':bob['id']}
    path='/api/upstreams/uploads/from-url'
    assert client.post(path,json=body).status_code==401
    result=client.post(path,headers=auth(a),json=body)
    assert result.status_code==200,result.text
    item=result.json()['payload']['file'];assert item['size']==len(content) and item['name']=='clip.mp4'
    assert client.get('/api/upstreams/uploads/'+item['id']+'/content',headers=auth(b)).content==content
    assert client.get('/api/upstreams/uploads/'+item['id']+'/content',headers=auth(e)).status_code==404
    assert client.delete('/api/upstreams/uploads/'+item['id'],headers=auth(b)).status_code==404
    def should_not_fetch(url):raise AssertionError('Invalid metadata must not trigger network access')
    fake_response(monkeypatch,should_not_fetch)
    for change in ({'name':'../evil'},{'recipient':'unknown'},{'url':'http://file.example/file'}):
        assert client.post(path,headers=auth(a),json={**body,**change}).status_code==422
    fake_response(monkeypatch,lambda url:Response(b'incomplete',**{'Content-Length':'100'}))
    assert client.post(path,headers=auth(a),json=body).status_code==502
    assert len(uploads.list_files(alice['id']))==1
    assert download.SLOTS.acquire(False) and download.SLOTS.acquire(False)
    try:assert client.post(path,headers=auth(a),json=body).status_code==429
    finally:download.SLOTS.release();download.SLOTS.release()


def test_public_ipv4_preferred_for_managed_service_and_tls_keeps_original_host(monkeypatch):
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**kw:[(socket.AF_INET6,1,6,'',('2606:4700:4700::1111',443)),(socket.AF_INET,1,6,'',('8.8.8.8',443))])
    assert download.public_address('files.example')=='8.8.8.8'
    events=[]
    class Raw:
        def close(self):events.append('close')
    def connect(address,timeout):events.append(address);return Raw()
    class TLS:
        def wrap_socket(self,raw,server_hostname):events.append(server_hostname);return raw
    monkeypatch.setattr(socket,'create_connection',connect)
    connection=download.PinnedHTTPS('files.example','8.8.8.8');connection._context=TLS();connection.connect();connection.close()
    assert events==[('8.8.8.8',443),'files.example','close']
