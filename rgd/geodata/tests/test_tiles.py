import pytest

from rgd.geodata.datastore import datastore

from . import factories


@pytest.fixture
def image_entry():
    imagefile = factories.ImageFileFactory(
        file__file__filename='paris_france_10.tiff',
        file__file__from_path=datastore.fetch('paris_france_10.tiff'),
    )
    return imagefile.imageentry


@pytest.mark.django_db(transaction=True)
def test_metadata(api_client, image_entry):
    response = api_client.get(f'/api/geodata/imagery/image_entry/{image_entry.pk}/tiles')
    metadata = response.data
    assert metadata['levels'] == 2
    assert metadata['sizeX'] == metadata['sizeY'] == 328
    assert metadata['tileWidth'] == metadata['tileHeight'] == 256
    assert metadata['tileWidth'] == metadata['tileHeight'] == 256


@pytest.mark.django_db(transaction=True)
def test_tile(api_client, image_entry):
    response = api_client.get(f'/api/geodata/imagery/image_entry/{image_entry.pk}/tiles/1/0/0.png')
    assert response.status_code == 200
    assert response['Content-Type'] == 'image/jpeg'


@pytest.mark.django_db(transaction=True)
def test_thumbnail(api_client, image_entry):
    response = api_client.get(f'/api/geodata/imagery/image_entry/{image_entry.pk}/thumbnail')
    assert response.status_code == 200
    assert response['Content-Type'] == 'image/jpeg'
