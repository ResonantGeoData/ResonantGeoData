from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List

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


def download_checksum_file_to_path(file: Dict, path: Path, overwrite: bool):
    """
    Download a RGD ChecksumFile to a given path.

    Args:
        file: A RGD ChecksumFile serialized as a Dict.
        path: The root path to download this file to.
        overwrite: if True, replace files existing on disk

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
    if not file_path.is_file() or overwrite:
        with open(file_path, 'wb') as open_file_path:
            for chunk in iterate_response_bytes(file_download_url):
                open_file_path.write(chunk)

    return file_path
