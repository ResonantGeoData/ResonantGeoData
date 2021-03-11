from typing import Dict, Iterator, Optional
from base64 import b64encode
from requests_toolbelt.sessions import BaseUrlSession


__version__ = '0.0000'


class RgdcSession(BaseUrlSession):
    def __init__(self, base_url: str, credentials: Optional[str] = None):
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

        if credentials:
            encoded = b64encode(credentials.encode('utf-8'))
            self.headers['Authorization'] = f'Basic {encoded.decode()}'


class RGDC:
    def __init__(self, base_url: str, credentials: Optional[str] = None):
        self.session = RgdcSession(base_url=base_url, credentials=credentials)

    # TODO: Improve return type to something more specific than Dict
    def list_image_entry_tiles(self, image_entry_id: str) -> Dict:
        """List geodata imagery image_entry tiles."""
        r = self.session.get(f'geodata/imagery/image_entry/{image_entry_id}/tiles')
        r.raise_for_status()

        return r

    def download_image_entry_file(self, image_entry_id: str) -> Iterator[bytes]:
        """Download the associated ImageFile data for this ImageEntry directly from S3."""
        r = self.session.get(f'geodata/imagery/image_entry/{image_entry_id}/data', stream=True)
        r.raise_for_status()

        return r.iter_content()
