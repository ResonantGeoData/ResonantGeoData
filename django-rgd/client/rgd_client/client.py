import getpass
import inspect
import os
from typing import Dict, List, Optional, Type

from pkg_resources import iter_entry_points
import requests

from .plugin import CorePlugin
from .session import RgdClientSession, clone_session
from .utils import API_KEY_DIR_PATH, API_KEY_FILE_NAME, DEFAULT_RGD_API

_NAMESPACE = 'rgd_client.plugin'


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


def _plugins_dict(extra_plugins: Optional[List] = None) -> Dict:
    entry_points = iter_entry_points(_NAMESPACE)
    plugins_classes = [ep.load() for ep in entry_points]
    if extra_plugins is not None:
        plugins_classes.extend(extra_plugins)

    members = {}
    for cls in plugins_classes:
        members.update({n: v for n, v in inspect.getmembers(cls) if not n.startswith('__')})

    return members


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
    plugins = _plugins_dict(extra_plugins=extra_plugins)
    client = RgdClient(api_url, username, password, save)
    for name, cls in plugins.items():
        instance = cls(clone_session(client.session))
        setattr(client, name, instance)

    return client
