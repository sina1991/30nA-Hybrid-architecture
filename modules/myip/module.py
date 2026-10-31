"""Display the requesting client's IP; CLI has no implicit browser identity."""
from pathlib import Path
import sys
import ipaddress
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from modules.module_support import main


def run(data):
    if set(data)-{'_request_ip','address'}:raise ValueError('Unknown My IP input')
    value=data.get('_request_ip',data.get('address'))
    if value is None:return {'status':'unavailable','ip':None,'source':'no_http_client','message':'Client IP requires an authenticated HTTP request.'}
    try:address=str(ipaddress.ip_address(value))
    except (TypeError,ValueError):raise ValueError('Invalid IP address') from None
    return {'status':'ok','ip':address,'source':'http_client' if '_request_ip' in data else 'provided'}

if __name__=='__main__':sys.exit(main(run))
