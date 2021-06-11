import pytest
from rgd.geodata import models
from rgd.geodata.filters import RasterMetaEntryFilter, SpatialEntryFilter


@pytest.mark.django_db(transaction=True)
def test_q_distance(sample_raster_a, sample_raster_b):
    assert models.SpatialEntry.objects.count() == 2
    # Make sure all are returned sorted by distance
    filterset = SpatialEntryFilter(
        data={
            'q': f'SRID=4326;{sample_raster_a.outline.wkt}',
        }
    )
    assert filterset.is_valid()
    qs = filterset.filter_queryset(models.SpatialEntry.objects.all())
    assert qs.count() == 2
    assert qs.first().spatial_id == sample_raster_a.spatial_id
    filterset = SpatialEntryFilter(
        data={
            'q': f'SRID=4326;{sample_raster_b.outline.wkt}',
        }
    )
    assert filterset.is_valid()
    qs = filterset.filter_queryset(models.SpatialEntry.objects.all())
    assert qs.count() == 2
    assert qs.first().spatial_id == sample_raster_b.spatial_id


@pytest.mark.django_db(transaction=True)
def test_raster_intersects(sample_raster_a, sample_raster_b):
    assert models.SpatialEntry.objects.count() == 2
    filterset = SpatialEntryFilter(
        data={
            'q': f'SRID=4326;{sample_raster_a.outline.wkt}',
            'predicate': 'intersects',
        }
    )
    assert filterset.is_valid()
    qs = filterset.filter_queryset(models.RasterMetaEntry.objects.all())
    assert qs.count() == 1


@pytest.mark.django_db(transaction=True)
def test_raster_num_bands(sample_raster_b, sample_raster_c):
    # b has many bands and c has 1 band
    assert models.SpatialEntry.objects.count() == 2
    filterset = RasterMetaEntryFilter(
        data={
            'num_bands_max': 2,
        }
    )
    assert filterset.is_valid()
    qs = filterset.filter_queryset(models.RasterMetaEntry.objects.all())
    assert qs.count() == 1


@pytest.mark.django_db(transaction=True)
def test_geojson_intersects(sample_raster_a, sample_raster_b):
    assert models.SpatialEntry.objects.count() == 2
    filterset = SpatialEntryFilter(
        data={
            'q': f'{sample_raster_a.outline.geojson}',
            'predicate': 'intersects',
        }
    )
    assert filterset.is_valid()
    qs = filterset.filter_queryset(models.SpatialEntry.objects.all())
    assert qs.count() == 1
    assert qs.first().spatial_id == sample_raster_a.spatial_id
