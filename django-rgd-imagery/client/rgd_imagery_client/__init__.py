from rgd_client.client import RgdClient

from .plugin import ImageryPlugin, RasterDownload
from ._version import __version__  # noqa


class ImageryClient(RgdClient):
    imagery = ImageryPlugin


__all__ = ['ImageryClient', 'ImageryPlugin', 'RasterDownload']
