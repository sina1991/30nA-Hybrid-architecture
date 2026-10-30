import ssl

import pytest
from worker_manager.http_gateway import RuntimeHTTPGateway


def test_missing_or_invalid_private_ca_is_not_silently_ignored(tmp_path):
    for value in ['',False,123]:
        with pytest.raises(ValueError):RuntimeHTTPGateway('https://localhost','fixture-token',ca_file=value)
    with pytest.raises(OSError):RuntimeHTTPGateway('https://localhost','fixture-token',ca_file=str(tmp_path/'missing.pem'))
    bad=tmp_path/'invalid.pem';bad.write_text('not a certificate')
    with pytest.raises(ssl.SSLError):RuntimeHTTPGateway('https://localhost','fixture-token',ca_file=str(bad))


def test_injected_client_cannot_silently_override_explicit_ca_configuration():
    with pytest.raises(ValueError,match='injected client'):
        RuntimeHTTPGateway('https://localhost','fixture-token',client=object(),ca_file='/unused/cert.pem')
