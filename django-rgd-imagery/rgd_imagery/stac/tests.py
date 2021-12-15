import pytest
from rgd_imagery.stac.serializers import ItemSerializer


@pytest.mark.django_db(transaction=True)
def test_raster_stac_serializer_simple(sample_raster_url_single):
    data = ItemSerializer().to_representation(sample_raster_url_single)
    assets = data['assets']
    assert len(assets) == 2


@pytest.mark.django_db(transaction=True)
def test_raster_stac_serializer_multi_file_bands(sample_raster_url):
    data = ItemSerializer().to_representation(sample_raster_url)
    assets = data['assets']
    assert len(assets) == 4


@pytest.mark.django_db(transaction=True)
def test_eo_serialize(sample_raster_url):
    data = ItemSerializer().to_representation(sample_raster_url)
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
def test_optimized_query(admin_api_client, sample_raster_url, django_assert_num_queries):
    with django_assert_num_queries(1):
        admin_api_client.get('/api/stac/collection/default/items')
