import json

import pytest
from rgd.models import ChecksumFile
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
