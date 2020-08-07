import inspect

import factory
import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient

from . import factories


@pytest.fixture
def api_client():
    return APIClient()


for _, fac in inspect.getmembers(factories):
    if inspect.isclass(fac) and issubclass(fac, factory.Factory):
        register(fac)
