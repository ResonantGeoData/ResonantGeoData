import pytest
from rest_framework.test import APIClient


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
