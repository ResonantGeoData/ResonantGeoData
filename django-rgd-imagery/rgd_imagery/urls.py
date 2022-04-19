from django.urls import include, path, register_converter
from rest_framework.routers import SimpleRouter
from rgd_imagery import models, views
from rgd_imagery.rest import tiles, viewsets

router = SimpleRouter(trailing_slash=False)
router.register(r'api/image_process/group', viewsets.ProcessedImageGroupViewSet)
router.register(r'api/image_process', viewsets.ProcessedImageViewSet)
router.register(r'api/rgd_imagery/image_set_spatial', viewsets.ImageSetSpatialViewSet)
router.register(r'api/rgd_imagery/image_set', viewsets.ImageSetViewSet)
router.register(r'api/rgd_imagery/raster', viewsets.RasterMetaViewSet, basename='raster')
router.register(r'api/rgd_imagery/tiles', tiles.TilesViewSet, basename='image-tiles')
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
        'rgd_imagery/image_set/',
        views.ImageSetListView.as_view(),
        name='image-sets',
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
    path(
        'api/stac/',
        include('rgd_imagery.stac.urls'),
    ),
    path('', include('django_large_image.urls')),
] + router.urls
