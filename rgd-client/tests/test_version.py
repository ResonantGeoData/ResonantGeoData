import rgd_client


def test_rgd_version():
    assert rgd_client.__version__  # Make sure not None
