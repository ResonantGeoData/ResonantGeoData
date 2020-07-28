import pytest

from . import factories
from .datastore import datastore


SampleFiles = [
    {'name': '20091021202517-01000100-VIS_0001.ntf', 'centroid': {'x': -84.1110, 'y': 39.781}},
    {'name': 'aerial_rgba_000003.tiff', 'centroid': {'x': -122.0050, 'y': 37.3359}},
    {'name': 'cclc_schu_100.tif', 'centroid': {'x': -76.8638, 'y': 42.3869}},
    {'name': 'landcover_sample_2000.tif', 'centroid': {'x': -75.4412, 'y': 42.6694}},
    {'name': 'paris_france_10.tiff', 'centroid': {'x': 2.5485, 'y': 49.0039}},
    {'name': 'rgb_geotiff.tiff', 'centroid': {'x': -117.1872, 'y': 33.1712}},
    {'name': 'RomanColosseum_WV2mulitband_10.tif', 'centroid': {'x': 12.4923, 'y': 41.8902}},
]


@pytest.mark.parametrize('testfile', SampleFiles)
@pytest.mark.django_db(transaction=True)
def test_imagefile_to_rasterentry_centroids(testfile):
    imagefile = factories.ImageFileFactory(
        file__filename=testfile['name'], file__from_path=datastore.fetch(testfile['name']),
    )
    raster = factories.RasterEntryFactory(name=testfile['name'], images=[imagefile.imageentry.id])
    centroid = raster.footprint.centroid
    assert centroid.x == pytest.approx(testfile['centroid']['x'], abs=2e-4)
    assert centroid.y == pytest.approx(testfile['centroid']['y'], abs=2e-4)
