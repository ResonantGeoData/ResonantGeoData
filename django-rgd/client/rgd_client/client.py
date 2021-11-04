import getpass
import inspect
import os
from typing import Dict, List, Optional, Type

from pkg_resources import iter_entry_points
import requests

from .plugin import CorePlugin, RGDPlugin
from .session import RgdClientSession, clone_session
from .utils import API_KEY_DIR_PATH, API_KEY_FILE_NAME, DEFAULT_RGD_API

_NAMESPACE = 'rgd_client.plugin'
_PLUGIN_CLASS_DICT = Dict[str, Type[RGDPlugin]]
_PLUGIN_INSTANCE_DICT = Dict[Type[RGDPlugin], RGDPlugin]


class RgdClient:
    def __init__(
        self,
        api_url: str = DEFAULT_RGD_API,
        username: Optional[str] = None,
        password: Optional[str] = None,
        save: Optional[bool] = True,
    ) -> None:
        """
        Initialize the base RGD Client.

        Args:
            api_url: The base url of the RGD API instance.
            username: The username to authenticate to the instance with, if any.
            password: The password associated with the provided username. If None, a prompt will be provided.
            save: Whether or not to save the logged-in user's API key to disk for future use.

        Returns:
            A base RgdClient instance.
        """
        # Look for an API key in the environment. If it's not there, check username/password
        api_key = _read_api_key()
        if api_key is None:
            if username is not None and password is None:
                password = getpass.getpass()

            # Get an API key for this user and save it to disk
            if username and password:
                api_key = _get_api_key(api_url, username, password, save)

        auth_header = f'Token {api_key}'

        self.session = RgdClientSession(base_url=api_url, auth_header=auth_header)
        self.rgd = CorePlugin(clone_session(self.session))

    def clear_token(self):
        """Delete a locally-stored API key."""
        (API_KEY_DIR_PATH / API_KEY_FILE_NAME).unlink(missing_ok=True)


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
                if inspect.isclass(v) and issubclass(v, RGDPlugin)
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
        # Ensure plugins class is defined
        if not inspect.isclass(getattr(plugin_class, 'plugins', None)):
            continue

        # Retrieve deps
        deps = [
            (name, val)
            for name, val in inspect.getmembers(plugin_class.plugins)
            if inspect.isclass(val) and issubclass(val, RGDPlugin)
        ]

        for name, cls in deps:
            if cls in plugin_instances:
                setattr(plugin_instance.plugins, name, plugin_instances[cls])


def _get_api_key(api_url: str, username: str, password: str, save: bool) -> str:
    """Get an RGD API Key for the given user from the server, and save it if requested."""
    resp = requests.post(f'{api_url}/api-token-auth', {'username': username, 'password': password})
    resp.raise_for_status()
    token = resp.json()['token']
    if save:
        API_KEY_DIR_PATH.mkdir(parents=True, exist_ok=True)
        with open(API_KEY_DIR_PATH / API_KEY_FILE_NAME, 'w') as fd:
            fd.write(token)
    return token


def _read_api_key() -> Optional[str]:
    """
    Retrieve an RGD API Key from the users environment.

    This function checks for an environment variable named RGD_API_TOKEN and returns it if it exists.
    If it does not exist, it looks for a file located at ~/.rgd/token and returns its contents.
    """
    token = os.getenv('RGD_API_TOKEN', None)
    if token is not None:
        return token

    try:
        # read the first line of the text file at ~/.rgd/token
        with open(API_KEY_DIR_PATH / API_KEY_FILE_NAME, 'r') as fd:
            return fd.readline().strip()
    except FileNotFoundError:
        return None


def create_rgd_client(
    api_url: str = DEFAULT_RGD_API,
    username: Optional[str] = None,
    password: Optional[str] = None,
    save: Optional[bool] = True,
    extra_plugins: Optional[List[Type]] = None,
):
    # Create initial client
    client = RgdClient(api_url, username, password, save)

    # Perform plugin initialization
    plugin_classes = _plugin_classes(extra_plugins=extra_plugins)
    plugin_instances = _plugin_instances(client, plugin_classes)
    _inject_plugin_deps(plugin_instances)

    return client
