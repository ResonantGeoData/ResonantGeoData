from datetime import datetime
from typing import Iterator

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


def results(responses: Iterator[Response]) -> Iterator[dict]:
    for response in responses:
        response.raise_for_status()
        for result in response.json()['results']:
            yield result


def datetime_to_str(value: object):
    """Convert datetime objects to ISO8601 strings."""
    if value is not None:
        if isinstance(value, datetime):
            return value.isoformat()

    return value
