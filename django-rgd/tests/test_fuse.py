from pathlib import Path

import magic
import pytest
from rgd import utility
from rgd.datastore import datastore

SKIP_FUSE = True
try:
    import simple_httpfs  # noqa

    assert Path('/tmp/rgd/http').exists()
    SKIP_FUSE = False
except (ImportError, EnvironmentError, AssertionError):
    pass

FILENAME = 'stars.png'


@pytest.fixture
def simple_url():
    return datastore.get_url(FILENAME)


@pytest.mark.skipif(SKIP_FUSE, reason='FUSE is not installed/configured.')
@pytest.mark.django_db(transaction=True)
def test_fuse_mount(simple_url):
    assert utility.precheck_fuse(simple_url)
    path = utility.url_file_to_fuse_path(simple_url)
    assert path.exists()
    mime = magic.Magic(mime=True)
    assert mime.from_file(path) == 'image/png'
