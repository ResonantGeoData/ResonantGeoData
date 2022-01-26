import time

import pytest
import requests
from rest_framework import status
from rest_framework.test import RequestsClient
from rgd.datastore import datastore
from rgd_imagery import models

from . import factories


@pytest.mark.django_db(transaction=True)
def test_swagger(admin_api_client):
    response = admin_api_client.get('/swagger/?format=openapi')
    assert status.is_success(response.status_code)


@pytest.mark.django_db(transaction=True)
def test_download_image_file(admin_api_client, astro_image):
    pk = astro_image.pk
    response = admin_api_client.get(f'/api/rgd_imagery/{pk}/data')
    assert status.is_redirect(response.status_code)


@pytest.mark.xfail
@pytest.mark.django_db(transaction=True)
def test_create_get_subsampled_image(admin_api_client, astro_image):
    payload = {
        'process_type': 'region',
        'parameters': {
            'sample_type': 'pixel box',
            'right': 100,
            'left': 0,
            'top': 200,
            'bottom': 0,
        },
    }
    response = admin_api_client.post('/api/image_process/group', payload, format='json')
    assert response.status_code == 201
    assert response.data
    group_id = response.data['id']
    payload = {
        'source_images': [
            astro_image.pk,
        ],
        'group': group_id,
    }
    response = admin_api_client.post('/api/image_process', payload, format='json')
    assert response.status_code == 201
    assert response.data
    id = response.data['id']
    sub = models.ProcessedImage.objects.get(pk=id)
    assert sub.processed_image
    # Test the GET
    response = admin_api_client.get(f'/api/image_process/{id}')
    assert response.status_code == 200
    assert response.data
    # Now test to make sure the serializer prevents duplicates
    response = admin_api_client.post('/api/image_process', payload, format='json')
    assert response.status_code == 201
    assert response.data
    assert id == response.data['id']  # Compare against original PK


@pytest.mark.xfail
@pytest.mark.django_db(transaction=True)
def test_create_and_download_cog(admin_api_client, geotiff_image_entry):
    response = admin_api_client.post(
        '/api/image_process/group',
        {
            'process_type': 'cog',
        },
        format='json',
    )
    assert response.status_code == 201
    assert response.data
    group_id = response.data['id']
    response = admin_api_client.post(
        '/api/image_process',
        {
            'source_images': [
                geotiff_image_entry.id,
            ],
            'group': group_id,
        },
        format='json',
    )
    assert response.status_code == 201
    assert response.data
    # Check that a COG was generated
    cog = models.ProcessedImage.objects.get(pk=response.data['id'])
    # NOTE: This doesn't actually verify the file is in COG format. Assumed.
    assert cog.processed_image
    # Also test download endpoint here:
    pk = cog.pk
    response = admin_api_client.get(f'/api/image_process/{pk}')
    assert response.data


@pytest.mark.django_db(transaction=True)
def test_tiles_endpoint_with_signature(admin_api_client, live_server, settings):
    image = factories.ImageFactory(
        file__file__filename='paris_france_10.tiff',
        file__file__from_path=datastore.fetch('paris_france_10.tiff'),
    )
    # Set the TTL to something short
    settings.RGD_SIGNED_URL_TTL = 3  # seconds
    # Generate a signature
    response = admin_api_client.post('/api/signature')
    params = response.data
    # 15/16618/11252 - paris_france_10.tiff
    url = f'{live_server.url}/api/image_process/imagery/{image.pk}/tiles/15/16618/11252.png?projection=EPSG:3857'
    for k, v in params.items():
        url += f'&{k}={v}'
    # Use a client without authententication
    client = RequestsClient()
    response = client.get(url)
    response.raise_for_status()
    # Let the signature expire and assert that we get an accessed denied error
    time.sleep(3)
    response = client.get(url)
    with pytest.raises(requests.HTTPError):
        response.raise_for_status()
    assert response.status_code == 401
