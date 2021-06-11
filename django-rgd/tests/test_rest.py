import pytest
from rest_framework import status


@pytest.mark.django_db(transaction=True)
def test_get_status(admin_api_client, astro_image):
    model = 'ChecksumFile'
    id = astro_image.image_file.imagefile.id
    response = admin_api_client.get(f'/api/geodata/status/{model}/{id}')
    assert response.status_code == 200
    assert response.data
    with pytest.raises(AttributeError):
        admin_api_client.get(f'/api/geodata/status/Foo/{id}')


@pytest.mark.django_db(transaction=True)
def test_download_checksum_file(admin_api_client, checksum_file):
    pk = checksum_file.pk
    response = admin_api_client.get(f'/api/geodata/common/checksum_file/{pk}/data')
    assert status.is_redirect(response.status_code)


@pytest.mark.django_db(transaction=True)
def test_download_checksum_file_url(admin_api_client, checksum_file_url):
    pk = checksum_file_url.pk
    response = admin_api_client.get(f'/api/geodata/common/checksum_file/{pk}/data')
    assert status.is_redirect(response.status_code)


@pytest.mark.django_db(transaction=True)
def test_get_checksum_file(admin_api_client, checksum_file):
    pk = checksum_file.pk
    content = admin_api_client.get(f'/api/geodata/common/checksum_file/{pk}').data
    assert content
    # Check that a hyperlink is given to the file data
    # NOTE: tried using the URLValidator from django but it thinks this URL is invalid
    assert content['file'].startswith('http')


@pytest.mark.django_db(transaction=True)
def test_get_spatial_entry(api_client, sample_raster_a):
    """Test individual GET for SpatialEntry model."""
    pk = sample_raster_a.rastermetaentry.spatial_id
    response = api_client.get(f'/api/geodata/common/spatial_entry/{pk}')
    assert response.status_code == 200
    assert response.data
    assert response.data['outline']
