from django.core.management import call_command
import pytest

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
        def data_fixture():
            call_command(s)

        yield (s, data_fixture)
