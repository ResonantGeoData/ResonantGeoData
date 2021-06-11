from large_image_source_gdal import GDALFileTileSource
import pytest
from rgd.datastore import datastore
from rgd_imagery.models.imagery import ConvertedImageFile, ImageEntry, SubsampledImage
from rgd_imagery.models.imagery.annotation import Annotation
from rgd_imagery.tasks.subsample import populate_subsampled_image

from . import factories


@pytest.mark.django_db(transaction=True)
def test_cog_image_conversion():
    image_file = factories.ImageFileFactory(
        file__file__filename='20091021202517-01000100-VIS_0001.ntf',
        file__file__from_path=datastore.fetch('20091021202517-01000100-VIS_0001.ntf'),
    )
    img = ImageEntry.objects.get(image_file=image_file)
    c = ConvertedImageFile()
    c.source_image = img
    c.save()
    # Task should complete synchronously
    c.refresh_from_db()
    assert c.converted_file


def _create_subsampled(img, sample_type, params):
    sub = SubsampledImage()
    sub.source_image = img
    sub.sample_type = sample_type
    sub.sample_parameters = params
    sub.skip_signal = True
    sub.save()
    populate_subsampled_image(sub)
    sub.refresh_from_db()
    return sub


def _assert_bounds(new, bounds):
    assert new['xmin'] >= bounds['xmin'], (new['srs'], bounds['srs'])
    assert new['xmax'] <= bounds['xmax'], (new['srs'], bounds['srs'])
    assert new['ymin'] >= bounds['ymin'], (new['srs'], bounds['srs'])
    assert new['ymax'] <= bounds['ymax'], (new['srs'], bounds['srs'])


@pytest.mark.django_db(transaction=True)
def test_subsample_pixel_box(elevation):
    with elevation.image_file.file.yield_local_path() as file_path:
        tile_source = GDALFileTileSource(str(file_path), projection='EPSG:3857', encoding='PNG')
        bounds = tile_source.getBounds()
    # Test with bbox
    sub = _create_subsampled(
        elevation, 'pixel box', {'left': 0, 'right': 100, 'bottom': 0, 'top': 200}
    )
    assert sub.data
    with sub.data.yield_local_path() as file_path:
        tile_source = GDALFileTileSource(str(file_path), projection='EPSG:3857', encoding='PNG')
        new = tile_source.getBounds()
    _assert_bounds(new, bounds)


@pytest.mark.django_db(transaction=True)
def test_subsample_geo_box(elevation):
    with elevation.image_file.file.yield_local_path() as file_path:
        tile_source = GDALFileTileSource(str(file_path), projection='EPSG:3857', encoding='PNG')
        bounds = tile_source.getBounds()
    # Test with bbox
    # -107.16011512365533, -107.05522782296597
    # 38.87471016725091, 38.92317443621267
    sub = _create_subsampled(
        elevation,
        'geographic box',
        {
            'left': -107.16011512365533,
            'right': -107.05522782296597,
            'bottom': 38.87471016725091,
            'top': 38.92317443621267,
            'projection': 'EPSG:4326',
        },
    )
    assert sub.data
    with sub.data.yield_local_path() as file_path:
        tile_source = GDALFileTileSource(str(file_path), projection='EPSG:3857', encoding='PNG')
        new = tile_source.getBounds()
    _assert_bounds(new, bounds)


@pytest.mark.django_db(transaction=True)
def test_subsample_geojson(elevation):
    with elevation.image_file.file.yield_local_path() as file_path:
        tile_source = GDALFileTileSource(str(file_path), projection='EPSG:3857', encoding='PNG')
        bounds = tile_source.getBounds()
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
        'projection': 'EPSG:4326',
    }
    sub = _create_subsampled(elevation, 'geojson', geojson)
    assert sub.data
    with sub.data.yield_local_path() as file_path:
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

    img = ImageEntry.objects.get(name='000000242287.jpg')  # bicycle
    a = Annotation.objects.get(image=img.id)  # Should be only one
    sub = _create_subsampled(img, 'annotation', {'id': a.id})
    assert sub.data
