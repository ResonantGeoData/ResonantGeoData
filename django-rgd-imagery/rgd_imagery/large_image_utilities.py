from contextlib import contextmanager
import logging
import os
import pathlib
import tempfile

import large_image
from large_image.tilesource import FileTileSource
from rgd.utility import get_temp_dir
from rgd_imagery.models import Image

logger = logging.getLogger(__name__)


def get_tilesource_from_image(
    image: Image, projection: str = None, style: str = None
) -> FileTileSource:
    # NOTE: We ran into issues using VSI paths with some image formats (NITF)
    #       this now requires the images be a local path on the file system.
    #       For URL files, this is done through FUSE but for S3FileField
    #       files, we must download the entire file to the local disk.
    with image.file.yield_local_path(yield_file_set=True) as file_path:
        # NOTE: yield_file_set=True incase there are header files
        return large_image.open(str(file_path), projection=projection, style=style, encoding='PNG')


@contextmanager
def yeild_tilesource_from_image(image: Image, projection: str = None) -> FileTileSource:
    yield get_tilesource_from_image(image, projection)


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
    path, mime_type = tile_source.getRegion(region=region, encoding=encoding)
    return path, mime_type


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
    if hasattr(tile_source, 'geospatial'):
        if not encoding:
            encoding = 'TILED'
        path, mime_type = tile_source.getRegion(region=region, encoding=encoding)
    else:
        if not encoding:
            encoding = 'JPEG'
        content, mime_type = tile_source.getRegion(region=region, encoding=encoding)
        # Write content to temporary file
        fd, path = tempfile.mkstemp(suffix='.tiff', prefix='pixelRegion_', dir=str(get_temp_dir()))
        os.close(fd)
        path = pathlib.Path(path)
        with open(path, 'wb') as f:
            f.write(content)
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
