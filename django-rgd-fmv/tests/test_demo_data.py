import pytest
from rgd_fmv.management.commands import demo_data

from rgd_testing_utils.helpers import _call_command


@pytest.mark.skip
@pytest.mark.django_db(transaction=True)
def test_demo_command_wasabi():
    out = _call_command('wasabi')
    assert out == demo_data.SUCCESS_MSG + '\n'
