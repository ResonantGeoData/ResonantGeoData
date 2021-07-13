import pystac
import pytest
from rgd_imagery import models
from rgd_imagery.serializers import STACRasterSerializer


def _check_conforms_stac(data):
    assert 'stac_version' in data
    assert 'assets' in data
    item = pystac.Item.from_dict(data)  # noqa
    # TODO:
    # errors = item.validate()
    # if errors:
    #     raise ValueError('ilformed STAC Item.')


@pytest.mark.django_db(transaction=True)
def test_raster_stac_serializer_simple(admin_api_client, sample_raster_url_single):
    id = sample_raster_url_single.pk
    response = admin_api_client.get(f'/rgd_imagery_test/api/rgd_imagery/raster/{id}/stac')
    assert response.status_code == 200
    data = response.data
    assert data
    _check_conforms_stac(data)
    assets = data['assets']
    assert len(assets) == 2


@pytest.mark.django_db(transaction=True)
def test_raster_stac_serializer_multi_file_bands(admin_api_client, sample_raster_url):
    id = sample_raster_url.pk
    response = admin_api_client.get(f'/rgd_imagery_test/api/rgd_imagery/raster/{id}/stac')
    assert response.status_code == 200
    data = response.data
    assert data
    _check_conforms_stac(data)
    assets = data['assets']
    assert len(assets) == 4


@pytest.mark.django_db(transaction=True)
def test_eo_serialize(admin_api_client, sample_raster_url):
    id = sample_raster_url.pk
    response = admin_api_client.get(f'/rgd_imagery_test/api/rgd_imagery/raster/{id}/stac')
    data = response.data
    _check_conforms_stac(data)
    for asset in data['assets'].values():
        if 'data' in asset.get('roles', []):
            assert 'eo:bands' in asset
            bands = asset['eo:bands']
            for band in bands:
                assert 'name' in band and band['name'].startswith('B')
                assert 'common_name' in band or (
                    'center_wavelength' in band and 'full_width_half_max' in band
                )


@pytest.mark.django_db(transaction=True)
def test_raster_stac_export_import(admin_api_client, sample_raster_url):
    sample = sample_raster_url
    data = STACRasterSerializer(sample).data
    instance = STACRasterSerializer().create(data)
    # Check Image/ImageMeta
    assert (
        instance.parent_raster.image_set.images.count()
        == sample.parent_raster.image_set.images.count()
    )
    # Since testing URL files, make sure there are no duplicates
    assert set(instance.parent_raster.image_set.images.all()) == set(
        sample.parent_raster.image_set.images.all()
    )
    # Get checksum files and make sure they are actually the same (no duplicates)

    # Same for ancillary files
    assert (
        instance.parent_raster.ancillary_files.count()
        == sample.parent_raster.ancillary_files.count()
    )
    assert set(instance.parent_raster.ancillary_files.all()) == set(
        sample.parent_raster.ancillary_files.all()
    )

    # Asset outline/footprint of rasters are the same
    assert instance.footprint.equals(sample.footprint)
    # assert instance.outline.equals(sample.outline)

    # Check that no duplicate data were produced
    assert instance.pk == sample.pk

    # assert that bands were made
    assert models.BandMeta.objects.count() == models.BandMeta.objects.count() > 0
