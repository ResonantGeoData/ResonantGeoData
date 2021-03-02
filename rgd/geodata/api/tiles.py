from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from large_image_source_gdal import GDALFileTileSource
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from rgd.geodata.models import ImageEntry


class BaseTileView(APIView):
    def get_tile_source(self, request: Request, pk: int) -> GDALFileTileSource:
        """Return the built tile source."""
        image_entry = get_object_or_404(ImageEntry, pk=pk)
        self.check_object_permissions(request, image_entry)
        file_path = image_entry.image_file.file.get_vsi_path()
        tile_source = GDALFileTileSource(file_path)
        return tile_source


class TileMetadataView(BaseTileView):
    """Returns tile metadata."""

    def get(self, request: Request, pk: int) -> Response:
        tile_source = self.get_tile_source(request, pk)
        metadata = tile_source.getMetadata()
        return Response(metadata)


class TileView(BaseTileView):
    """Returns tile binary."""

    def get(self, request: Request, pk: int, x: int, y: int, z: int) -> HttpResponse:
        tile_source = self.get_tile_source(request, pk)
        tile_binary = tile_source.getTile(x, y, z)
        mime_type = tile_source.getTileMimeType()
        return HttpResponse(tile_binary, content_type=mime_type)


class TileThumnailView(BaseTileView):
    """Returns tile thumbnail."""

    def get(self, request: Request, pk: int) -> Response:
        tile_source = self.get_tile_source(request, pk)
        thumb_data, mime_type = tile_source.getThumbnail()
        return HttpResponse(thumb_data, content_type=mime_type)
