from datetime import datetime
import json
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import Dict, Generator, Iterator, List, Optional, Tuple, Union

from geomet import wkt
import requests
from requests import Response, Session

from .types import DATETIME_OR_STR_TUPLE, SEARCH_PREDICATE_CHOICE

DEFAULT_RGD_API = 'https://www.resonantgeodata.com/api'

API_KEY_DIR_PATH = Path('~/.rgd/').expanduser()
API_KEY_FILE_NAME = 'token'


def pager(session: Session, url: str, **kwargs) -> Iterator[Response]:
    """Exhaust a DRF Paginated list."""
    while True:
        r = session.get(url, **kwargs)
        yield r

        if 'next' in r.links:
            url = r.links['next']['url']
        else:
            break


def limit_offset_pager(session: Session, url: str, **kwargs) -> Generator[Dict, None, None]:
    """Exhaust a DRF Paginated list, respecting limit/offset."""
    # Default params kwarg
    if not kwargs.get('params'):
        kwargs['params'] = {}

    params: Optional[Dict] = kwargs['params']
    total_limit = params.get('limit')

    # Default offset
    if params.get('offset') is None:
        params['offset'] = 0

    num_results = 0
    while True:
        # Update limit
        if total_limit:
            params['limit'] = total_limit - num_results

        # Make request and raise exception if failed
        r = session.get(url, **kwargs)
        r.raise_for_status()

        # Yield results
        results = r.json()['results']
        yield from results

        # Update offset and num_results
        params['offset'] += len(results)
        num_results += len(results)

        # Check if there is no more data, or if we've reached our limit
        no_more_data = 'next' not in r.links or not results
        limit_reached = total_limit and num_results >= total_limit
        if no_more_data or limit_reached:
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


def datetime_to_time(value: object):
    """Convert datetime objects to HH:MM strings."""
    if value is not None:
        if isinstance(value, datetime):
            return value.strftime('%H:%M')

    return value


def order_datetimes(value1: object, value2: object):
    """
    Sort 2 objects if they are datetimes.

    Example:
        >>> from rgd_client.utils import *  # NOQA
        >>> value1 = datetime.fromisoformat('2000-01-01T00:13:30')
        >>> value2 = datetime.fromisoformat('1999-01-01T00:13:30')
        >>> result = order_datetimes(value1, value2)
        >>> assert len(result) == 2
    """
    if isinstance(value1, datetime) and isinstance(value2, datetime):
        return (value1, value2) if value1 < value2 else (value2, value1)

    return value1, value2


def download_checksum_file_to_path(file: Dict, path: Path, keep_existing: bool):
    """
    Download a RGD ChecksumFile to a given path.

    Args:
        file: A RGD ChecksumFile serialized as a Dict.
        path: The root path to download this file to.
        keep_existing: If False, replace files existing on disk.

    Returns:
        The path on disk the file was downloaded to.
    """
    filepath = file.get('name')
    file_download_url = file.get('download_url')

    # Skip image if some fields are missing
    if not (file and filepath and file_download_url):
        # TODO: throw a warning to let user know this file failed
        return

    # Parse file path to identifiy nested directories
    filepath: str = filepath.lstrip('/')
    split_filepath: List[str] = filepath.split('/')
    parent_dirname = '/'.join(split_filepath[:-1])
    filename = split_filepath[-1]

    # Create nested directory if necessary
    parent_path = path / parent_dirname if parent_dirname else path
    parent_path.mkdir(parents=True, exist_ok=True)

    # Download contents to file
    file_path = parent_path / filename
    if not (file_path.is_file() and keep_existing):
        with open(file_path, 'wb') as open_file_path:
            for chunk in iterate_response_bytes(file_download_url):
                open_file_path.write(chunk)

    return file_path


def spatial_subentry_id(search_result):
    """Get the id of a returned SpatialEntry."""
    if 'stac_version' in search_result:
        return search_result['id']
    return search_result['spatial_id']


def spatial_search_params(
    query: Optional[Union[Dict, str]] = None,
    predicate: Optional[SEARCH_PREDICATE_CHOICE] = None,
    relates: Optional[str] = None,
    distance: Optional[Tuple[float, float]] = None,
    acquired: Optional[DATETIME_OR_STR_TUPLE] = None,
    instrumentation: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    time_of_day: Optional[DATETIME_OR_STR_TUPLE] = None,
) -> Dict:
    # The dict that will be used to store params.
    # Initialize with queries that won't be additionally processed.
    params = {
        'predicate': predicate,
        'relates': relates,
        'instrumentation': instrumentation,
        'limit': limit,
        'offset': offset,
    }

    if query:
        if isinstance(query, str):
            try:
                query = json.loads(query)
            except JSONDecodeError:
                pass

        if isinstance(query, dict):
            # Allow failure on invalid format
            query = wkt.dumps(query)

        params['q'] = query

    # Process range params

    if distance and len(distance) == 2:
        dmin, dmax = distance
        params['distance_min'] = dmin
        params['distance_max'] = dmax

    # TODO: Determine if the before/after param order needs to be swapped?
    if acquired and len(acquired) == 2:
        amin, amax = order_datetimes(*acquired)
        params['acquired_before'] = datetime_to_str(amax)
        params['acquired_after'] = datetime_to_str(amin)

    if time_of_day and len(time_of_day) == 2:
        after, before = order_datetimes(*time_of_day)
        params['time_of_day_after'] = datetime_to_time(after)
        params['time_of_day_before'] = datetime_to_time(before)

    return params
