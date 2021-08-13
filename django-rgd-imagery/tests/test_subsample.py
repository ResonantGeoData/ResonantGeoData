from large_image_source_gdal import GDALFileTileSource
import pytest
from rgd.datastore import datastore
from rgd.models import ChecksumFile
from rgd_imagery.models import Annotation, Image, ProcessedImage, ProcessedImageGroup
from rgd_imagery.tasks.subsample import extract_region

from . import factories


@pytest.mark.django_db(transaction=True)
def test_cog_image_conversion():
    image = factories.ImageFactory(
        file__file__filename='20091021202517-01000100-VIS_0001.ntf',
        file__file__from_path=datastore.fetch('20091021202517-01000100-VIS_0001.ntf'),
    )
    group = ProcessedImageGroup()
    group.process_type = ProcessedImageGroup.ProcessTypes.COG
    group.save()
    c = ProcessedImage()
    c.group = group
    c.skip_signal = True
    c.save()
    c.source_images.add(image)
    c.skip_signal = False
    c.save()
    # Task should complete synchronously
    c.refresh_from_db()
    assert c.processed_image


def _create_subsampled(image, params):
    group = ProcessedImageGroup()
    group.process_type = ProcessedImageGroup.ProcessTypes.REGION
    group.parameters = params
    group.save()
    sub = ProcessedImage()
    sub.skip_signal = True
    sub.group = group
    sub.save()
    sub.source_images.add(image)
    sub.save()
    extract_region(sub)
    sub.refresh_from_db()
    return sub


def _assert_bounds(new, bounds):
    assert new['xmin'] >= bounds['xmin'], (new['srs'], bounds['srs'])
    assert new['xmax'] <= bounds['xmax'], (new['srs'], bounds['srs'])
    assert new['ymin'] >= bounds['ymin'], (new['srs'], bounds['srs'])
    assert new['ymax'] <= bounds['ymax'], (new['srs'], bounds['srs'])


@pytest.mark.django_db(transaction=True)
def test_subsample_pixel_box(elevation):
    with elevation.file.yield_local_path() as file_path:
        tile_source = GDALFileTileSource(str(file_path), projection='EPSG:3857', encoding='PNG')
        bounds = tile_source.getBounds()
    # Test with bbox
    sub = _create_subsampled(
        elevation, {'sample_type': 'pixel box', 'left': 0, 'right': 100, 'bottom': 0, 'top': 200}
    )
    sub.refresh_from_db()
    assert sub.processed_image.file
    with sub.processed_image.file.yield_local_path() as file_path:
        tile_source = GDALFileTileSource(str(file_path), projection='EPSG:3857', encoding='PNG')
        new = tile_source.getBounds()
    _assert_bounds(new, bounds)


@pytest.mark.django_db(transaction=True)
def test_subsample_geo_box(elevation):
    with elevation.file.yield_local_path() as file_path:
        tile_source = GDALFileTileSource(str(file_path), projection='EPSG:3857', encoding='PNG')
        bounds = tile_source.getBounds()
    # Test with bbox
    # -107.16011512365533, -107.05522782296597
    # 38.87471016725091, 38.92317443621267
    sub = _create_subsampled(
        elevation,
        {
            'sample_type': 'geographic box',
            'left': -107.16011512365533,
            'right': -107.05522782296597,
            'bottom': 38.87471016725091,
            'top': 38.92317443621267,
            'projection': 'EPSG:4326',
        },
    )
    sub.refresh_from_db()
    assert sub.processed_image.file
    with sub.processed_image.file.yield_local_path() as file_path:
        tile_source = GDALFileTileSource(str(file_path), projection='EPSG:3857', encoding='PNG')
        new = tile_source.getBounds()
    _assert_bounds(new, bounds)


@pytest.mark.django_db(transaction=True)
def test_subsample_geojson(elevation):
    with elevation.file.yield_local_path() as file_path:
        tile_source = GDALFileTileSource(str(file_path), projection='EPSG:3857', encoding='PNG')
        bounds = tile_source.getBounds()
    # Test with GeoJSON
    geojson = {
        'sample_type': 'geojson',
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
        'projection': 'EPSG:4326',
    }
    sub = _create_subsampled(elevation, geojson)
    sub.refresh_from_db()
    assert sub.processed_image.file
    with sub.processed_image.file.yield_local_path() as file_path:
        tile_source = GDALFileTileSource(str(file_path), projection='EPSG:3857', encoding='PNG')
        new = tile_source.getBounds()
    _assert_bounds(new, bounds)


@pytest.mark.django_db(transaction=True)
def test_subsample_annotaion():
    # Test with annotations
    factories.KWCOCOArchiveFactory(
        image_archive__file__filename='demo_rle.zip',
        image_archive__file__from_path=datastore.fetch('demo_rle.zip'),
        spec_file__file__filename='demo_rle.kwcoco.json',
        spec_file__file__from_path=datastore.fetch('demo_rle.kwcoco.json'),
    )

    file = ChecksumFile.objects.get(name='000000242287.jpg')  # bicycle
    image = Image.objects.get(file=file)
    a = Annotation.objects.get(image=image.pk)  # Should be only one
    sub = _create_subsampled(image, {'sample_type': 'annotation', 'id': a.pk})
    sub.refresh_from_db()
    assert sub.processed_image.file
