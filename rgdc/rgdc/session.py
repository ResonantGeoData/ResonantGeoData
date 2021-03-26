from typing import Optional

from requests_toolbelt.sessions import BaseUrlSession

__version__ = '0.0000'


class RgdcSession(BaseUrlSession):
    def __init__(self, base_url: str, auth_header: Optional[str] = None):
        """
        Initialize a session with a ResonantGeoData server.

        base_url: The base url of the RGD API instance.
        auth_header: If provided, set as the `Authorization` header on each request
        """
        base_url = f'{base_url.rstrip("/")}/'  # tolerate input with or without trailing slash
        super().__init__(base_url=base_url)
        self.headers.update(
            {
                'User-agent': f'rgdc/{__version__}',
                'Accept': 'application/json',
            }
        )

        if auth_header:
            self.headers['Authorization'] = auth_header
