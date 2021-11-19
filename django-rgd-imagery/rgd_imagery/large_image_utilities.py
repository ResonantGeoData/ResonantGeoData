from contextlib import contextmanager
import os
import pathlib
import tempfile

import large_image
from large_image.tilesource import FileTileSource
from large_image_source_gdal import GDALFileTileSource
from rgd.utility import get_cache_dir
from rgd_imagery.models import Image


def get_tilesource_from_image(
    image: Image, projection: str = None, style: str = None
) -> FileTileSource:
    # NOTE: We ran into issues using VSI paths with some image formats (NITF)
    #       this now requires the images be a local path on the file system.
    #       For URL files, this is done through FUSE but for S3FileField
    #       files, we must download the entire file to the local disk.
    with image.file.yield_local_path(yield_file_set=True) as file_path:
        # NOTE: yield_file_set=True in case there are header files
        return large_image.open(str(file_path), projection=projection, style=style, encoding='PNG')


@contextmanager
def yeild_tilesource_from_image(image: Image, projection: str = None) -> FileTileSource:
    yield get_tilesource_from_image(image, projection)


def _get_region(tile_source: FileTileSource, region: dict, encoding: str):
    result, mime_type = tile_source.getRegion(region=region, encoding=encoding)
    if encoding == 'TILED':
        path = result
    else:
        # Write content to temporary file
        fd, path = tempfile.mkstemp(
            suffix=f'.{encoding}', prefix='pixelRegion_', dir=str(get_cache_dir())
        )
        os.close(fd)
        path = pathlib.Path(path)
        with open(path, 'wb') as f:
            f.write(result)
    return path, mime_type


def get_region_world(
    tile_source: FileTileSource,
    left: float,
    right: float,
    bottom: float,
    top: float,
    units: str = 'EPSG:4326',
    encoding: str = 'TILED',
):
    region = dict(left=left, right=right, bottom=bottom, top=top, units=units)
    return _get_region(tile_source, region, encoding)


def get_region_pixel(
    tile_source: FileTileSource,
    left: int,
    right: int,
    bottom: int,
    top: int,
    units: str = 'pixels',
    encoding: str = None,
):
    left, right = min(left, right), max(left, right)
    top, bottom = min(top, bottom), max(top, bottom)
    region = dict(left=left, right=right, bottom=bottom, top=top, units=units)
    if isinstance(tile_source, GDALFileTileSource) and encoding is None:
        # Use tiled encoding by default for geospatial rasters
        #   output will be a tiled TIF
        encoding = 'TILED'
    elif encoding is None:
        # Otherwise use JPEG encoding by default
        encoding = 'JPEG'
    return _get_region(tile_source, region, encoding)


def get_tile_bounds(
    tile_source: FileTileSource,
    projection: str = 'EPSG:4326',
):
    bounds = tile_source.getBounds(srs=projection)
    threshold = 89.9999
    for key in ('ymin', 'ymax'):
        bounds[key] = max(min(bounds[key], threshold), -threshold)
    return bounds
