import requests

import rgd_client


def test_rgd_version():
    assert rgd_client.__version__  # Make sure not None


def test_server_status(live_server):
    assert requests.get(live_server.url).status_code == 200
