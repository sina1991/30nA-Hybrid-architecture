"""Use a canonical header only from the explicitly trusted local proxy."""
import ipaddress
import os


def address(request):
    try:peer=ipaddress.ip_address(request.client.host)
    except (ValueError,AttributeError):return None
    if peer.is_loopback:
        if os.environ.get('DASHBOARD_TRUST_LOCAL_PROXY')!='1':return None
        try:return str(ipaddress.ip_address(request.headers.get('x-30na-client-ip','')))
        except ValueError:return None
    return str(peer)
