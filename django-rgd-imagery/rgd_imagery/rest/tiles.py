import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from large_image.tilesource import FileTileSource
from large_image_source_gdal import GDALFileTileSource
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rgd_imagery import large_image_utilities
from rgd_imagery.models import Image


class BaseTileView(APIView):
    def get_tile_source(self, request: Request, pk: int) -> FileTileSource:
        """Return the built tile source."""
        image_entry = get_object_or_404(Image, pk=pk)
        self.check_object_permissions(request, image_entry)
        projection = request.query_params.get('projection', None)
        band = int(request.query_params.get('band', 0))
        style = None
        if band:
            style = json.dumps({'band': band})
        return large_image_utilities.get_tilesource_from_image(image_entry, projection, style=style)


class TileMetadataView(BaseTileView):
    """Returns tile metadata."""

    def get(self, request: Request, pk: int) -> Response:
        tile_source = self.get_tile_source(request, pk)
        metadata = tile_source.getMetadata()
        return Response(metadata)


class TileInternalMetadataView(BaseTileView):
    """Returns additional known metadata about the tile source."""

    def get(self, request: Request, pk: int) -> Response:
        tile_source = self.get_tile_source(request, pk)
        metadata = tile_source.getInternalMetadata()
        return Response(metadata)


class TileView(BaseTileView):
    """Returns tile binary."""

    def get(self, request: Request, pk: int, x: int, y: int, z: int) -> HttpResponse:
        tile_source = self.get_tile_source(request, pk)
        tile_binary = tile_source.getTile(x, y, z)
        mime_type = tile_source.getTileMimeType()
        return HttpResponse(tile_binary, content_type=mime_type)


class TileCornersView(BaseTileView):
    """Returns bounds of a tile for a given x, y, z index."""

    def get(self, request: Request, pk: int, x: int, y: int, z: int) -> HttpResponse:
        tile_source = self.get_tile_source(request, pk)
        xmin, ymin, xmax, ymax = tile_source.getTileCorners(z, x, y)
        metadata = {
            'xmin': xmin,
            'xmax': xmax,
            'ymin': ymin,
            'ymax': ymax,
            'proj4': tile_source.getProj4String(),
        }
        return Response(metadata)


class TileThumnailView(BaseTileView):
    """Returns tile thumbnail."""

    def get(self, request: Request, pk: int) -> Response:
        tile_source = self.get_tile_source(request, pk)
        thumb_data, mime_type = tile_source.getThumbnail(encoding='PNG')
        return HttpResponse(thumb_data, content_type=mime_type)


class TileBandInfoView(BaseTileView):
    """Returns band information."""

    def get(self, request: Request, pk: int) -> Response:
        tile_source = self.get_tile_source(request, pk)
        metadata = tile_source.getBandInformation()
        return Response(metadata)


class TileSingleBandInfoView(BaseTileView):
    """Returns single band information."""

    def get(self, request: Request, pk: int, band: int) -> Response:
        tile_source = self.get_tile_source(request, pk)
        metadata = tile_source.getOneBandInformation(band)
        return Response(metadata)


class TileRegionView(BaseTileView):
    """Returns region tile binary from world coordinates in given EPSG."""

    def get(
        self, request: Request, pk: int, left: float, right: float, bottom: float, top: float
    ) -> HttpResponse:
        tile_source = self.get_tile_source(request, pk)
        if not isinstance(tile_source, GDALFileTileSource):
            raise TypeError('Souce image must have geospatial reference.')
        projection = request.query_params.get('projection', 'EPSG:3857')
        path, mime_type = large_image_utilities.get_region_world(
            tile_source, left, right, bottom, top, projection
        )
        tile_binary = open(path, 'rb')
        return HttpResponse(tile_binary, content_type=mime_type)


class TileRegionPixelView(BaseTileView):
    """Returns region tile binary from pixel coordinates."""

    def get(
        self, request: Request, pk: int, left: float, right: float, bottom: float, top: float
    ) -> HttpResponse:
        tile_source = self.get_tile_source(request, pk)
        path, mime_type = large_image_utilities.get_region_world(
            tile_source, left, right, bottom, top
        )
        tile_binary = open(path, 'rb')
        return HttpResponse(tile_binary, content_type=mime_type)
