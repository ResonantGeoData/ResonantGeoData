import json

import pytest
from rest_framework import status

from rgd.geodata import models
from rgd.geodata.datastore import datastore

from . import factories


@pytest.fixture()
def checksum_file():
    return factories.ChecksumFileFactory()


@pytest.fixture()
def checksum_file_url():
    return factories.ChecksumFileFactory(
        file=None,
        url=datastore.get_url('stars.png'),
        type=models.FileSourceType.URL,
    )


@pytest.fixture()
def landsat_image():
    name = 'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band1.tif'
    imagefile = factories.ImageFileFactory(
        file__file__filename=name,
        file__file__from_path=datastore.fetch(name),
    )
    return imagefile.imageentry


@pytest.fixture()
def astro_image():
    name = 'astro.png'
    imagefile = factories.ImageFileFactory(
        file__file__filename=name,
        file__file__from_path=datastore.fetch(name),
    )
    return imagefile.imageentry


@pytest.fixture()
def landsat_raster():
    name = 'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band1.tif'
    imagefile = factories.ImageFileFactory(
        file__file__filename=name,
        file__file__from_path=datastore.fetch(name),
    )
    image_set = factories.ImageSetFactory(
        images=[imagefile.imageentry.id],
    )
    raster = factories.RasterEntryFactory(
        name=name,
        image_set=image_set,
    )
    raster.refresh_from_db()
    return raster


@pytest.mark.django_db(transaction=True)
def test_get_status(api_client, astro_image):
    model = 'ImageFile'
    id = astro_image.image_file.imagefile.id
    response = api_client.get(f'/api/geodata/status/{model}/{id}')
    assert response.status_code == 200
    assert response.data
    with pytest.raises(AttributeError):
        api_client.get(f'/api/geodata/status/Foo/{id}')


@pytest.mark.django_db(transaction=True)
def test_download_checksum_file(api_client, checksum_file):
    pk = checksum_file.pk
    response = api_client.get(f'/api/geodata/common/checksum_file/{pk}/data')
    assert status.is_redirect(response.status_code)


@pytest.mark.django_db(transaction=True)
def test_download_checksum_file_url(api_client, checksum_file_url):
    pk = checksum_file_url.pk
    response = api_client.get(f'/api/geodata/common/checksum_file/{pk}/data')
    assert status.is_redirect(response.status_code)


@pytest.mark.django_db(transaction=True)
def test_download_image_entry_file(api_client, astro_image):
    pk = astro_image.pk
    response = api_client.get(f'/api/geodata/imagery/image_entry/{pk}/data')
    assert status.is_redirect(response.status_code)


@pytest.mark.django_db(transaction=True)
def test_get_checksum_file(api_client, checksum_file):
    pk = checksum_file.pk
    content = api_client.get(f'/api/geodata/common/checksum_file/{pk}').data
    assert content
    # Check that a hyperlink is given to the file data
    # NOTE: tried using the URLValidator from django but it thinks this URL is invalid
    assert content['file'].startswith('http')


@pytest.mark.django_db(transaction=True)
def test_get_spatial_entry(api_client, landsat_raster):
    """Test individual GET for SpatialEntry model."""
    pk = landsat_raster.rastermetaentry.spatial_id
    response = api_client.get(f'/api/geodata/common/spatial_entry/{pk}')
    assert response.status_code == 200
    assert response.data
    assert response.data['footprint']
    assert response.data['outline']


@pytest.mark.django_db(transaction=True)
def test_create_get_subsampled_image(api_client, astro_image):
    """Test POST and GET for SubsampledImage model."""
    payload = {
        'source_image': astro_image.pk,
        'sample_type': 'pixel box',
        'sample_parameters': json.dumps({'umax': 100, 'umin': 0, 'vmax': 200, 'vmin': 0}),
    }
    response = api_client.post('/api/geodata/imagery/subsample', payload)
    assert response.status_code == 201
    assert response.data
    pk = response.data['pk']
    sub = models.imagery.SubsampledImage.objects.get(pk=pk)
    assert sub.data
    # Test the GET
    response = api_client.get(f'/api/geodata/imagery/subsample/{pk}')
    assert response.status_code == 200
    assert response.data
    # Now test to make sure the serializer prevents duplicates
    response = api_client.post('/api/geodata/imagery/subsample', payload)
    assert response.status_code == 201
    assert response.data
    assert pk == response.data['pk']  # Compare against original PK


@pytest.mark.django_db(transaction=True)
def test_create_and_download_cog(api_client, landsat_image):
    """Test POST for ConvertedImageFile model."""
    response = api_client.post(
        '/api/geodata/imagery/cog',
        {'source_image': landsat_image.id},
    )
    assert response.status_code == 201
    assert response.data
    # Check that a COG was generated
    cog = models.imagery.ConvertedImageFile.objects.get(source_image=landsat_image.id)
    # NOTE: This doesn't actually verify the file is in COG format. Assumed.
    assert cog.converted_file
    # Also test download endpoint here:
    pk = cog.pk
    response = api_client.get(f'/api/geodata/imagery/cog/{pk}/data')
    assert status.is_redirect(response.status_code)
