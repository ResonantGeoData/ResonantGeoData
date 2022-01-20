import json

from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from large_image.tilesource import FileTileSource
from large_image_source_gdal import GDALFileTileSource
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rgd.rest import CACHE_TIMEOUT
from rgd.rest.authentication import SignedURLAuthentication
from rgd.rest.mixins import BaseRestViewMixin
from rgd_imagery import large_image_utilities
from rgd_imagery.models import Image


class BaseTileView(BaseRestViewMixin, APIView):
    def get_tile_source(self, request: Request, pk: int) -> FileTileSource:
        """Return the built tile source."""
        # get image_entry from cache
        image_cache_key = f'large_image_tile:image_{pk}'
        if (image_entry := cache.get(image_cache_key, None)) is None:
            image_entry = get_object_or_404(Image.objects.select_related('file'), pk=pk)
            cache.set(image_cache_key, image_entry, CACHE_TIMEOUT)

        # check authentication
        sentinel = object()
        auth_cache_key = f'large_image_tile:image_{pk}:user_{request.user.pk}'
        if cache.get(auth_cache_key, sentinel) is sentinel:
            self.check_object_permissions(request, image_entry)
            cache.set(auth_cache_key, None, CACHE_TIMEOUT)

        projection = request.query_params.get('projection', None)
        band = int(request.query_params.get('band', 0))
        style = None
        if band:
            style = {'band': band}
            bmin = request.query_params.get('min', None)
            bmax = request.query_params.get('max', None)
            if bmin is not None:
                style['min'] = bmin
            if bmax is not None:
                style['max'] = bmax
            palette = request.query_params.get('palette', None)
            if palette:
                style['palette'] = palette
            nodata = request.query_params.get('nodata', None)
            if nodata:
                style['nodata'] = nodata
            style = json.dumps(style)
        return large_image_utilities.get_tilesource_from_image(image_entry, projection, style=style)


class TileMetadataView(BaseTileView):
    """Returns tile metadata."""

    def get(self, request: Request, pk: int) -> Response:
        tile_source = self.get_tile_source(request, pk)
        metadata = tile_source.getMetadata()
        metadata['bounds'] = large_image_utilities.get_tile_bounds(tile_source)
        return Response(metadata)


class TileInternalMetadataView(BaseTileView):
    """Returns additional known metadata about the tile source."""

    def get(self, request: Request, pk: int) -> Response:
        tile_source = self.get_tile_source(request, pk)
        metadata = tile_source.getInternalMetadata()
        return Response(metadata)


class TileView(BaseTileView):
    """Returns tile binary."""

    authentication_classes = BaseTileView.authentication_classes + [
        SignedURLAuthentication,
    ]

    @method_decorator(cache_page(CACHE_TIMEOUT))
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

    @method_decorator(cache_page(CACHE_TIMEOUT))
    def get(self, request: Request, pk: int) -> HttpResponse:
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
    """Returns region tile binary from world coordinates in given EPSG.

    Note
    ----
    Use the `units` query parameter to inidicate the projection of the given
    coordinates. This can be different than the `projection` parameter used
    to open the tile source. `units` defaults to `EPSG:4326`.

    """

    def get(
        self, request: Request, pk: int, left: float, right: float, bottom: float, top: float
    ) -> HttpResponse:
        tile_source = self.get_tile_source(request, pk)
        if not isinstance(tile_source, GDALFileTileSource):
            raise TypeError('Souce image must have geospatial reference.')
        units = request.query_params.get('units', 'EPSG:4326')
        encoding = request.query_params.get('encoding', 'TILED')
        path, mime_type = large_image_utilities.get_region_world(
            tile_source,
            left,
            right,
            bottom,
            top,
            units,
            encoding,
        )
        if not path:
            # TODO: should this raise error status?
            return HttpResponse(b'', content_type=mime_type)
        tile_binary = open(path, 'rb')
        return HttpResponse(tile_binary, content_type=mime_type)


class TileRegionPixelView(BaseTileView):
    """Returns region tile binary from pixel coordinates."""

    def get(
        self, request: Request, pk: int, left: float, right: float, bottom: float, top: float
    ) -> HttpResponse:
        tile_source = self.get_tile_source(request, pk)
        encoding = request.query_params.get('encoding', None)
        path, mime_type = large_image_utilities.get_region_pixel(
            tile_source,
            left,
            right,
            bottom,
            top,
            encoding=encoding,
        )
        tile_binary = open(path, 'rb')
        return HttpResponse(tile_binary, content_type=mime_type)
