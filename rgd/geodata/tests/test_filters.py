import pytest

from rgd.geodata.datastore import datastore
from rgd.geodata.filters import SpatialEntryFilter
from rgd.geodata.models import RasterMetaEntry, SpatialEntry

from . import factories


@pytest.fixture
def sample_raster_a():
    imagefile = factories.ImageFileFactory(
        file__filename='20091021202517-01000100-VIS_0001.ntf',
        file__from_path=datastore.fetch('20091021202517-01000100-VIS_0001.ntf'),
    )
    image_set = factories.ImageSetFactory(
        images=[imagefile.imageentry.id],
    )
    raster = factories.RasterEntryFactory(
        name='20091021202517-01000100-VIS_0001.ntf',
        image_set=image_set,
    )
    return RasterMetaEntry.objects.filter(parent_raster=raster).get()


@pytest.fixture
def sample_raster_b():
    imagefile = factories.ImageFileFactory(
        file__filename='cclc_schu_100.tif',
        file__from_path=datastore.fetch('cclc_schu_100.tif'),
    )
    image_set = factories.ImageSetFactory(
        images=[imagefile.imageentry.id],
    )
    raster = factories.RasterEntryFactory(
        name='cclc_schu_100.tif',
        image_set=image_set,
    )
    return RasterMetaEntry.objects.filter(parent_raster=raster).get()


@pytest.mark.django_db(transaction=True)
def test_raster_intersects(sample_raster_a, sample_raster_b):
    assert SpatialEntry.objects.count() == 2
    filterset = SpatialEntryFilter(
        data={
            'q': f'SRID=4326;{sample_raster_a.footprint.wkt}',
            'predicate': 'intersects',
        }
    )
    assert filterset.is_valid()
    qs = filterset.filter_queryset(SpatialEntry.objects.all())
    assert qs.count() == 1
