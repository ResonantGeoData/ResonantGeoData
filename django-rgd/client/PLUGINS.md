# Plugin Development

The behavior of `rgd_client` can be extended through plugins. A plugin is python package with a specific class definition that can be loaded by the `create_rgd_client` method. This document outlines the definition and use of these plugins.


## Defining a Plugin
A plugin is defined by creating two classes. The first is the definition of the core plugin itself


### The Plugin Class
```python
class MyPlugin:
    def __init__(self, session: RgdClientSession):
        self.session = session

        # Optionally extend the existing base url
        self.session.base_url += 'foo/'

    def get_bar(self):
        return self.session.get('bar')
```

Each plugin is instantiated with a `RgdClientSession` instance. This is a copy of the core client session, which is instantiated once and copied to all loaded plugins. The core client session is instantiated with the base url of the RGD API you're trying to access, as well as authentication if `username` and `password` are supplied to `create_rgd_client`. This session copy is supplied to the plugin for it's own use, as well as possible modification. Since it's common for plugins to urls under a specific prefix, the session base url can be extended, as shown in the example. The session can be modified in any desired way, as it's a copy and will not affect the core client session.


### The Client Class
The second class that's required serves two purposes: Plugin discovery, and static type preservation. The class is defined as followed:

```python
from rgd_client import RgdClient


class MyClient(RgdClient):
    foo = MyPlugin
```

The definition of the class itself (along with an entry point definition, covered below) is all that's required for the plugin to be loaded. You'll notice that `MyClient` extends `RgdClient`. This isn't strictly necessary for plugin discovery, but it done so for type information. Since we've extended `RgdClient`, the `rgd` namespace will be shown as a class member in your IDE. Generally speaking, if a plugin wants correct type information, it should inherit from all plugins that it intends to use. So, if the above plugin was making use of several other plugins, it might be defined as follows

```python
class MyClient(FooClient, BarClient, BazClient):
    foo = MyPlugin
```

Notice that I didn't extend `RgdClient` explicitly here. That's because in this example, I'm assuming that all of the inherited clients already do so in their definitions, so declaring it explicitly here is redundant.

Without these type hints, any loaded plugins can still be used, their namespaces just won't be visible with any IDE autocompletion or intellisense.


### Defining the Plugin Entry Point
To allow for easy plugin discovery, plugins can register an entry point in their `setup.py` or `setup.cfg` with the `rgd_client.plugin` namespace. Below is an example with a `setup.py` file. Let's assume `MyClient` is defined in `my_client/__init__.py`

```python
setup(
    name='my-rgd-plugin',
    install_requires=['rgd_client'],
    entry_points={
        'rgd_client.plugin': [
            'my_client = my_client:MyClient',
        ],
    },
)
```
Now, to make this plugin visible to the core client, all that's required is to install this package with pip, either locally, or from PyPI.

### Using a plugin without defining an entry point
It may not be practical or desired to create an entire python package to house your plugin. For this reason, there's another way to register your plugin for use

```python
from rgd_client import create_rgd_client

client: MyClient = create_rgd_client(
    api_url='https://foo.com',
    username='foo',
    password='bar',
    extra_plugins=[MyClient]
)
```
Now your plugin is registered and able to be used without needing an entrypoint.

### Using your Plugin
Creating a client instance that loads your plugin is identical to the above example, with the exception of not needing to supply `extra_plugins` if your plugin is registered through an entry point.

Your plugin features can be accessed the following way

```python
client.foo.bar()
```

Since the definition of `MyClient` defines the namespace as `foo`, all methods in `MyPlugin` are accessed through this namespace.


### Using the Client
Sometimes you might need to use the client without defining your own plugin, but rather just using others. In this case, all that's required in this case is to install the plugins and create a client instance

```python
from rgd_client import create_rgd_client

client = create_rgd_client()
```

However, this won't contain any type information about any installed plugins (just the core plugin). If you want to preserve this type information for your own use, you can define a dummy class for the sole purpose of type hints

```python
from rgd_client import create_rgd_client
from foo_plugin import FooClient
from bar_plugin import BarClient
from baz_plugin import BazClient

class Client(FooClient, BarClient, BazClient):
    pass

client: Client = create_rgd_client()
```

Now, all plugin namespaces and methods will be shown in your IDE.


### Sibling plugins
There may be a circumstance where you'd like to make use of another plugin from within your own plugin. For example, if you wanted to wrap the core `search` method in your own `my_search` function. This can be done by defining a *plugin dependency*.

This is very simple to do, just place a definition of the plugin you'd like to use within your own plugin definition. Here's an example that illustrates the situation metioned above

```python
from rgd_client.plugin import CorePlugin


class MyPlugin(RgdPlugin):
    rgd = CorePlugin

    def my_search(self, *args, **kwargs):
        res = self.rgd.search(*args, **kwargs)

        print('Search Performed!')
        return res

class MyClient:
    foo = MyPlugin

```

When `create_rgd_client` is called, it searches all registered plugins for members that inherit `RgdPlugin`, and instantiates them if it does. So, as long as the plugin you want to use is installed with `pip`, or is provided in `extra_plugins`, it will be injected into your plugin.
