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


def test_plugin_dependency_inject():
    client: MyClient = create_rgd_client(extra_plugins=[ClientA, ClientB])

    # Assert plugins were loaded correctly
    assert isinstance(client.a.rgd, CorePlugin)
    assert isinstance(client.b.rgd, CorePlugin)
    assert isinstance(client.b.a, PluginA)

    # Assert underlying class is not modified
    assert not isinstance(PluginA.rgd, CorePlugin)
    assert not isinstance(PluginB.rgd, CorePlugin)
    assert not isinstance(PluginB.a, PluginA)
