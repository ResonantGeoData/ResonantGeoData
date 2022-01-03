from pathlib import Path

import pytest
from rest_framework import status
from rgd.models import ChecksumFile


@pytest.mark.django_db(transaction=True)
def test_swagger(admin_api_client):
    response = admin_api_client.get('/swagger/?format=openapi')
    assert status.is_success(response.status_code)


@pytest.mark.django_db(transaction=True)
def test_download_checksum_file(admin_api_client, checksum_file):
    pk = checksum_file.pk
    response = admin_api_client.get(f'/api/rgd/checksum_file/{pk}/data')
    assert status.is_redirect(response.status_code)


@pytest.mark.django_db(transaction=True)
def test_download_checksum_file_url(admin_api_client, checksum_file_url):
    pk = checksum_file_url.pk
    response = admin_api_client.get(f'/api/rgd/checksum_file/{pk}/data')
    assert status.is_redirect(response.status_code)


@pytest.mark.django_db(transaction=True)
def test_get_checksum_file(admin_api_client, checksum_file):
    pk = checksum_file.pk
    content = admin_api_client.get(f'/api/rgd/checksum_file/{pk}').data
    assert content
    # Check that a hyperlink is given to the file data
    # NOTE: tried using the URLValidator from django but it thinks this URL is invalid
    assert content['file'].startswith('http')


@pytest.mark.django_db(transaction=True)
def test_get_spatial_entry(admin_api_client, spatial_asset_a):
    """Test individual GET for SpatialEntry model."""
    pk = spatial_asset_a.spatial_id
    response = admin_api_client.get(f'/api/rgd/spatial_entry/{pk}')
    assert response.status_code == 200
    assert response.data
    assert response.data['outline']


@pytest.mark.django_db(transaction=True)
def test_get_checksum_file_tree(
    checksum_file_factory, checksum_file_url: ChecksumFile, admin_api_client
):
    """Test that the tree list endpoint functions as expected."""
    # Top level
    file1: ChecksumFile = checksum_file_factory(name='h.txt')

    # a/ directory
    file2: ChecksumFile = checksum_file_factory(name='a/f.txt')
    file3: ChecksumFile = checksum_file_factory(name='a/g.txt')

    # a/b/ directory
    file4: ChecksumFile = checksum_file_factory(name='a/b/d.txt')
    file5: ChecksumFile = checksum_file_factory(name='a/b/e.txt')

    # Put one url file in a/b/ directory
    checksum_file_url.name = 'a/b/c.jpg'
    checksum_file_url.save()
    file6 = checksum_file_url

    # Testing folders
    folder_b = [file4, file5, file6]
    folder_a = [file2, file3] + folder_b

    known_size_a = sum([f.size for f in folder_a if f.size is not None])
    a_created = min([file.created for file in folder_a]).isoformat()
    a_modified = max([file.modified for file in folder_a]).isoformat()

    known_size_b = sum([f.size for f in folder_b if f.size is not None])
    b_created = min([file.created for file in folder_b]).isoformat()
    b_modified = max([file.modified for file in folder_b]).isoformat()

    # Check top level response
    r = admin_api_client.get('/api/rgd/checksum_file/tree')
    assert r.json()['files'][file1.name]['id'] == file1.id
    assert r.json()['folders'] == {
        'a': {
            'known_size': known_size_a,
            'num_files': len(folder_a),
            'num_url_files': 1,
            'created': a_created,
            'modified': a_modified,
        }
    }

    # Search folder 'a'
    r = admin_api_client.get('/api/rgd/checksum_file/tree', {'path_prefix': 'a'})

    # Files
    files = r.json()['files']
    assert files[Path(file2.name).name]['id'] == file2.id
    assert files[Path(file3.name).name]['id'] == file3.id

    # Folders
    assert r.json()['folders'] == {
        'b': {
            'known_size': known_size_b,
            'num_files': len(folder_b),
            'num_url_files': 1,
            'created': b_created,
            'modified': b_modified,
        }
    }

    # Search folder 'a/b'
    r = admin_api_client.get('/api/rgd/checksum_file/tree', {'path_prefix': 'a/b'})

    # Files
    files = r.json()['files']
    assert files[Path(file4.name).name]['id'] == file4.id
    assert files[Path(file5.name).name]['id'] == file5.id
    assert files[Path(file6.name).name]['id'] == file6.id
