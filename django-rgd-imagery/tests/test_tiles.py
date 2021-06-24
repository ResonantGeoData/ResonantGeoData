import pytest


@pytest.mark.django_db(transaction=True)
def test_metadata(api_client, geotiff_image_entry):
    response = api_client.get(
        f'/rgd_imagery_test/api/image_process/imagery/{geotiff_image_entry.pk}/tiles?projection=EPSG:3857'
    )
    metadata = response.data
    assert metadata['levels'] == 15
    assert metadata['sizeX'] == metadata['sizeY']
    assert metadata['tileWidth'] == metadata['tileHeight']
    assert metadata['tileWidth'] == metadata['tileHeight']


@pytest.mark.django_db(transaction=True)
def test_tile(api_client, geotiff_image_entry):
    response = api_client.get(
        f'/rgd_imagery_test/api/image_process/imagery/{geotiff_image_entry.pk}/tiles/1/0/0.png'
    )
    assert response.status_code == 200
    assert response['Content-Type'] == 'image/png'


@pytest.mark.django_db(transaction=True)
def test_thumbnail(api_client, geotiff_image_entry):
    response = api_client.get(
        f'/rgd_imagery_test/api/image_process/imagery/{geotiff_image_entry.pk}/thumbnail'
    )
    assert response.status_code == 200
    assert response['Content-Type'] == 'image/png'
