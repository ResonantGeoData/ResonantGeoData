from base64 import b64encode
from copy import deepcopy
import getpass
import inspect
from typing import Dict, List, Optional, Type
from pkg_resources import iter_entry_points

from .plugin import CorePlugin
from .session import clone_session, RgdClientSession
from .utils import DEFAULT_RGD_API


_NAMESPACE = 'rgd_client.plugin'


class RgdClient:
    def __init__(
        self,
        api_url: str = DEFAULT_RGD_API,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        """
        Initialize the base RGD Client.

        Args:
            api_url: The base url of the RGD API instance.
            username: The username to authenticate to the instance with, if any.
            password: The password associated with the provided username. If None, a prompt will be provided.

        Returns:
            A base RgdClient instance.
        """
        auth_header = None

        if username is not None and password is None:
            password = getpass.getpass()

        if username and password:
            encoded_credentials = b64encode(f"{username}:{password}".encode("utf-8")).decode()
            auth_header = f"Basic {encoded_credentials}"

        self.session = RgdClientSession(base_url=api_url, auth_header=auth_header)
        self.rgd = CorePlugin(clone_session(self.session))


def _plugins_dict(extra_plugins: Optional[List] = None) -> Dict:
    entry_points = iter_entry_points(_NAMESPACE)
    plugins_classes = [ep.load() for ep in entry_points]
    if extra_plugins is not None:
        plugins_classes.extend(extra_plugins)

    members = {}
    for cls in plugins_classes:
        members.update({n: v for n, v in inspect.getmembers(cls) if not n.startswith("__")})

    return members


def create_rgd_client(
    api_url: str = DEFAULT_RGD_API,
    username: Optional[str] = None,
    password: Optional[str] = None,
    extra_plugins: Optional[List[Type]] = None,
):
    plugins = _plugins_dict(extra_plugins=extra_plugins)
    client = RgdClient(api_url, username, password)
    for name, cls in plugins.items():
        instance = cls(clone_session(client.session))
        setattr(client, name, instance)

    return client
