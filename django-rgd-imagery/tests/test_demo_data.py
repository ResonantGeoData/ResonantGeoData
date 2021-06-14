from io import StringIO

from django.core.management import call_command
import pytest

# from rgd_imagery.management.commands import demo_data


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
def test_demo_command_landsat():
    out = _call_command('s3_landsat', count=1)
    assert out  # == demo_data.SUCCESS_MSG.replace('demo', 'landsat') + '\n'
