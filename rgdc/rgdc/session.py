from typing import Optional

from requests_toolbelt.sessions import BaseUrlSession
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from .version import __version__


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


def retry_RgdcSession(*args, retries: Optional[int] = 5, **kwargs):
    """
    Initialize a session with a ResonantGeoData server with automatic retries.

    See RgdcSession for args.

    References:
        https://www.peterbe.com/plog/best-practice-with-retries-with-requests
        https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/
    """
    session = RgdcSession(*args, **kwargs)
    retry = Retry(
        total=retries, status_forcelist=[429, 503], method_whitelist=['GET'], backoff_factor=1
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)

    return session
