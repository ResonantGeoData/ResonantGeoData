from django.urls import include, path, register_converter
from rest_framework.routers import SimpleRouter
from rgd_imagery import models, rest, views
from rgd_imagery.rest import viewsets

router = SimpleRouter(trailing_slash=False)
router.register(r'api/image_process/group', viewsets.ProcessedImageGroupViewSet)
router.register(r'api/image_process', viewsets.ProcessedImageViewSet)
router.register(r'api/rgd_imagery/image_set_spatial', viewsets.ImageSetSpatialViewSet)
router.register(r'api/rgd_imagery/image_set', viewsets.ImageSetViewSet)
router.register(r'api/rgd_imagery/raster', viewsets.RasterViewSet, basename='raster')
router.register(r'api/rgd_imagery', viewsets.ImageViewSet, basename='imagery')


class FloatUrlParameterConverter:
    regex = r'-?[0-9]+\.?[0-9]+'

    def to_python(self, value):
        return float(value)

    def to_url(self, value):
        return str(value)


register_converter(FloatUrlParameterConverter, 'float')


urlpatterns = [
    # Pages
    path(r'rgd_imagery/raster/', views.RasterMetaEntriesListView.as_view(), name='raster-search'),
    path(
        'rgd_imagery/raster/<int:pk>/',
        views.RasterDetailView.as_view(),
        name=models.RasterMeta.detail_view_name,
    ),
    path(
        'rgd_imagery/image_set/<int:pk>/',
        views.ImageSetDetailView.as_view(),
        name=models.ImageSet.detail_view_name,
    ),
    path(
        'rgd_imagery/stac_browser/',
        views.STACBrowserView.as_view(),
        name='stac-browser',
    ),
    #############
    # Geoprocessing
    path(
        'api/image_process/imagery/<int:pk>/tiles',
        rest.tiles.TileMetadataView.as_view(),
        name='image-tile-metadata',
    ),
    path(
        'api/image_process/imagery/<int:pk>/tiles/internal',
        rest.tiles.TileInternalMetadataView.as_view(),
        name='image-tile-internal-metadata',
    ),
    path(
        'api/image_process/imagery/<int:pk>/tiles/<int:z>/<int:x>/<int:y>.png',
        rest.tiles.TileView.as_view(),
        name='image-tiles',
    ),
    path(
        'api/image_process/imagery/<int:pk>/tiles/region/world/<float:left>/<float:right>/<float:bottom>/<float:top>/region.tif',
        rest.tiles.TileRegionView.as_view(),
        name='image-region',
    ),
    path(
        'api/image_process/imagery/<int:pk>/tiles/region/pixel/<int:left>/<int:right>/<int:bottom>/<int:top>/region.tif',
        rest.tiles.TileRegionPixelView.as_view(),
        name='image-region-pixel',
    ),
    path(
        'api/image_process/imagery/<int:pk>/tiles/<int:z>/<int:x>/<int:y>/corners',
        rest.tiles.TileCornersView.as_view(),
        name='image-tile-corners',
    ),
    path(
        'api/image_process/imagery/<int:pk>/thumbnail',
        rest.tiles.TileThumnailView.as_view(),
        name='image-thumbnail',
    ),
    path(
        'api/image_process/imagery/<int:pk>/bands',
        rest.tiles.TileBandInfoView.as_view(),
        name='image-bands',
    ),
    path(
        'api/image_process/imagery/<int:pk>/bands/<int:band>',
        rest.tiles.TileSingleBandInfoView.as_view(),
        name='image-bands-single',
    ),
    path(
        'api/stac/',
        include('rgd_imagery.stac.urls'),
    ),
] + router.urls
