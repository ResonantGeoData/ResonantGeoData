import pytest

from django.conf import settings

from rgd.geodata import models
from rgd.geodata.datastore import datastore
from rgd.geodata.permissions import filter_read_perm

from . import factories


@pytest.fixture
def sample_raster_a():
    imagefile = factories.ImageFileFactory(
        file__file__filename='20091021202517-01000100-VIS_0001.ntf',
        file__file__from_path=datastore.fetch('20091021202517-01000100-VIS_0001.ntf'),
    )
    image_set = factories.ImageSetFactory(
        images=[imagefile.imageentry.id],
    )
    raster = factories.RasterEntryFactory(
        name='20091021202517-01000100-VIS_0001.ntf',
        image_set=image_set,
    )
    return models.RasterMetaEntry.objects.get(parent_raster=raster)


@pytest.fixture
def sample_raster_b():
    imagefile = factories.ImageFileFactory(
        file__file__filename='cclc_schu_100.tif',
        file__file__from_path=datastore.fetch('cclc_schu_100.tif'),
    )
    image_set = factories.ImageSetFactory(
        images=[imagefile.imageentry.id],
    )
    raster = factories.RasterEntryFactory(
        name='cclc_schu_100.tif',
        image_set=image_set,
    )
    return models.RasterMetaEntry.objects.get(parent_raster=raster)


@pytest.fixture
def multi_file_raster():
    # These test files are dramatically downsampled for rapid testing
    LandsatFiles = [
        'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band1.tif',
        'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band2.tif',
        'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band3.tif',
    ]
    b1 = factories.ImageFileFactory(
        file__file__filename=LandsatFiles[0],
        file__file__from_path=datastore.fetch(LandsatFiles[0]),
    )
    b2 = factories.ImageFileFactory(
        file__file__filename=LandsatFiles[1],
        file__file__from_path=datastore.fetch(LandsatFiles[1]),
    )
    b3 = factories.ImageFileFactory(
        file__file__filename=LandsatFiles[2],
        file__file__from_path=datastore.fetch(LandsatFiles[2]),
    )
    image_set = factories.ImageSetFactory(
        images=[
            b1.imageentry.id,
            b2.imageentry.id,
            b3.imageentry.id,
        ],
    )
    # Create a RasterEntry from the three band image entries
    raster = factories.RasterEntryFactory(
        name='Multi File Test',
        image_set=image_set,
    )
    return raster.rastermetaentry


@pytest.mark.django_db(transaction=True)
def test_unassigned_permissions_simple(user_factory, user, sample_raster_a, sample_raster_b):
    prior = settings.RGD_GLOBAL_READ_ACCESS
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


@pytest.mark.django_db(transaction=True)
def test_unassigned_permissions_complex(user_factory, user, sample_raster_a, multi_file_raster):
    prior = settings.RGD_GLOBAL_READ_ACCESS
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
