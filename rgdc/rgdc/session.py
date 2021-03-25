from base64 import b64encode
from typing import Optional

from requests_toolbelt.sessions import BaseUrlSession

from .utils import DEFAULT_RGD_API

__version__ = '0.0000'


class RgdcSession(BaseUrlSession):
    def __init__(
        self,
        base_url: str = DEFAULT_RGD_API,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize a session with a ResonantGeoData server.

        base_url: The base API URL of the server
        credentials: User credentials to the server, of the form username:password
        """
        base_url = f'{base_url.rstrip("/")}/'  # tolerate input with or without trailing slash
        super().__init__(base_url=base_url)
        self.headers.update(
            {
                'User-agent': f'rgdc/{__version__}',
                'Accept': 'application/json',
            }
        )

        if username and password:
            encoded = b64encode(f'{username}:{password}'.encode('utf-8'))
            self.headers['Authorization'] = f'Basic {encoded.decode()}'
