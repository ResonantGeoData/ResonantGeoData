import json

import pytest
from rgd.datastore import datastore
from rgd_imagery import models
from rgd_imagery.stac.serializers import ItemSerializer


@pytest.mark.django_db(transaction=True)
def test_raster_stac_serializer_simple(admin_api_client, sample_raster_url_single):
    id = sample_raster_url_single.pk
    response = admin_api_client.get(f'/api/rgd_imagery/raster/{id}/stac')
    assert response.status_code == 200
    data = response.data
    assert data
    assets = data['assets']
    assert len(assets) == 2


@pytest.mark.django_db(transaction=True)
def test_raster_stac_serializer_multi_file_bands(admin_api_client, sample_raster_url):
    id = sample_raster_url.pk
    response = admin_api_client.get(f'/api/rgd_imagery/raster/{id}/stac')
    assert response.status_code == 200
    data = response.data
    assert data
    assets = data['assets']
    assert len(assets) == 4


@pytest.mark.django_db(transaction=True)
def test_eo_serialize(admin_api_client, sample_raster_url):
    id = sample_raster_url.pk
    response = admin_api_client.get(f'/api/rgd_imagery/raster/{id}/stac')
    data = response.data
    for asset in data['assets'].values():
        if 'data' in asset.get('roles', []):
            assert 'eo:bands' in asset
            bands = asset['eo:bands']
            for band in bands:
                assert 'name' in band and band['name'].startswith('B')
                assert 'common_name' in band or (
                    'center_wavelength' in band and 'full_width_half_max' in band
                )
