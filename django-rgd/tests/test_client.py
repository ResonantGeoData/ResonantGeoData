import json

import pytest
from rgd.models.common import ChecksumFile
from rgd_client import RgdClient


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
