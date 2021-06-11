import pytest
from rgd import models
from rgd.filters import SpatialEntryFilter


@pytest.mark.django_db(transaction=True)
def test_q_distance(spatial_asset_a, spatial_asset_b):
    assert models.SpatialEntry.objects.count() == 2
    # Make sure all are returned sorted by distance
    filterset = SpatialEntryFilter(
        data={
            'q': f'SRID=4326;{spatial_asset_a.outline.wkt}',
        }
    )
    assert filterset.is_valid()
    qs = filterset.filter_queryset(models.SpatialEntry.objects.all())
    assert qs.count() == 2
    assert qs.first().spatial_id == spatial_asset_a.spatial_id
    filterset = SpatialEntryFilter(
        data={
            'q': f'SRID=4326;{spatial_asset_b.outline.wkt}',
        }
    )
    assert filterset.is_valid()
    qs = filterset.filter_queryset(models.SpatialEntry.objects.all())
    assert qs.count() == 2
    assert qs.first().spatial_id == spatial_asset_b.spatial_id


@pytest.mark.django_db(transaction=True)
def test_footprint_intersects(spatial_asset_a, spatial_asset_b):
    assert models.SpatialEntry.objects.count() == 2
    filterset = SpatialEntryFilter(
        data={
            'q': f'SRID=4326;{spatial_asset_a.outline.wkt}',
            'predicate': 'intersects',
        }
    )
    assert filterset.is_valid()
    qs = filterset.filter_queryset(models.SpatialEntry.objects.all())
    assert qs.count() == 1


@pytest.mark.django_db(transaction=True)
def test_geojson_intersects(spatial_asset_a, spatial_asset_b):
    assert models.SpatialEntry.objects.count() == 2
    filterset = SpatialEntryFilter(
        data={
            'q': f'{spatial_asset_a.outline.geojson}',
            'predicate': 'intersects',
        }
    )
    assert filterset.is_valid()
    qs = filterset.filter_queryset(models.SpatialEntry.objects.all())
    assert qs.count() == 1
    assert qs.first().spatial_id == spatial_asset_a.spatial_id
