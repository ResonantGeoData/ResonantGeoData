from django.apps import apps
from django.conf import settings
import pytest
from rgd import models
from rgd.permissions import filter_read_perm
from rgd_testing_utils.helpers import check_model_permissions


@pytest.mark.django_db(transaction=True)
def test_unassigned_permissions_complex(user_factory, user, spatial_asset_a, spatial_asset_b):
    # TODO: reimplement with multi raster file fixture also
    prior = getattr(settings, 'RGD_GLOBAL_READ_ACCESS', None)
    settings.RGD_GLOBAL_READ_ACCESS = False
    admin = user_factory(is_superuser=True)
    admin_q = filter_read_perm(admin, models.SpatialEntry.objects.all())
    basic_q = filter_read_perm(user, models.SpatialEntry.objects.all())
    assert len(admin_q) == 2
    assert len(basic_q) == 0
    settings.RGD_GLOBAL_READ_ACCESS = True
    admin_q = filter_read_perm(admin, models.SpatialEntry.objects.all())
    basic_q = filter_read_perm(user, models.SpatialEntry.objects.all())
    assert len(admin_q) == len(basic_q)
    assert set(admin_q) == set(basic_q)
    settings.RGD_GLOBAL_READ_ACCESS = prior


def test_check_permissions_path_rgd():
    for model in apps.get_app_config('rgd').get_models():
        check_model_permissions(model)
