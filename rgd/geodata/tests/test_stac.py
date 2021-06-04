import pytest

from rgd.geodata.serializers import STACRasterSerializer


def _check_conforms_stac(data):
    assert 'stac_version' in data
    assert 'assets' in data
    # TODO: make this better


@pytest.mark.django_db(transaction=True)
def test_raster_stac_serializer_simple(admin_api_client, sample_raster_a):
    id = sample_raster_a.id
    response = admin_api_client.get(f'/api/geodata/imagery/raster/{id}/stac')
    assert response.status_code == 200
    data = response.data
    assert data
    _check_conforms_stac(data)
    assets = data['assets']
    assert len(assets) == 1


@pytest.mark.django_db(transaction=True)
def test_raster_stac_serializer_multi_file_bands(admin_api_client, sample_raster_multi):
    id = sample_raster_multi.id
    response = admin_api_client.get(f'/api/geodata/imagery/raster/{id}/stac')
    assert response.status_code == 200
    data = response.data
    assert data
    _check_conforms_stac(data)
    assets = data['assets']
    assert len(assets) == 3


@pytest.mark.django_db(transaction=True)
def test_raster_stac_export_import(admin_api_client, sample_raster_a):
    data = STACRasterSerializer(sample_raster_a).data
    instance = STACRasterSerializer().create(data)
    assert instance
    # TODO: versify instance == sample_raster_a

    # Same for ImageFile/ImageEntry
    assert instance.parent_raster.image_set.images.count() == sample_raster_a.parent_raster.image_set.images.count()

    # Same for ancillary files
    assert instance.parent_raster.ancillary_files.count() == sample_raster_a.parent_raster.ancillary_files.count()

    # Get checksum files and make sure they are actually the same (no duplicates)

    # Asset outline/footprint of rasters are the same
    assert instance.footprint == sample_raster_a.footprint
    assert instance.outline == sample_raster_a.outline
