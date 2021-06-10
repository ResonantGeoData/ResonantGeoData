import pytest
from rest_framework import status

from rgd.geodata import models


@pytest.mark.django_db(transaction=True)
def test_get_status(admin_api_client, astro_image):
    model = 'ImageFile'
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
def test_download_image_entry_file(admin_api_client, astro_image):
    pk = astro_image.pk
    response = admin_api_client.get(f'/api/geodata/imagery/{pk}/data')
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


@pytest.mark.django_db(transaction=True)
def test_create_get_subsampled_image(admin_api_client, astro_image):
    """Test POST and GET for SubsampledImage model."""
    payload = {
        'source_image': astro_image.pk,
        'sample_type': 'pixel box',
        'sample_parameters': {'right': 100, 'left': 0, 'top': 200, 'bottom': 0},
    }
    response = admin_api_client.post('/api/geoprocess/imagery/subsample', payload)
    assert response.status_code == 201
    assert response.data
    id = response.data['id']
    sub = models.imagery.SubsampledImage.objects.get(id=id)
    assert sub.data
    # Test the GET
    response = admin_api_client.get(f'/api/geoprocess/imagery/subsample/{id}')
    assert response.status_code == 200
    assert response.data
    # Now test to make sure the serializer prevents duplicates
    response = admin_api_client.post('/api/geoprocess/imagery/subsample', payload)
    assert response.status_code == 201
    assert response.data
    assert id == response.data['id']  # Compare against original PK


@pytest.mark.django_db(transaction=True)
def test_create_and_download_cog(admin_api_client, geotiff_image_entry):
    """Test POST for ConvertedImageFile model."""
    response = admin_api_client.post(
        '/api/geoprocess/imagery/cog',
        {'source_image': geotiff_image_entry.id},
    )
    assert response.status_code == 201
    assert response.data
    # Check that a COG was generated
    cog = models.imagery.ConvertedImageFile.objects.get(source_image=geotiff_image_entry.id)
    # NOTE: This doesn't actually verify the file is in COG format. Assumed.
    assert cog.converted_file
    # Also test download endpoint here:
    pk = cog.pk
    response = admin_api_client.get(f'/api/geoprocess/imagery/cog/{pk}/data')
    assert status.is_redirect(response.status_code)
