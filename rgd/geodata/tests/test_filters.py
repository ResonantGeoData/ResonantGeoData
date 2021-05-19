import pytest

from rgd.geodata.datastore import datastore
from rgd.geodata.filters import RasterMetaEntryFilter, SpatialEntryFilter
from rgd.geodata.models import RasterMetaEntry, SpatialEntry

from . import factories


@pytest.fixture
def sample_raster_a():
    imagefile = factories.ImageFileFactory(
        file__file__filename='RomanColosseum_WV2mulitband_10.tif',
        file__file__from_path=datastore.fetch('RomanColosseum_WV2mulitband_10.tif'),
    )
    image_set = factories.ImageSetFactory(
        images=[imagefile.imageentry.id],
    )
    raster = factories.RasterEntryFactory(
        name='20091021202517-01000100-VIS_0001.ntf',
        image_set=image_set,
    )
    return RasterMetaEntry.objects.get(parent_raster=raster)


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
    return RasterMetaEntry.objects.get(parent_raster=raster)


@pytest.mark.django_db(transaction=True)
def test_q_distance(sample_raster_a, sample_raster_b):
    assert SpatialEntry.objects.count() == 2
    # Make sure all are returned sorted by distance
    filterset = SpatialEntryFilter(
        data={
            'q': f'SRID=4326;{sample_raster_a.outline.wkt}',
        }
    )
    assert filterset.is_valid()
    qs = filterset.filter_queryset(SpatialEntry.objects.all())
    assert qs.count() == 2
    assert qs.first().spatial_id == sample_raster_a.spatial_id
    filterset = SpatialEntryFilter(
        data={
            'q': f'SRID=4326;{sample_raster_b.outline.wkt}',
        }
    )
    assert filterset.is_valid()
    qs = filterset.filter_queryset(SpatialEntry.objects.all())
    assert qs.count() == 2
    assert qs.first().spatial_id == sample_raster_b.spatial_id


@pytest.mark.django_db(transaction=True)
def test_raster_intersects(sample_raster_a, sample_raster_b):
    assert SpatialEntry.objects.count() == 2
    filterset = RasterMetaEntryFilter(
        data={
            'q': f'SRID=4326;{sample_raster_a.outline.wkt}',
            'predicate': 'intersects',
        }
    )
    assert filterset.is_valid()
    qs = filterset.filter_queryset(RasterMetaEntry.objects.all())
    assert qs.count() == 1


@pytest.mark.django_db(transaction=True)
def test_raster_num_bands(sample_raster_a, sample_raster_b):
    assert SpatialEntry.objects.count() == 2
    filterset = RasterMetaEntryFilter(
        data={
            'num_bands_max': 2,
        }
    )
    assert filterset.is_valid()
    qs = filterset.filter_queryset(RasterMetaEntry.objects.all())
    assert qs.count() == 1


@pytest.mark.django_db(transaction=True)
def test_geojson_intersects(sample_raster_a, sample_raster_b):
    assert SpatialEntry.objects.count() == 2
    filterset = SpatialEntryFilter(
        data={
            'q': f'{sample_raster_a.outline.geojson}',
            'predicate': 'intersects',
        }
    )
    assert filterset.is_valid()
    qs = filterset.filter_queryset(SpatialEntry.objects.all())
    assert qs.count() == 1
    assert qs.first().spatial_id == sample_raster_a.spatial_id
