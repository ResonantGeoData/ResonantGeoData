import inspect

from django.contrib.auth.models import User
import factory
import pytest
from pytest_factoryboy import register
from rgd_client import create_rgd_client
from rgd_testing_utils import factories
from rgd_testing_utils.api_fixtures import *  # noqa
from rgd_testing_utils.data_fixtures import *  # noqa

for _, fac in inspect.getmembers(factories):
    if inspect.isclass(fac) and issubclass(fac, factory.Factory):
        register(fac)


@pytest.fixture
def py_client(live_server):
    params = {'username': 'test@kitware.com', 'email': 'test@kitware.com', 'password': 'password'}

    user = User.objects.create_user(is_staff=True, is_superuser=True, **params)
    user.save()

    client = create_rgd_client(
        username=params['username'], password=params['password'], api_url=f'{live_server.url}/api'
    )

    return client
