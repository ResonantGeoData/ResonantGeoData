import json

import pytest

from rgd.geodata import models
from rgd.geodata.datastore import datastore

from . import factories


@pytest.fixture()
def arbitrary_file():
    return factories.ArbitraryFileFactory()


@pytest.fixture()
def landsat_image():
    name = 'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band1.tif'
    imagefile = factories.ImageFileFactory(
        file__filename=name,
        file__from_path=datastore.fetch(name),
    )
    return imagefile.baseimagefile_ptr.imageentry


@pytest.fixture()
def astro_image():
    name = 'astro.png'
    imagefile = factories.ImageFileFactory(
        file__filename=name,
        file__from_path=datastore.fetch(name),
    )
    return imagefile.baseimagefile_ptr.imageentry


@pytest.fixture()
def landsat_raster():
    name = 'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band1.tif'
    imagefile = factories.ImageFileFactory(
        file__filename=name,
        file__from_path=datastore.fetch(name),
    )
    image_set = factories.ImageSetFactory(
        images=[imagefile.baseimagefile_ptr.imageentry.id],
    )
    raster = factories.RasterEntryFactory(
        name=name,
        image_set=image_set,
    )
    raster.refresh_from_db()
    return raster


@pytest.mark.django_db(transaction=True)
def test_download_file(client, arbitrary_file):
    model = 'ArbitraryFile'
    id = arbitrary_file.id
    field = 'file'
    result = client.get(f'/api/geodata/download/{model}/{id}/{field}')
    assert result.status_code == 200
    with pytest.raises(AttributeError):
        # Test bad model
        client.get('/api/geodata/download/Foo/0/file')
    with pytest.raises(AttributeError):
        # Test good model, bad field
        client.get(f'/api/geodata/download/{model}/{id}/foo')


@pytest.mark.django_db(transaction=True)
def test_get_status(client, astro_image):
    model = 'ImageFile'
    id = astro_image.image_file.imagefile.id
    result = client.get(f'/api/geodata/status/{model}/{id}')
    assert result.status_code == 200
    with pytest.raises(AttributeError):
        client.get(f'/api/geodata/status/Foo/{id}')


@pytest.mark.django_db(transaction=True)
def test_download_arbitry_file(client, arbitrary_file):
    pk = arbitrary_file.pk
    result = client.get(f'/api/geodata/common/arbitrary_file/{pk}/data')
    assert result.status_code == 302 or result.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_download_image_entry_file(client, astro_image):
    pk = astro_image.pk
    result = client.get(f'/api/geodata/imagery/image_entry/{pk}/data')
    assert result.status_code == 302 or result.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_get_arbitrary_file(client, arbitrary_file):
    pk = arbitrary_file.pk
    content = json.loads(client.get(f'/api/geodata/common/arbitrary_file/{pk}/').content)
    assert content
    # Check that a hyperlink is given to the file data
    # NOTE: tried using the URLValidator from django but it thinks this URL is invalid
    assert content['file'].startswith('http')


@pytest.mark.django_db(transaction=True)
def test_get_spatial_entry(client, landsat_raster):
    """Test individual GET for SpatialEntry model."""
    pk = landsat_raster.rastermetaentry.spatial_id
    content = json.loads(client.get(f'/api/geodata/common/spatial_entry/{pk}/').content)
    assert content
    assert content['footprint']
    assert content['outline']


@pytest.mark.django_db(transaction=True)
def test_create_get_subsampled_image(client, astro_image):
    """Test POST and GET for SubsampledImage model."""
    client.post(
        '/api/geodata/imagery/subsample',
        {
            'source_image': astro_image.id,
            'sample_type': 'pixel box',
            'sample_parameters': {'umax': 100, 'umin': 0, 'vmax': 200, 'vmin': 0},
        },
    )
    # TODO: wait for the task kicked of by POST to complete?
    sub = models.imagery.SubsampledImage.objects.get(source_image=landsat_image.id)
    assert sub.data
    # Test the GET
    content = json.loads(client.get(f'/api/geodata/imagery/subsample/{sub.id}/').content)
    assert content


@pytest.mark.django_db(transaction=True)
def test_create_and_download_cog(client, landsat_image):
    """Test POST for ConvertedImageFile model."""
    client.post(
        '/api/geodata/imagery/cog',
        {'source_image': landsat_image.id},
    )
    # Check that a COG was generated
    cog = models.imagery.ConvertedImageFile.objects.get(source_image=landsat_image.id)
    # NOTE: This doesn't actually verify the file is in COG format. Assumed.
    assert cog.converted_file
    # Also test download endpoint here:
    pk = cog.pk
    result = client.get(f'/api/geodata/imagery/cog/{pk}/data')
    assert result.status_code == 302 or result.status_code == 200
