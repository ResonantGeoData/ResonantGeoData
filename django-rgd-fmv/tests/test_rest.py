import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rgd_fmv.models import FMV
from rgd_fmv.serializers import FMVMetaSerializer


@pytest.mark.django_db(transaction=True)
def test_swagger(admin_api_client):
    response = admin_api_client.get('/swagger/?format=openapi')
    assert status.is_success(response.status_code)


@pytest.mark.django_db(transaction=True)
def test_fmv_spatial_entry(admin_api_client: APIClient, fmv_klv_file: FMV):
    resp = admin_api_client.get(f'/rgd_fmv_test/api/rgd_fmv/{fmv_klv_file.fmvmeta.pk}')
    assert resp.json() == FMVMetaSerializer(fmv_klv_file.fmvmeta).data
