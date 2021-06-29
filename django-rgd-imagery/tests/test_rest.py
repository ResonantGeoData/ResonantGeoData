import pytest
from rest_framework import status
from rgd_imagery import models


@pytest.mark.django_db(transaction=True)
def test_download_image_file(admin_api_client, astro_image):
    pk = astro_image.pk
    response = admin_api_client.get(f'/rgd_imagery_test/api/rgd_imagery/{pk}/data')
    assert status.is_redirect(response.status_code)


@pytest.mark.django_db(transaction=True)
def test_create_get_subsampled_image(admin_api_client, astro_image):
    """Test POST and GET for RegionImage model."""
    payload = {
        'source_image': astro_image.pk,
        'sample_type': 'pixel box',
        'sample_parameters': {'right': 100, 'left': 0, 'top': 200, 'bottom': 0},
    }
    response = admin_api_client.post(
        '/rgd_imagery_test/api/image_process/imagery/subsample', payload, format='json'
    )
    assert response.status_code == 201
    assert response.data
    id = response.data['id']
    sub = models.RegionImage.objects.get(id=id)
    assert sub.processed_image
    # Test the GET
    response = admin_api_client.get(f'/rgd_imagery_test/api/image_process/imagery/subsample/{id}')
    assert response.status_code == 200
    assert response.data
    # Now test to make sure the serializer prevents duplicates
    response = admin_api_client.post(
        '/rgd_imagery_test/api/image_process/imagery/subsample', payload, format='json'
    )
    assert response.status_code == 201
    assert response.data
    assert id == response.data['id']  # Compare against original PK


@pytest.mark.django_db(transaction=True)
def test_create_and_download_cog(admin_api_client, geotiff_image_entry):
    """Test POST for ConvertedImage model."""
    response = admin_api_client.post(
        '/rgd_imagery_test/api/image_process/imagery/cog',
        {'source_image': geotiff_image_entry.id},
    )
    assert response.status_code == 201
    assert response.data
    # Check that a COG was generated
    cog = models.ConvertedImage.objects.get(source_image=geotiff_image_entry.id)
    # NOTE: This doesn't actually verify the file is in COG format. Assumed.
    assert cog.processed_image
    # Also test download endpoint here:
    pk = cog.pk
    response = admin_api_client.get(f'/rgd_imagery_test/api/image_process/imagery/cog/{pk}/data')
    assert status.is_redirect(response.status_code)
