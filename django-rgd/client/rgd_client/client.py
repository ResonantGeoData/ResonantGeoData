import getpass
import logging
import os
from typing import List, Optional, Type

import requests

from .plugin import CorePlugin
from .session import RgdClientSession, clone_session
from .utils import API_KEY_DIR_PATH, API_KEY_FILE_NAME, DEFAULT_RGD_API

logger = logging.getLogger(__name__)


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
        api_key = _read_api_key(api_url=api_url, username=username, password=password)
        if api_key is None:
            if username is not None and password is None:
                password = getpass.getpass()

            # Get an API key for this user and save it to disk
            if username and password:
                api_key = _get_api_key(api_url, username, password, save)
                if api_key is None:
                    logger.error(
                        'Failed to retrieve API key; are your username and password correct?'
                    )

        self.session = RgdClientSession(base_url=api_url, auth_token=api_key)
        self.rgd = CorePlugin(clone_session(self.session))

    def clear_token(self):
        """Delete a locally-stored API key."""
        (API_KEY_DIR_PATH / API_KEY_FILE_NAME).unlink(missing_ok=True)


def _get_api_key(api_url: str, username: str, password: str, save: bool) -> Optional[str]:
    """Get an RGD API Key for the given user from the server, and save it if requested."""
    resp = requests.post(f'{api_url}/api-token-auth', {'username': username, 'password': password})
    token = resp.json().get('token')
    if token is None:
        return None
    if save:
        API_KEY_DIR_PATH.mkdir(parents=True, exist_ok=True)
        with open(API_KEY_DIR_PATH / API_KEY_FILE_NAME, 'w') as fd:
            fd.write(token)
    return token


def _read_api_key(api_url: str, username: str = None, password: str = None) -> Optional[str]:
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
            api_key = fd.readline().strip()
    except FileNotFoundError:
        return None

    # Make sure API key works by hitting a protected endpoint
    resp = requests.get(f'{api_url}/rgd/collection', headers={'Authorization': f'Token {api_key}'})

    # If it doesn't, try to get a new one and save it to ~/.rgd/token, as the current one is corrupted
    if resp.status_code == 401:
        logger.error('API key is invalid.')
        # If username + password were provided, try to get a new API key with them
        if username is not None and password is not None:
            logger.info('Attempting to fetch a new API key...')
            api_key = _get_api_key(api_url, username, password, save=True)
            if api_key is not None:
                logger.info('Succeeded.')
            return api_key
        else:
            logger.error('Provide your username and password next time to fetch a new one.')
            return None

    return api_key


def create_rgd_client(
    api_url: str = DEFAULT_RGD_API,
    username: Optional[str] = None,
    password: Optional[str] = None,
    save: Optional[bool] = True,
    extra_plugins: Optional[List[Type]] = None,
):
    # Avoid circular import
    from ._plugin_utils import _inject_plugin_deps, _plugin_classes, _plugin_instances

    # Create initial client
    client = RgdClient(api_url, username, password, save)

    # Perform plugin initialization
    plugin_classes = _plugin_classes(extra_plugins=extra_plugins)
    plugin_instances = _plugin_instances(client, plugin_classes)
    _inject_plugin_deps(plugin_instances)

    return client
