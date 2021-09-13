from rgd_client.client import RgdClient

from ._version import __version__  # noqa
from .plugin import ImageryPlugin, RasterDownload


class ImageryClient(RgdClient):
    imagery = ImageryPlugin


__all__ = ['ImageryClient', 'ImageryPlugin', 'RasterDownload']
