from contextlib import contextmanager

from large_image.exceptions import TileSourceException
from large_image.tilesource import FileTileSource
from large_image_source_gdal import GDALFileTileSource
from large_image_source_pil import PILFileTileSource
from rgd_imagery.models import Image


def get_tilesource_from_image(
    image: Image, projection: str = None, style: str = None
) -> FileTileSource:
    # Make sure projection is None by default to use source projection
    try:
        file_path = image.file.get_vsi_path(internal=True)
        return GDALFileTileSource(file_path, projection=projection, encoding='PNG', style=style)
    except TileSourceException:
        with image.file.yield_local_path() as file_path:
            return PILFileTileSource(file_path, style=style)


@contextmanager
def yeild_tilesource_from_image(image: Image, projection: str = None) -> FileTileSource:
    yield get_tilesource_from_image(image, projection)


def get_region_world(
    tile_source: FileTileSource,
    left: float,
    right: float,
    bottom: float,
    top: float,
    projection: str = 'EPSG:4326',
):
    region = dict(left=left, right=right, bottom=bottom, top=top, units=projection)
    path, mime_type = tile_source.getRegion(region=region, encoding='TILED')
    return path, mime_type


def get_region_pixel(
    tile_source: FileTileSource,
    left: int,
    right: int,
    bottom: int,
    top: int,
    units: str = 'pixels',
):
    left, right = min(left, right), max(left, right)
    top, bottom = min(top, bottom), max(top, bottom)
    region = dict(left=left, right=right, bottom=bottom, top=top, units=units)
    path, mime_type = tile_source.getRegion(region=region, encoding='TILED')
    return path, mime_type


def get_tile_bounds(
    tile_source: FileTileSource,
    projection: str = 'EPSG:4326',
):
    bounds = tile_source.getBounds(srs='EPSG:4326')
    threshold = 89.9999
    for key in ('ymin', 'ymax'):
        bounds[key] = max(min(bounds[key], threshold), -threshold)
    return bounds
