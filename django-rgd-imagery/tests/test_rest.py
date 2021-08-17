import pytest
from rest_framework import status
from rgd_imagery import models


@pytest.mark.django_db(transaction=True)
def test_download_image_file(admin_api_client, astro_image):
    pk = astro_image.pk
    response = admin_api_client.get(f'/rgd_imagery_test/api/rgd_imagery/{pk}/data')
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
    response = admin_api_client.post(
        '/rgd_imagery_test/api/image_process/group', payload, format='json'
    )
    assert response.status_code == 201
    assert response.data
    group_id = response.data['id']
    payload = {
        'source_images': [
            astro_image.pk,
        ],
        'group': group_id,
    }
    response = admin_api_client.post('/rgd_imagery_test/api/image_process', payload, format='json')
    assert response.status_code == 201
    assert response.data
    id = response.data['id']
    sub = models.ProcessedImage.objects.get(id=id)
    assert sub.processed_image
    # Test the GET
    response = admin_api_client.get(f'/rgd_imagery_test/api/image_process/{id}')
    assert response.status_code == 200
    assert response.data
    # Now test to make sure the serializer prevents duplicates
    response = admin_api_client.post('/rgd_imagery_test/api/image_process', payload, format='json')
    assert response.status_code == 201
    assert response.data
    assert id == response.data['id']  # Compare against original PK


@pytest.mark.xfail
@pytest.mark.django_db(transaction=True)
def test_create_and_download_cog(admin_api_client, geotiff_image_entry):
    response = admin_api_client.post(
        '/rgd_imagery_test/api/image_process/group',
        {
            'process_type': 'cog',
        },
        format='json',
    )
    assert response.status_code == 201
    assert response.data
    group_id = response.data['id']
    response = admin_api_client.post(
        '/rgd_imagery_test/api/image_process',
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
    response = admin_api_client.get(f'/rgd_imagery_test/api/image_process/{pk}')
    assert response.data
