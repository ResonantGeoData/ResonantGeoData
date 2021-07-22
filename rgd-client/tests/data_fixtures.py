import subprocess

import pytest

from . import MANAGE_PATH, PYTHON_PATH, SETTINGS_MODULE

sources = [
    'rgd_3d_demo',
    'rgd_fmv_demo',
    'rgd_geometry_demo',
    'rgd_imagery_demo',
]

# dynamically creates fixtures for above management commands


def generate_fixtures():
    for s in sources:

        @pytest.fixture
        def data_fixture(pytestconfig):

            has_run = pytestconfig.cache.get(s, False)

            if not has_run:
                subprocess.run(
                    [PYTHON_PATH, MANAGE_PATH, s],
                    env={'DJANGO_SETTINGS_MODULE': SETTINGS_MODULE},
                )

                pytestconfig.cache.set(s, True)

        yield (s, data_fixture)
