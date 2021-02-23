import inspect

import factory
import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient

from . import factories


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def admin_api_client(user) -> APIClient:
    client = APIClient()
    user.is_superuser = True
    user.is_staff = True
    user.is_active = True
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
