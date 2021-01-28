import pytest

from rgd.geodata.datastore import datastore
from rgd.geodata.models.common import FileSourceType
from rgd.geodata.models.imagery.annotation import Annotation, RLESegmentation
from rgd.geodata.models.imagery.base import (
    ConvertedImageFile,
    ImageEntry,
    ImageFile,
    SubsampledImage,
)
from rgd.geodata.models.imagery.etl import populate_image_entry
from rgd.geodata.models.imagery.subsample import populate_subsampled_image

from . import factories

SampleFiles = [
    {'name': '20091021202517-01000100-VIS_0001.ntf', 'centroid': {'x': -84.1110, 'y': 39.781}},
    {'name': 'aerial_rgba_000003.tiff', 'centroid': {'x': -122.0050, 'y': 37.3362}},
    {'name': 'cclc_schu_100.tif', 'centroid': {'x': -76.8746, 'y': 42.3933}},
    {'name': 'landcover_sample_2000.tif', 'centroid': {'x': -75.5988, 'y': 42.9230}},
    {'name': 'paris_france_10.tiff', 'centroid': {'x': 2.5485, 'y': 49.0039}},
    {'name': 'rgb_geotiff.tiff', 'centroid': {'x': -117.1900, 'y': 33.1713}},
    {'name': 'RomanColosseum_WV2mulitband_10.tif', 'centroid': {'x': 12.4923, 'y': 41.8902}},
]

# These test files are dramatically downsampled for rapid testing
LandsatFiles = [
    'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band1.tif',
    'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band2.tif',
    'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band3.tif',
]


@pytest.mark.parametrize('testfile', SampleFiles)
@pytest.mark.django_db(transaction=True)
def test_imagefile_to_rasterentry_centroids(testfile):
    imagefile = factories.ImageFileFactory(
        file__file__filename=testfile['name'],
        file__file__from_path=datastore.fetch(testfile['name']),
    )
    image_set = factories.ImageSetFactory(
        images=[imagefile.imageentry.id],
    )
    raster = factories.RasterEntryFactory(
        name=testfile['name'],
        image_set=image_set,
    )
    meta = raster.rastermetaentry
    centroid = meta.footprint.centroid
    assert centroid.x == pytest.approx(testfile['centroid']['x'], abs=2e-4)
    assert centroid.y == pytest.approx(testfile['centroid']['y'], abs=2e-4)


@pytest.mark.parametrize('testfile', SampleFiles)
@pytest.mark.django_db(transaction=True)
def test_imagefile_url_to_rasterentry_centroids(testfile):
    imagefile = factories.ImageFileFactory(
        file__file=None,
        file__url=datastore.get_url(testfile['name']),
        file__type=FileSourceType.URL,
    )
    image_set = factories.ImageSetFactory(
        images=[imagefile.imageentry.id],
    )
    raster = factories.RasterEntryFactory(
        name=testfile['name'],
        image_set=image_set,
    )
    meta = raster.rastermetaentry
    centroid = meta.footprint.centroid
    # Sanity check
    assert imagefile.file.type == FileSourceType.URL
    # Make sure the file contents were read correctly
    assert centroid.x == pytest.approx(testfile['centroid']['x'], abs=2e-4)
    assert centroid.y == pytest.approx(testfile['centroid']['y'], abs=2e-4)


@pytest.mark.django_db(transaction=True)
def test_repopulate_image_entry():
    """Only test with single image file."""
    testfile = SampleFiles[0]
    imagefile = factories.ImageFileFactory(
        file__file__filename=testfile['name'],
        file__file__from_path=datastore.fetch(testfile['name']),
    )
    # Testing that we can repopulate an image entry
    populate_image_entry(imagefile.id)


@pytest.mark.django_db(transaction=True)
def test_multi_file_raster():
    """Test the use case where a raster is generated from multiple files."""
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
    meta = raster.rastermetaentry
    assert raster.image_set.count == 3
    assert meta.crs is not None


def _run_kwcoco_import(demo):
    f_image_archive = demo['archive']
    f_spec_file = demo['spec']

    kwds = factories.KWCOCOArchiveFactory(
        image_archive__file__filename=f_image_archive,
        image_archive__file__from_path=datastore.fetch(f_image_archive),
        spec_file__file__filename=f_spec_file,
        spec_file__file__from_path=datastore.fetch(f_spec_file),
    )
    return kwds


@pytest.mark.django_db(transaction=True)
def test_kwcoco_basic_demo():
    demo = {
        'archive': 'demodata.zip',
        'spec': 'demo.kwcoco.json',
        'n_images': 3,
        'n_annotations': 11,
    }

    kwds = _run_kwcoco_import(demo)
    assert kwds.image_set.count == demo['n_images']
    annotations = [a for anns in kwds.image_set.get_all_annotations().values() for a in anns]
    assert len(annotations) == demo['n_annotations']
    # Trigger save event and make sure original images were deleted
    image_file_ids = [im.image_file.id for im in kwds.image_set.images.all()]
    kwds.save()
    for id in image_file_ids:
        with pytest.raises(ImageFile.DoesNotExist):
            ImageFile.objects.get(id=id)
    # Now do same for delete
    image_file_ids = [im.image_file.id for im in kwds.image_set.images.all()]
    kwds.delete()
    for id in image_file_ids:
        with pytest.raises(ImageFile.DoesNotExist):
            ImageFile.objects.get(id=id)


@pytest.mark.django_db(transaction=True)
def test_kwcoco_rle_demo():
    demo = {
        'archive': 'demo_rle.zip',
        'spec': 'demo_rle.kwcoco.json',
        'n_images': 2,
        'n_annotations': 15,
    }

    kwds = _run_kwcoco_import(demo)
    assert kwds.image_set.count == demo['n_images']
    annotations = [a for anns in kwds.image_set.get_all_annotations().values() for a in anns]
    assert len(annotations) == demo['n_annotations']

    # Test the RLESegmentation methods
    seg = RLESegmentation.objects.all().first()
    image = seg.annotation.image
    assert seg.width == image.width
    assert seg.height == image.height

    rle = seg.to_rle()
    assert 'counts' in rle
    assert 'size' in rle
    assert rle['size'] == [seg.height, seg.width]

    mask = seg.to_mask()
    assert mask.shape == (seg.height, seg.width)


@pytest.mark.django_db(transaction=True)
def test_cog_image_conversion():
    image_file = factories.ImageFileFactory(
        file__file__filename=SampleFiles[0]['name'],
        file__file__from_path=datastore.fetch(SampleFiles[0]['name']),
    )
    img = ImageEntry.objects.get(image_file=image_file)
    c = ConvertedImageFile()
    c.source_image = img
    c.save()
    # Task should complete synchronously
    c.refresh_from_db()
    assert c.converted_file


@pytest.mark.django_db(transaction=True)
def test_subsampling():
    name = 'Elevation.tif'
    image_file = factories.ImageFileFactory(
        file__file__filename=name,
        file__file__from_path=datastore.fetch(name),
    )

    def create_subsampled(img, sample_type, params):
        sub = SubsampledImage()
        sub.source_image = img
        sub.sample_type = sample_type
        sub.sample_parameters = params
        sub.skip_signal = True
        sub.save()
        populate_subsampled_image(sub)
        sub.refresh_from_db()
        return sub

    img = ImageEntry.objects.get(image_file=image_file)

    # Test with bbox
    sub = create_subsampled(img, 'pixel box', {'umax': 100, 'umin': 0, 'vmax': 200, 'vmin': 0})
    assert sub.data
    # Test with GeoJSON
    geojson = {
        'type': 'Polygon',
        'coordinates': [
            [
                [-107.08212524738178, 39.01040379702808],
                [-106.96182164246767, 39.03110215679572],
                [-106.90895466037738, 38.98387516880551],
                [-106.9805540376965, 38.91038429753703],
                [-107.07130208569401, 38.952157178475225],
                [-107.08212524738178, 39.01040379702808],
            ]
        ],
    }
    sub = create_subsampled(img, 'geojson', geojson)
    assert sub.data
    # Test with annotations
    demo = {
        'archive': 'demo_rle.zip',
        'spec': 'demo_rle.kwcoco.json',
    }
    _ = _run_kwcoco_import(demo)
    img = ImageEntry.objects.get(name='000000242287.jpg')  # bicycle
    a = Annotation.objects.get(image=img.id)  # Should be only one
    sub = create_subsampled(img, 'annotation', {'id': a.id})
    assert sub.data
    sub = create_subsampled(img, 'annotation', {'id': a.id, 'outline': True})
    assert sub.data
