from datetime import datetime
from typing import Iterator

import requests
from requests import Response, Session

DEFAULT_RGD_API = 'https://www.resonantgeodata.com/api'


def pager(session: Session, url: str, **kwargs) -> Iterator[Response]:
    """Exhaust a DRF Paginated list."""
    while True:
        r = session.get(url, **kwargs)
        yield r

        if 'next' in r.links:
            url = r.links['next']['url']
        else:
            break


def iterate_response_bytes(
    url: str, chunk_size: int = 1024 * 1024, raise_for_status: bool = True
) -> Iterator[bytes]:
    """Return the response body as an iterator of bytes, where each item is `chunk_size` bytes long."""
    r = requests.get(url, stream=True)

    if raise_for_status:
        r.raise_for_status()

    return r.iter_content(chunk_size=chunk_size)


def datetime_to_str(value: object):
    """Convert datetime objects to ISO8601 strings."""
    if value is not None:
        if isinstance(value, datetime):
            return value.isoformat()

    return value
