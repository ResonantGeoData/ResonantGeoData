import pytest
from rgd.datastore import datastore
from rgd.models import ChecksumFile, FileSet, FileSourceType
from rgd_imagery.tasks.etl import load_image, populate_raster_footprint

from . import factories

SampleFiles = [
    {'name': '20091021202517-01000100-VIS_0001.ntf', 'centroid': {'x': -84.11, 'y': 39.78}},
    {'name': 'aerial_rgba_000003.tiff', 'centroid': {'x': -122.01, 'y': 37.34}},
    {'name': 'cclc_schu_100.tif', 'centroid': {'x': -76.85, 'y': 42.40}},
    {'name': 'landcover_sample_2000.tif', 'centroid': {'x': -75.23, 'y': 42.96}},
    {'name': 'paris_france_10.tiff', 'centroid': {'x': 2.55, 'y': 49.00}},
    {'name': 'rgb_geotiff.tiff', 'centroid': {'x': -117.19, 'y': 33.17}},
    {'name': 'RomanColosseum_WV2mulitband_10.tif', 'centroid': {'x': 12.50, 'y': 41.89}},
]


TOLERANCE = 2e-2


def _make_raster_from_datastore(name):
    image = factories.ImageFactory(
        file__file__filename=name,
        file__file__from_path=datastore.fetch(name),
    )
    image_set = factories.ImageSetFactory(
        images=[image.id],
    )
    raster = factories.RasterFactory(
        name=name,
        image_set=image_set,
    )
    return raster


@pytest.mark.parametrize('testfile', SampleFiles)
@pytest.mark.django_db(transaction=True)
def test_imagefile_to_rasterentry_centroids(testfile):
    raster = _make_raster_from_datastore(testfile['name'])
    meta = raster.rastermeta
    centroid = meta.outline.centroid
    assert centroid.x == pytest.approx(testfile['centroid']['x'], abs=TOLERANCE)
    assert centroid.y == pytest.approx(testfile['centroid']['y'], abs=TOLERANCE)


@pytest.mark.parametrize('testfile', SampleFiles)
@pytest.mark.django_db(transaction=True)
def test_imagefile_url_to_rasterentry_centroids(testfile):
    image = factories.ImageFactory(
        file__file=None,
        file__url=datastore.get_url(testfile['name']),
        file__type=FileSourceType.URL,
    )
    image_set = factories.ImageSetFactory(
        images=[image.id],
    )
    raster = factories.RasterFactory(
        name=testfile['name'],
        image_set=image_set,
    )
    meta = raster.rastermeta
    centroid = meta.outline.centroid
    # Sanity check
    assert image.file.type == FileSourceType.URL
    # Make sure the file contents were read correctly
    assert centroid.x == pytest.approx(testfile['centroid']['x'], abs=TOLERANCE)
    assert centroid.y == pytest.approx(testfile['centroid']['y'], abs=TOLERANCE)


@pytest.mark.django_db(transaction=True)
def test_repopulate_image_entry():
    """Only test with single image file."""
    testfile = SampleFiles[0]
    imagefile = factories.ImageFactory(
        file__file__filename=testfile['name'],
        file__file__from_path=datastore.fetch(testfile['name']),
    )
    # Testing that we can repopulate an image entry
    load_image(imagefile.id)


@pytest.mark.django_db(transaction=True)
def test_multi_file_raster(sample_raster_multi):
    """Test the use case where a raster is generated from multiple files."""
    assert sample_raster_multi.parent_raster.image_set.count == 3
    assert sample_raster_multi.crs is not None


@pytest.mark.parametrize(
    'name',
    [
        'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band1.tif',
        'landcover_sample_2000.tif',
    ],
)
@pytest.mark.django_db(transaction=True)
def test_raster_footprint(name):
    raster = _make_raster_from_datastore(name)
    populate_raster_footprint(raster.id)
    meta = raster.rastermeta
    assert meta.footprint
    assert meta.footprint != meta.outline


@pytest.mark.django_db(transaction=True)
def test_raster_with_header_file():
    # Download the two files for the image: envi_rgbsmall_bip
    file_set = FileSet.objects.create()
    img = ChecksumFile.objects.create(
        file_set=file_set, type=FileSourceType.URL, url=datastore.get_url('envi_rgbsmall_bip.img')
    )
    _ = ChecksumFile.objects.create(
        file_set=file_set, type=FileSourceType.URL, url=datastore.get_url('envi_rgbsmall_bip.hdr')
    )
    image = factories.ImageFactory(
        file=img,
    )
    image_set = factories.ImageSetFactory(
        images=[image.id],
    )
    raster = factories.RasterFactory(
        name='envi_rgbsmall_bip',
        image_set=image_set,
    )
    meta = raster.rastermeta
    centroid = meta.outline.centroid
    assert centroid.x == pytest.approx(-44.75, abs=TOLERANCE)
    assert centroid.y == pytest.approx(-23.02, abs=TOLERANCE)
