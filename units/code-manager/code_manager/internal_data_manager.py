"""In-process WSGI transport preserving the DataManagerClient API contract."""
import io
from urllib.parse import urlsplit
from wsgiref.util import setup_testing_defaults

from .data_manager_client import DataManagerClient


def client_factory(data_manager_application):
    def for_owner(owner_id):
        def transport(method, url, headers, body, timeout):
            parsed = urlsplit(url)
            env = {}
            setup_testing_defaults(env)
            env.update(REQUEST_METHOD=method, PATH_INFO=parsed.path,
                       QUERY_STRING=parsed.query, CONTENT_LENGTH=str(len(body or b'')),
                       **{'wsgi.input': io.BytesIO(body or b''), 'REMOTE_USER': owner_id})
            if 'Content-Type' in headers:
                env['CONTENT_TYPE'] = headers['Content-Type']
            result = {}
            def start_response(status, response_headers, exc_info=None):
                result['status'] = int(status.split(' ', 1)[0])
                result['headers'] = dict(response_headers)
            response = data_manager_application(env, start_response)
            try:
                payload = b''.join(response)
            finally:
                if hasattr(response, 'close'):
                    response.close()
            return result['status'], result['headers'], payload
        return DataManagerClient('http://localhost', transport=transport)
    return for_owner
