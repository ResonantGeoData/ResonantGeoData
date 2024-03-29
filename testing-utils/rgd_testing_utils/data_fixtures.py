from django.contrib.gis.geos import GEOSGeometry
import pytest
from rgd import models
from rgd.datastore import datastore

from . import factories


@pytest.fixture
def checksum_file():
    return factories.ChecksumFileFactory()


@pytest.fixture
def checksum_file_url():
    return factories.ChecksumFileFactory(
        file=None,
        url=datastore.get_url('stars.png'),
        type=models.FileSourceType.URL,
    )


@pytest.fixture
def spatial_asset_a():
    geom = GEOSGeometry(
        'POLYGON ((-84.14505029585798 39.8080495412844, -84.07694970414201 39.8080495412844, -84.07694970414201 39.75395045871559, -84.14505029585798 39.75395045871559, -84.14505029585798 39.8080495412844))'
    )
    e = models.SpatialAsset()
    e.footprint = geom
    e.outline = geom
    e.save()
    e.files.add(factories.ChecksumFileFactory(file__filename='spatial_asset_a.dat'))
    e.save()
    return e


@pytest.fixture
def spatial_asset_b():
    geom = GEOSGeometry(
        'POLYGON ((-77.16435685136094 42.60406117923981, -76.53961844004117 42.60406117923981, -76.53961844004117 42.20103756066038, -77.16435685136094 42.20103756066038, -77.16435685136094 42.60406117923981))'
    )
    e = models.SpatialAsset()
    e.footprint = geom
    e.outline = geom
    e.save()
    e.files.add(factories.ChecksumFileFactory(file__filename='spatial_asset_b.dat'))
    e.save()
    return e


@pytest.fixture
def s3_url():
    return 's3://sentinel-cogs/sentinel-s2-l2a-cogs/2020/S2A_34RCN_20200111_0_L2A/S2A_34RCN_20200111_0_L2A.json'
