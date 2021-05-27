import pytest


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
