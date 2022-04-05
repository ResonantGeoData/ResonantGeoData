from contextlib import contextmanager

import large_image
from large_image.tilesource import FileTileSource
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
