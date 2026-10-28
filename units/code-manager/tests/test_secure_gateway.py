import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from wsgiref.util import setup_testing_defaults

from code_manager.secure_gateway import authenticated_wsgi
from code_manager.internal_data_manager import client_factory


class SecurityBoundaryTests(unittest.TestCase):
    def test_auth_and_spoofing_and_revocation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'credentials.json'
            token = 'unit-test-only-not-operational'
            path.write_text(json.dumps({hashlib.sha256(token.encode()).hexdigest(): 'ownerA'}))
            def app(env, start):
                start('200 OK', [])
                return [env['REMOTE_USER'].encode()]
            gateway = authenticated_wsgi(app, path)
            def request(auth=None):
                env = {'REMOTE_USER': 'attacker', 'HTTP_X_MANAGER_ID': 'attacker'}
                if auth is not None:
                    env['HTTP_AUTHORIZATION'] = auth
                out = {}
                def start(status, headers): out['status'] = status
                payload = b''.join(gateway(env, start))
                return out['status'], payload
            self.assertTrue(request()[0].startswith('401'))
            self.assertTrue(request('Bearer bad')[0].startswith('401'))
            self.assertEqual(request('Bearer ' + token), ('200 OK', b'ownerA'))
            path.write_text(json.dumps({hashlib.sha256(b'other').hexdigest(): 'ownerA'}))
            self.assertTrue(request('Bearer ' + token)[0].startswith('401'))

    def test_internal_transport_preserves_owner_and_body(self):
        def app(env, start):
            body = env['wsgi.input'].read(int(env['CONTENT_LENGTH']))
            payload = json.dumps({'owner': env['REMOTE_USER'], 'body': json.loads(body)}).encode()
            start('200 OK', [('Content-Type', 'application/json')])
            return [payload]
        client = client_factory(app)('ownerB')
        result = client.request('POST', '/api/v1/models', {'a': 1})
        self.assertEqual(result, {'owner': 'ownerB', 'body': {'a': 1}})


if __name__ == '__main__':
    unittest.main()
