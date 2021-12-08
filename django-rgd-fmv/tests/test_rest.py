import pytest
from rest_framework import status


@pytest.mark.django_db(transaction=True)
def test_swagger(admin_api_client):
    response = admin_api_client.get('/swagger/?format=openapi')
    assert status.is_success(response.status_code)
