import pytest


@pytest.mark.django_db(transaction=True)
def test_metadata(admin_api_client, geotiff_image_entry):
    response = admin_api_client.get(
        f'/api/image_process/imagery/{geotiff_image_entry.pk}/tiles?projection=EPSG:3857'
    )
    metadata = response.data
    assert metadata['levels'] == 15
    assert metadata['sizeX'] == metadata['sizeY']
    assert metadata['tileWidth'] == metadata['tileHeight']
    assert metadata['tileWidth'] == metadata['tileHeight']


@pytest.mark.django_db(transaction=True)
def test_tile(admin_api_client, geotiff_image_entry):
    response = admin_api_client.get(
        f'/api/image_process/imagery/{geotiff_image_entry.pk}/tiles/1/0/0.png'
    )
    assert response.status_code == 200
    assert response['Content-Type'] == 'image/png'


@pytest.mark.django_db(transaction=True)
def test_thumbnail(admin_api_client, geotiff_image_entry):
    response = admin_api_client.get(
        f'/api/image_process/imagery/{geotiff_image_entry.pk}/thumbnail'
    )
    assert response.status_code == 200
    assert response['Content-Type'] == 'image/png'


@pytest.mark.django_db(transaction=True)
def test_cache(admin_api_client, geotiff_image_entry, django_assert_num_queries):
    # cache a response
    admin_api_client.get(f'/api/image_process/imagery/{geotiff_image_entry.pk}/tiles/1/0/0.png')
    # ensure no new queries are made for a different tile request made by same user on same image
    with django_assert_num_queries(0):
        admin_api_client.get(f'/api/image_process/imagery/{geotiff_image_entry.pk}/tiles/1/1/0.png')
