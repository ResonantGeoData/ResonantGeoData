from large_image.exceptions import TileSourceException
from large_image.tilesource import FileTileSource
from large_image_source_gdal import GDALFileTileSource
from large_image_source_pil import PILFileTileSource

from .base import ImageEntry


def get_tilesource_from_image_entry(
    image_entry: ImageEntry, projection: str = 'EPSG:3857'
) -> FileTileSource:
    try:
        file_path = image_entry.image_file.file.get_vsi_path(internal=True)
        return GDALFileTileSource(file_path, projection=projection, encoding='PNG')
    except TileSourceException:
        with image_entry.image_file.file.yield_local_path() as file_path:
            return PILFileTileSource(file_path)


def get_region_world(
    tile_source: FileTileSource,
    left: float,
    right: float,
    bottom: float,
    top: float,
    projection: str = 'EPSG:3857',
):
    region = dict(left=left, right=right, bottom=bottom, top=top, units=projection)
    path, mime_type = tile_source.getRegion(region=region, encoding='TILED')
    return path, mime_type


def get_region_pixel(tile_source: FileTileSource, left: int, right: int, bottom: int, top: int):
    left, right = min(left, right), max(left, right)
    top, bottom = min(top, bottom), max(top, bottom)
    region = dict(left=left, right=right, bottom=bottom, top=top, units='pixel')
    path, mime_type = tile_source.getRegion(region=region, encoding='TILED')
    return path, mime_type
