import copy
from typing import Optional

from requests import Response
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests_toolbelt.sessions import BaseUrlSession

from ._version import __version__


class RgdClientSession(BaseUrlSession):
    def __init__(self, base_url: str, auth_token: Optional[str] = None, retries: Optional[int] = 5):
        """
        Initialize a session with a Resonant GeoData server.

        base_url: The base url of the RGD API instance.
        auth_header: If provided, set as the `Authorization` header on each request
        retries: Number of times to retry a failed request

        References:
            https://www.peterbe.com/plog/best-practice-with-retries-with-requests
            https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/
        """
        base_url = f'{base_url.rstrip("/")}/'  # tolerate input with or without trailing slash
        super().__init__(base_url=base_url)
        self.headers.update(
            {
                'User-agent': f'rgd_client/{__version__}',
                'Accept': 'application/json',
            }
        )

        if auth_token:
            self.headers['Authorization'] = f'Token {auth_token}'

        self.rgd_auth_token = auth_token

        retry = Retry(
            total=retries, status_forcelist=[429, 503], method_whitelist=['GET'], backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.mount('https://', adapter)
        self.mount('http://', adapter)

        # Define hook to assert that a request succeeded
        def assert_status_hook(response: Response, *args, **kwargs):
            response.raise_for_status()

        # Response field is present by default
        self.hooks['response'].append(assert_status_hook)


def clone_session(session: RgdClientSession):
    """
    Clone an existing RgdClientSession.

    This is necessary as simply calling `copy.deepcopy` won't suffice, due to
    BaseUrlSession defining `base_url` and `rgd_auth_token` as a class/static
    variables. Since copy.deepcopy doesn't copy class variables, `base_url` is
    `None` in the copied instance.
    """
    new_session = copy.deepcopy(session)
    new_session.base_url = session.base_url
    new_session.rgd_auth_token = session.rgd_auth_token

    return new_session
