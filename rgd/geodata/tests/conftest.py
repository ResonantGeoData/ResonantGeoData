import inspect

import factory
import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient

from . import factories
from .data_fixtures import *  # noqa


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def admin_api_client(user_factory) -> APIClient:
    client = APIClient()
    user = user_factory(is_superuser=True)
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def authenticated_api_client(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


for _, fac in inspect.getmembers(factories):
    if inspect.isclass(fac) and issubclass(fac, factory.Factory):
        register(fac)
