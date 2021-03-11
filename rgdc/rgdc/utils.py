from typing import Iterator

from requests import Response, Session


def pager(session: Session, url: str) -> Iterator[Response]:
    """Exhaust a DRF Paginated list."""

    while True:
        r = session.get(url)
        yield r

        if 'next' in r.links:
            url = r.links['next']
        else:
            break


def results(responses: Iterator[Response]) -> Iterator[dict]:
    for response in responses:
        response.raise_for_status()
        for result in response.json()['results']:
            yield result
