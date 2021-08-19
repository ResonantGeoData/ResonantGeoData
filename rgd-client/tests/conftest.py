from django.contrib.auth.models import User
import pytest
from rgd_client import Rgdc  # noqa

from .data_fixtures import generate_fixtures

# dynamic fixtures: populate commands
for (name, fixture) in generate_fixtures():
    globals()[name] = fixture


@pytest.fixture
def py_client(live_server):

    params = {'username': 'test@kitware.com', 'email': 'test@kitware.com', 'password': 'password'}

    user = User.objects.create_user(is_staff=True, is_superuser=True, **params)
    user.save()

    client = Rgdc(
        username=params['username'], password=params['password'], api_url=f'{live_server.url}/api'
    )

    return client
