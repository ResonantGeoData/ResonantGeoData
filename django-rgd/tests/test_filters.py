from datetime import datetime

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


@pytest.mark.django_db(transaction=True)
def test_q_time(spatial_asset_a):
    spatial_asset_a.acquisition_date = datetime(2021, 1, 1, hour=12, second=0)
    spatial_asset_a.save()
    filterset = SpatialEntryFilter(data={'time_of_day_before': '13:00'})
    assert filterset.is_valid()
    qs = filterset.filter_queryset(models.SpatialEntry.objects.all())
    assert qs.count() == 1
    filterset = SpatialEntryFilter(data={'time_of_day_after': '13:00'})
    assert filterset.is_valid()
    qs = filterset.filter_queryset(models.SpatialEntry.objects.all())
    assert qs.count() == 0


@pytest.mark.django_db(transaction=True)
def test_collection(spatial_asset_a):
    filterset = SpatialEntryFilter(
        data={'collections': [spatial_asset_a.files.first().collection.pk]}
    )
    assert filterset.is_valid()
    qs = filterset.filter_queryset(models.SpatialEntry.objects.all())
    assert qs.count() == 1
    assert spatial_asset_a.spatial_id == qs.first().spatial_id
