import subprocess

import pytest

from . import MANAGE_PATH, PYTHON_PATH

sources = [
    'rgd_3d_demo',
    'rgd_fmv_demo',
    'rgd_fmv_wasabi',
    'rgd_geometry_demo',
    'rgd_imagery_demo',
    'rgd_imagery_landsat_rgb_s3',
]


# dynamically creates fixtures for above management commands
for s in sources:

    @pytest.fixture
    def data_fixture():

        subprocess.run(
            [PYTHON_PATH, MANAGE_PATH, s],
            env={"DJANGO_SETTINGS_MODULE": "rgd_example.settings"},
        )

    globals()[s] = data_fixture
