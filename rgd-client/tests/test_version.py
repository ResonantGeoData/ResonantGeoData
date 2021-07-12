import requests

import rgd_client


def test_rgd_version():
    assert rgd_client.__version__  # Make sure not None


def test_server_status():
    assert requests.get('http://localhost:8000').status_code == 200
