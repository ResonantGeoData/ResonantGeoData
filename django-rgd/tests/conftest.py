import inspect

from django.contrib.auth.models import User
import factory
import pytest
from pytest_factoryboy import register
from rest_framework.authtoken.models import Token
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

    # use constant value for API key so this client fixture can be reused across multiple tests
    Token.objects.create(user=user, key='topsecretkey')

    client = create_rgd_client(
        username=params['username'], password=params['password'], api_url=f'{live_server.url}/api'
    )

    return client


@pytest.fixture
def user_with_api_key(faker):
    email = faker.email()
    password = 'password'
    params = {'username': email, 'email': email, 'password': password}

    user = User.objects.create_user(is_staff=True, is_superuser=True, **params)
    user.save()

    api_token = 'topsecretkey'
    Token.objects.create(user=user, key=api_token)

    return email, password, api_token
