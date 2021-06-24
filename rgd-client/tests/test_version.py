from io import open as io_open
import os

import rgd


def test_rgd_version():
    assert rgd.__version__  # Make sure not None
    __version__ = None
    filepath = os.path.dirname(__file__)
    version_file = os.path.join(filepath, '..', '..', 'version.py')
    with io_open(version_file, mode='r') as fd:
        exec(fd.read())
    assert (
        rgd.__version__ == __version__
    ), 'Cache likely needs to be cleared so package is reinstalled.'
