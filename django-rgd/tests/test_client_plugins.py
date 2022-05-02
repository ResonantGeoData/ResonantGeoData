from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rgd_client import create_rgd_client
from rgd_client.plugin import CorePlugin, RgdPlugin


# Plugin A
class PluginA(RgdPlugin):
    rgd = CorePlugin


class ClientA:
    a = PluginA


# Plugin B
class PluginB(RgdPlugin):
    a = PluginA
    rgd = CorePlugin


class ClientB:
    b = PluginB


class MyClient(ClientA, ClientB):
    pass


def test_plugin_dependency_inject(live_server):

    params = {'username': 'test@kitware.com', 'email': 'test@kitware.com', 'password': 'password'}

    user = User.objects.create_user(is_staff=True, is_superuser=True, **params)
    user.save()

    # use constant value for API key so this client fixture can be reused across multiple tests
    Token.objects.create(user=user, key='topsecretkey')

    client = create_rgd_client(
        username=params['username'],
        password=params['password'],
        api_url=f'{live_server.url}/api',
        extra_plugins=[ClientA, ClientB],
    )

    # Assert plugins were loaded correctly
    assert isinstance(client.a.rgd, CorePlugin)
    assert isinstance(client.b.rgd, CorePlugin)
    assert isinstance(client.b.a, PluginA)

    # Assert underlying class is not modified
    assert not isinstance(PluginA.rgd, CorePlugin)
    assert not isinstance(PluginB.rgd, CorePlugin)
    assert not isinstance(PluginB.a, PluginA)
