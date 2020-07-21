import pytest
from rest_framework.test import APIClient

# Names must be imported into conftest, importing for side effects is not sufficient
from .factories import *  # noqa: F401,F403


@pytest.fixture
def api_client():
    return APIClient()
