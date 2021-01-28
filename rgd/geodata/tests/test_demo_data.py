from io import StringIO

from django.core.management import call_command
import pytest

from rgd.geodata.datastore import registry
from rgd.geodata.management.commands import demo_data


def _call_command(name, *args, **kwargs):
    out = StringIO()
    call_command(
        name,
        *args,
        stdout=out,
        stderr=StringIO(),
        **kwargs,
    )
    return out.getvalue()


@pytest.mark.skip
@pytest.mark.django_db(transaction=True)
def test_load_all_demo_data():
    out = _call_command('demo_data')
    assert out == demo_data.SUCCESS_MSG + '\n'


def test_entries_in_datastore():
    def is_in_datastore(f):
        if isinstance(f, (list, tuple)):
            return all([is_in_datastore(i) for i in f])
        return f in registry

    for f in (
        demo_data.IMAGE_FILES
        + demo_data.RASTER_FILES
        + demo_data.SHAPE_FILES
        + demo_data.FMV_FILES
        + demo_data.KWCOCO_ARCHIVES
    ):
        assert is_in_datastore(f), f'`{f}` not in registry.'


@pytest.mark.skip
@pytest.mark.django_db(transaction=True)
def test_demo_command_landsat():
    out = _call_command('landsat_data', count=1)
    assert out == demo_data.SUCCESS_MSG + '\n'
