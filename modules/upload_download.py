"""Bounded public HTTPS downloads for Upload Center, without executable input.

Every redirect is revalidated. DNS results are checked and the selected public
address is pinned for the TLS connection, retaining hostname verification.
"""
from contextlib import contextmanager
import http.client
import ipaddress
import socket
import ssl
import threading
import time
from urllib.parse import urlsplit, urlunsplit, urljoin, unquote, quote
from . import uploads

SLOTS = threading.BoundedSemaphore(2)


class DownloadError(Exception): pass
class DownloadBusy(Exception): pass


def target(url):
    if not isinstance(url, str) or not 1 <= len(url) <= 4096 or any(ord(c) < 33 or ord(c) == 127 for c in url) or '\\' in url:
        raise ValueError('Use a public HTTPS file URL')
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username is not None or parsed.password is not None or parsed.port not in (None, 443):
        raise ValueError('Only public HTTPS URLs on port 443 without credentials are supported')
    host = parsed.hostname.encode('idna').decode('ascii')
    path = urlunsplit(('', '', quote(parsed.path or '/', safe="/%:@!$&'()*+,;=-._~"), quote(parsed.query, safe="/?%:@!$&'()*+,;=-._~"), ''))
    return host, path


def public_address(host):
    try: results = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError: raise DownloadError('Could not resolve the download host') from None
    addresses = []
    for family, _, _, _, sockaddr in results:
        if family not in (socket.AF_INET, socket.AF_INET6): continue
        address = ipaddress.ip_address(sockaddr[0])
        if not address.is_global or address.is_multicast or address.is_reserved or address.is_unspecified or address.is_loopback or address.is_link_local or getattr(address, 'ipv4_mapped', None) or getattr(address, 'sixtofour', None) or getattr(address, 'teredo', None):
            raise ValueError('Downloads from local, private or reserved addresses are not allowed')
        addresses.append(str(address))
    if not addresses: raise DownloadError('No public address found for the download host')
    # The managed Dashboard service permits AF_INET; prefer IPv4 when available.
    return next((address for address in addresses if ':' not in address), addresses[0])


class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host, address):
        super().__init__(host, timeout=8, context=ssl.create_default_context())
        self.address = address

    def connect(self):
        raw = socket.create_connection((self.address, 443), timeout=self.timeout)
        try: self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except BaseException:
            raw.close()
            raise


@contextmanager
def response_for(url):
    host, path = target(url)
    address = public_address(host)
    connection = PinnedHTTPS(host, address)
    try:
        connection.request('GET', path, headers={'User-Agent':'30na-UploadCenter/1.0', 'Accept-Encoding':'identity', 'Accept':'*/*'})
        response = connection.getresponse()
        try: yield response
        finally: response.close()
    finally: connection.close()


def download(url):
    target(url)
    started = time.monotonic()
    for attempt in range(4):
        if time.monotonic() - started > 60: raise DownloadError('Download timed out')
        try:
            with response_for(url) as response:
                if response.status in (301,302,303,307,308):
                    location = response.getheader('Location')
                    if not location or attempt == 3: raise DownloadError('Download redirected too many times or without a target')
                    url = urljoin(url, location)
                    target(url)
                    continue
                if response.status != 200: raise DownloadError('Remote server refused the download')
                if response.getheader('Content-Encoding', 'identity').lower() not in ('', 'identity'):
                    raise DownloadError('Compressed transfer encoding is not supported')
                declared = response.getheader('Content-Length')
                if declared is not None:
                    try: declared = int(declared)
                    except ValueError: raise DownloadError('Invalid remote file size') from None
                    if declared < 0: raise DownloadError('Invalid remote file size')
                    if declared > uploads.MAX_BYTES: raise OverflowError('File exceeds 20 MiB')
                data = bytearray()
                while True:
                    if time.monotonic() - started > 60: raise DownloadError('Download timed out')
                    chunk = response.read1(min(65536, uploads.MAX_BYTES + 1 - len(data)))
                    if not chunk: break
                    data.extend(chunk)
                    if len(data) > uploads.MAX_BYTES: raise OverflowError('File exceeds 20 MiB')
                if declared is not None and len(data) != declared: raise DownloadError('Remote download ended before the declared file size')
                return bytes(data)
        except (OSError, http.client.HTTPException):
            raise DownloadError('Could not download the file. Check the public link and remote server availability.') from None
    raise DownloadError('Download failed')


def import_url(owner, url, name='', visibility='public', recipient=None):
    target(url)
    if not isinstance(name, str): raise ValueError('Invalid filename')
    if not name:
        name = unquote(urlsplit(url).path.rsplit('/', 1)[-1]) or 'download.bin'
    uploads.validate_metadata(owner, name, visibility, recipient)
    if not SLOTS.acquire(blocking=False): raise DownloadBusy('Download capacity is busy. Try again later.')
    try:
        data = download(url)
        return uploads.create_bytes(owner, name, visibility, recipient, data)
    finally: SLOTS.release()
