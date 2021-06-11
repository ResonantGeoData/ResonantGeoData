from django.conf import settings
import pytest
from rgd.geodata.permissions import filter_read_perm

from rgd.geodata import models


@pytest.mark.django_db(transaction=True)
def test_unassigned_permissions_complex(user_factory, user, sample_raster_a, sample_raster_multi):
    prior = settings.RGD_GLOBAL_READ_ACCESS
    settings.RGD_GLOBAL_READ_ACCESS = False
    admin = user_factory(is_superuser=True)
    admin_q = filter_read_perm(admin, models.RasterMetaEntry.objects.all())
    basic_q = filter_read_perm(user, models.RasterMetaEntry.objects.all())
    assert len(admin_q) == 2
    assert len(basic_q) == 0
    settings.RGD_GLOBAL_READ_ACCESS = True
    admin_q = filter_read_perm(admin, models.RasterMetaEntry.objects.all())
    basic_q = filter_read_perm(user, models.RasterMetaEntry.objects.all())
    assert len(admin_q) == len(basic_q)
    assert set(admin_q) == set(basic_q)
    settings.RGD_GLOBAL_READ_ACCESS = prior
