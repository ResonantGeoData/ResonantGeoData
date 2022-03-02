import pytest


@pytest.mark.django_db(transaction=True)
def test_raster_stac_serializer_simple(admin_api_client, sample_raster_url_single):
    data = admin_api_client.get('/api/stac/collections/default/items').data['features'][0]
    assets = data['assets']
    assert len(assets) == 3


@pytest.mark.django_db(transaction=True)
def test_raster_stac_serializer_multi_file_bands(admin_api_client, sample_raster_url):
    data = admin_api_client.get('/api/stac/collections/default/items').data['features'][0]
    assets = data['assets']
    assert len(assets) == 7


@pytest.mark.django_db(transaction=True)
def test_eo_serialize(admin_api_client, sample_raster_url):
    data = admin_api_client.get('/api/stac/collections/default/items').data['features'][0]
    for asset in data['assets'].values():
        if 'data' in asset.get('roles', []):
            asset_properties = asset['properties']
            assert 'eo:bands' in asset_properties
            bands = asset_properties['eo:bands']
            for band in bands:
                assert 'name' in band and band['name'].startswith('B')
                assert 'common_name' in band or (
                    'center_wavelength' in band and 'full_width_half_max' in band
                )


@pytest.mark.django_db(transaction=True)
def test_optimized_query(admin_api_client, sample_raster_url, django_assert_num_queries):
    with django_assert_num_queries(1):
        admin_api_client.get('/api/stac/collections')
    with django_assert_num_queries(1):
        admin_api_client.get('/api/stac/collections/default/items')
