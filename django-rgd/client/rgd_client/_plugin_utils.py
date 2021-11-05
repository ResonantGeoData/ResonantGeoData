import inspect
from typing import Dict, List, Optional, Type

from pkg_resources import iter_entry_points
from rgd_client.client import RgdClient
from rgd_client.plugin import CorePlugin, RgdPlugin
from rgd_client.session import clone_session

_NAMESPACE = 'rgd_client.plugin'
_PLUGIN_CLASS_DICT = Dict[str, Type[RgdPlugin]]
_PLUGIN_INSTANCE_DICT = Dict[Type[RgdPlugin], RgdPlugin]


def _plugin_classes(extra_plugins: Optional[List] = None) -> _PLUGIN_CLASS_DICT:
    """Return a dict that maps a plugin namespace to its class."""
    entry_points = iter_entry_points(_NAMESPACE)
    plugins_classes = [ep.load() for ep in entry_points]
    if extra_plugins is not None:
        plugins_classes.extend(extra_plugins)

    members = {}
    for cls in plugins_classes:
        members.update(
            {
                n: v
                for n, v in inspect.getmembers(cls)
                if inspect.isclass(v) and issubclass(v, RgdPlugin)
            }
        )

    return members


def _plugin_instances(
    client: RgdClient, plugin_classes: _PLUGIN_CLASS_DICT
) -> _PLUGIN_INSTANCE_DICT:
    """Return a dict that maps a plugin class to its instance."""
    instance_dict: _PLUGIN_INSTANCE_DICT = {CorePlugin: client.rgd}
    for name, cls in plugin_classes.items():
        instance = cls(clone_session(client.session))
        setattr(client, name, instance)
        instance_dict[cls] = instance

    return instance_dict


def _inject_plugin_deps(plugin_instances: _PLUGIN_INSTANCE_DICT):
    """Inject plugin dependencies for each plugin instance."""
    for plugin_class, plugin_instance in plugin_instances.items():
        deps = [
            (name, val)
            for name, val in inspect.getmembers(plugin_class)
            if inspect.isclass(val) and issubclass(val, RgdPlugin)
        ]

        for name, cls in deps:
            if cls in plugin_instances:
                setattr(plugin_instance, name, plugin_instances[cls])
