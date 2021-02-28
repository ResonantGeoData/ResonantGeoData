from abc import ABCMeta, abstractmethod
from typing import Type, TypedDict, TypeVar

from django.http import HttpRequest, JsonResponse, StreamingHttpResponse
from django.views import View
from large_image.tilesource import FileTileSource
from large_image_source_gdal import GDALFileTileSource

AT = TypeVar('AT')
KT = TypeVar('KT')


class AbstractBaseTileView(View):
    """Base class for all tile views."""

    @abstractmethod
    def get_file_path(self, request: HttpRequest, *args, **kwargs) -> str:
        """Return the path of the image file."""
        raise NotImplementedError

    @abstractmethod
    def get_tile_source_class(self, request: HttpRequest, *args, **kwargs) -> Type[FileTileSource]:
        """Return the class to build a tile source."""
        raise NotImplementedError

    def get_tile_source_kwargs(self, request: HttpRequest, *args, **kwargs) -> dict:
        """Return any keyword arguments to provide to the tile source class when building."""
        return {}

    def get_tile_source(self, request: HttpRequest, *args, **kwargs) -> FileTileSource:
        """Return the built tile source."""
        tile_source_class = self.get_tile_source_class(request)
        file_path = self.get_file_path(request, *args, **kwargs)
        tile_source_kwargs = self.get_tile_source_kwargs(request, *args, **kwargs)
        tile_source = tile_source_class(file_path, **tile_source_kwargs)
        return tile_source


class AbstractMetadataTileView(AbstractBaseTileView):
    """Base class for tile metadata views."""

    def get(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        tile_source = self.get_tile_source(request, *args, **kwargs)
        metadata = tile_source.getMetadata()
        return JsonResponse(metadata)


class TileRequestParams(TypedDict, total=False):
    x: int
    y: int
    z: int


class AbstractTileView(AbstractBaseTileView):
    """Base class for views that return the actual tile data."""

    def get_tile_kwargs(self, request: HttpRequest, *args, **kwargs) -> Type[FileTileSource]:
        """Return any keyword arguments to provide to the tile source class when building an individual tile."""
        return {}

    def get(
        self, request: HttpRequest, *args, **kwargs: TileRequestParams
    ) -> StreamingHttpResponse:
        tile_source = self.get_tile_source(request, *args, **kwargs)
        tile_kwargs = self.get_tile_kwargs(request, *args, **kwargs)
        x = kwargs['x']
        y = kwargs['y']
        z = kwargs['z']
        tile_binary = tile_source.getTile(x, y, z, **tile_kwargs)
        return StreamingHttpResponse(tile_binary)


class GDALTileMetadataTileView(AbstractMetadataTileView, metaclass=ABCMeta):
    def get_tile_source_class(self, *args, **kwargs):
        return GDALFileTileSource


class GDALTileView(AbstractTileView, metaclass=ABCMeta):
    def get_tile_source_class(self, *args, **kwargs):
        return GDALFileTileSource
