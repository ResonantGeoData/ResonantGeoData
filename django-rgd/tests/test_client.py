import json
from pathlib import Path
from typing import Optional

import pytest
from requests.exceptions import HTTPError
from rgd.models import ChecksumFile, Collection
from rgd_client import RgdClient, create_rgd_client
from rgd_client.utils import API_KEY_DIR_PATH, API_KEY_FILE_NAME


@pytest.mark.django_db(transaction=True)
def test_basic_search(py_client: RgdClient, spatial_asset_a):
    bbox = {
        'type': 'Polygon',
        'coordinates': [
            [
                [-84.10240173339842, 39.72989765591686],
                [-84.0395736694336, 39.72989765591686],
                [-84.0395736694336, 39.78057429170315],
                [-84.10240173339842, 39.78057429170315],
                [-84.10240173339842, 39.72989765591686],
            ]
        ],
    }

    q = py_client.rgd.search(query=json.dumps(bbox), predicate='intersects')
    assert len(q) == 1


@pytest.mark.django_db(transaction=True)
def test_create_file_from_url(py_client: RgdClient, checksum_file_url: ChecksumFile):
    """Test that creation of a ChecksumFile with a URL succeeds."""
    file_dict = py_client.rgd.create_file_from_url(checksum_file_url.get_url())
    assert file_dict['url'] == checksum_file_url.get_url()
    assert file_dict['type'] == 2


@pytest.mark.django_db(transaction=True)
def test_create_file_from_url_existing(
    py_client: RgdClient, checksum_file_url: ChecksumFile, collection: Collection
):
    """Test that create with an existing URL/Collection returns the existing file."""
    checksum_file_url.collection = collection
    checksum_file_url.save()

    file_dict = py_client.rgd.create_file_from_url(
        url=checksum_file_url.get_url(), collection=collection.id
    )
    assert file_dict['id'] == checksum_file_url.id


@pytest.mark.django_db(transaction=True)
def test_tree_file_search(py_client: RgdClient, checksum_file: ChecksumFile):
    """Test that basic connection to the tree endpoint succeeds."""
    resp_dict = py_client.rgd.file_tree_search()
    assert 'folders' in resp_dict
    assert 'files' in resp_dict


@pytest.mark.django_db(transaction=True)
def test_save_api_key(live_server, user_with_api_key):
    """Test that saving an API key works correctly."""
    username, password, api_token = user_with_api_key

    create_rgd_client(
        username=username,
        password=password,
        api_url=f'{live_server.url}/api',
        save=True,  # save the API key
    )

    # Ensure ~/.rgd/token exists and contains the user's API key
    assert (API_KEY_DIR_PATH / API_KEY_FILE_NAME).read_text() == api_token


@pytest.mark.django_db(transaction=True)
def test_invalid_local_api_key(live_server, user_with_api_key):
    """Test that a new API key is fetched when the one on disk is invalid."""
    username, password, api_token = user_with_api_key

    # Save invalid API key to disk so `create_rgd_client` attempts to use it
    (API_KEY_DIR_PATH / API_KEY_FILE_NAME).write_text(f'{api_token}_bad')

    create_rgd_client(
        username=username,
        password=password,
        api_url=f'{live_server.url}/api',
        save=True,  # save the API key
    )

    # Ensure that `create_rgd_client` overwrote the invalid key with a fresh one
    assert (API_KEY_DIR_PATH / API_KEY_FILE_NAME).read_text() == api_token


@pytest.mark.django_db(transaction=True)
def test_invalid_env_var_api_key(live_server, user_with_api_key, monkeypatch):
    """Test that a new API key is *not* fetched when one provided via env var is invalid."""
    username, password, api_token = user_with_api_key
    monkeypatch.setenv('RGD_API_TOKEN', api_token)

    # Make sure ~/.rgd/token doesn't exist
    (API_KEY_DIR_PATH / API_KEY_FILE_NAME).unlink(missing_ok=True)
    assert not (API_KEY_DIR_PATH / API_KEY_FILE_NAME).exists()

    create_rgd_client(
        username=username,
        password=password,
        api_url=f'{live_server.url}/api',
        save=True,  # save the API key
    )

    # Make sure ~/.rgd/token wasn't created
    assert not (API_KEY_DIR_PATH / API_KEY_FILE_NAME).exists()


@pytest.mark.django_db(transaction=True)
def test_api_url_trailing_slash(live_server, user_with_api_key, checksum_file_url: ChecksumFile):
    url: str = live_server.url

    # Ensure url doesn't end with a trailing slash already
    if url.endswith('/'):
        url = url.rstrip('/')

    username, password, _ = user_with_api_key

    py_client = create_rgd_client(
        username=username,
        password=password,
        api_url=f'{url}/api/',  # append a trailing slash to url
    )
    assert py_client.session.base_url == f'{url}/api/'

    # Make sure the client behaves as expected given a trailing slash
    file_dict = py_client.rgd.create_file_from_url(checksum_file_url.get_url())
    assert file_dict['url'] == checksum_file_url.get_url()


@pytest.mark.django_db(transaction=True)
def test_invalid_api_url(live_server, user_with_api_key, monkeypatch):
    """Test that the client fails loudly when given an invalid API URL."""
    url: str = live_server.url
    username, password, api_key = user_with_api_key

    monkeypatch.setenv('RGD_API_TOKEN', api_key)

    with pytest.raises(HTTPError):
        create_rgd_client(
            username=username,
            password=password,
            api_url=f'{url}/invalid',
        )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    # Test cases: when download_location is None, and when it is a valid string
    'download_path,expected_download_directory,use_id',
    [
        (None, Path.cwd(), False),
        (Path('~/.rgd/temp').expanduser(), Path('~/.rgd/temp').expanduser(), False),
        (None, Path.cwd(), True),
        (Path('~/.rgd/temp').expanduser(), Path('~/.rgd/temp').expanduser(), True),
    ],
)
def test_file_download(
    py_client: RgdClient,
    checksum_file: ChecksumFile,
    download_path: Optional[Path],
    expected_download_directory: Optional[Path],
    use_id: bool,
):
    expected_download_path: Path = expected_download_directory / (
        str(checksum_file.id) if use_id else checksum_file.name
    )

    # Remove file if it already exists
    expected_download_path.unlink(missing_ok=True)

    # Download file and make sure it exists and the contents are as expected.
    download_path = py_client.rgd.download_checksum_file_to_path(
        checksum_file.id, download_path, use_id=use_id
    )

    assert download_path == expected_download_path
    assert expected_download_path.read_bytes() == checksum_file.file.file.read()


@pytest.mark.django_db(transaction=True)
def test_invalid_file_download(py_client: RgdClient, checksum_file: ChecksumFile):
    """Test that attempting to download a non-existent file fails properly."""
    checksum_file.delete()

    with pytest.raises(HTTPError) as error:
        py_client.rgd.download_checksum_file_to_path(checksum_file.id)

    # Make sure it was a 404 error
    assert error.match(r'404 Client Error')


@pytest.mark.django_db(transaction=True)
def test_file_download_keep_existing(
    tmp_path: Path, py_client: RgdClient, checksum_file: ChecksumFile
):
    # Save a file where the client would normally put the downloaded file
    file_path = tmp_path / str(checksum_file.id)
    existing_file_content: bytes = b'foobar'

    with open(file_path, 'wb') as f:
        f.write(existing_file_content)

    # Make sure the file isn't modified
    assert existing_file_content == file_path.read_bytes()
    py_client.rgd.download_checksum_file_to_path(
        checksum_file.id, tmp_path, keep_existing=True, use_id=True
    )
    assert existing_file_content == file_path.read_bytes()

    # Make sure the file *is* modified
    py_client.rgd.download_checksum_file_to_path(
        checksum_file.id, tmp_path, keep_existing=False, use_id=True
    )
    assert existing_file_content != file_path.read_bytes()
