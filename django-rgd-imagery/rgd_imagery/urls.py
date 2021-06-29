from django.urls import path, register_converter

from . import models, rest, views


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
        views.ImageSetSpatialDetailView.as_view(),
        name=models.ImageSetSpatial.detail_view_name,
    ),
    #############
    # Search
    path('api/rgd_imagery/raster/search', rest.search.SearchRasterMetaSTACView.as_view()),
    #############
    # Other
    path(
        'api/rgd_imagery/<int:pk>',
        rest.get.GetImageMeta.as_view(),
        name='image-entry',
    ),
    path(
        'api/rgd_imagery/<int:pk>/data',
        rest.download.download_image_file,
        name='image-entry-data',
    ),
    path(
        'api/rgd_imagery/image_set/<int:pk>',
        rest.get.GetImageSet.as_view(),
        name='image-set',
    ),
    path(
        'api/rgd_imagery/raster/<int:pk>',
        rest.get.GetRasterMeta.as_view(),
        name='raster-meta-entry',
    ),
    path(
        'api/rgd_imagery/raster/<int:pk>/stac',
        rest.get.GetRasterMetaSTAC.as_view(),
        name='raster-meta-entry-stac',
    ),
    path(
        'api/rgd_imagery/raster/stac',
        rest.post.CreateRasterSTAC.as_view(),
        name='raster-meta-entry-stac-post',
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
    path('api/image_process/imagery/cog', rest.post.CreateConvertedImage.as_view()),
    path(
        'api/image_process/imagery/cog/<int:pk>',
        rest.get.GetConvertedImageStatus.as_view(),
        name='cog',
    ),
    path(
        'api/image_process/imagery/cog/<int:pk>/data',
        rest.download.download_cog_file,
        name='cog-data',
    ),
    path(
        'api/image_process/imagery/subsample',
        rest.post.CreateRegionImage.as_view(),
    ),
    path(
        'api/image_process/imagery/subsample/<int:pk>',
        rest.get.GetRegionImage.as_view(),
        name='subsampled',
    ),
    path(
        'api/image_process/imagery/subsample/<int:pk>/status',
        rest.download.get_status_subsampled_image,
        name='subsampled-status',
    ),
]
