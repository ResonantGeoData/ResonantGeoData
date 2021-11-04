from rgd_client import create_rgd_client
from rgd_client.plugin import CorePlugin, RGDPlugin


# Plugin A
class PluginADependencies:
    rgd = CorePlugin


class PluginA(RGDPlugin):
    plugins = PluginADependencies


class ClientA:
    a = PluginA


# Plugin B
class PluginBDependencies:
    a = PluginA
    rgd = CorePlugin


class PluginB(RGDPlugin):
    plugins = PluginBDependencies


class ClientB:
    b = PluginB


class MyClient(ClientA, ClientB):
    pass


def test_plugin_dependency_inject():
    client: MyClient = create_rgd_client(extra_plugins=[ClientA, ClientB])

    # Assert plugins were loaded correctly
    assert isinstance(client.a.plugins.rgd, CorePlugin)
    assert isinstance(client.b.plugins.rgd, CorePlugin)
    assert isinstance(client.b.plugins.a, PluginA)
