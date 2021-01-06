from io import StringIO
import pytest

from django.core.management import call_command

from rgd.geodata.management.commands.demo_data import SUCCESS_MSG


def _call_command(*args, **kwargs):
    out = StringIO()
    call_command(
        "demo_data",
        *args,
        stdout=out,
        stderr=StringIO(),
        **kwargs,
    )
    return out.getvalue()


@pytest.mark.skip
@pytest.mark.django_db(transaction=True)
def test_load_all_demo_data():
    out = _call_command()
    assert out == SUCCESS_MSG + '\n'
