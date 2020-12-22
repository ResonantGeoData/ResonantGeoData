from django.urls import path
from django.views.generic.base import RedirectView

from . import api, views

urlpatterns = [
    # Pages
    path(
        'geodata/spatial_entries/', views.SpatialEntriesListView.as_view(), name='spatial_entries'
    ),
    path(
        'geodata/spatial_entries/<int:pk>/',
        views.SpatialEntryDetailView.as_view(),
        name='spatial-entry-detail',
    ),
    # Temporary redirect for home page
    path(r'', RedirectView.as_view(url='geodata/spatial_entries/', permanent=False), name='index'),
    path('geodata/fmv_entries/', views.FMVEntriesListView.as_view(), name='fmv_entries'),
    path('geodata/rasters/', views.RasterEntriesListView.as_view(), name='rasters'),
    path(
        'geodata/rasters/<int:pk>/',
        views.RasterEntryDetailView.as_view(),
        name='raster-entry-detail',
    ),
    path(
        'geodata/fmv_entries/<int:pk>/',
        views.FMVEntryDetailView.as_view(),
        name='fmv-entry-detail',
    ),
    path('geodata/geometries/', views.GeometryEntriesListView.as_view(), name='geometries'),
    path(
        'geodata/geometries/<int:pk>/',
        views.GeometryEntryDetailView.as_view(),
        name='geometry-entry-detail',
    ),
    #############
    path(
        'api/geodata/download/<model>/<int:id>/<field>',
        api.download.download_file,
        name='download-file',
    ),
    # Search
    path('api/geodata/near_point', api.search.search_near_point),
    path('api/geodata/raster/near_point', api.search.search_near_point_raster),
    path('api/geodata/geometry/near_point', api.search.search_near_point_geometry),
    path('api/geodata/near_point/extent', api.search.search_near_point_extent),
    path('api/geodata/raster/near_point/extent', api.search.search_near_point_extent_raster),
    path('api/geodata/geometry/near_point/extent', api.search.search_near_point_extent_geometry),
    path('api/geodata/bounding_box', api.search.search_bounding_box),
    path('api/geodata/raster/bounding_box', api.search.search_bounding_box_raster),
    path('api/geodata/geometry/bounding_box', api.search.search_bounding_box_geometry),
    path('api/geodata/bounding_box/extent', api.search.search_bounding_box_extent),
    path('api/geodata/raster/bounding_box/extent', api.search.search_bounding_box_extent_raster),
    path(
        'api/geodata/geometry/bounding_box/extent', api.search.search_bounding_box_extent_geometry
    ),
    path('api/geodata/geojson', api.search.search_geojson),
    path('api/geodata/raster/geojson', api.search.search_geojson_raster),
    path('api/geodata/geometry/geojson', api.search.search_geojson_geometry),
    path('api/geodata/geojson/extent', api.search.search_geojson_extent),
    path('api/geodata/raster/geojson/extent', api.search.search_geojson_extent_raster),
    path('api/geodata/geometry/geojson/extent', api.search.search_geojson_extent_geometry),
    path('api/geodata/search', api.search.SearchSpatialEntryView.as_view()),
    # Other
    path(
        'api/geodata/common/arbitraty_file/<int:pk>/',
        api.get.GetArbitraryFile.as_view(),
        name='arbitrary-file',
    ),
    path(
        'api/geodata/common/arbitrary_file/<int:pk>/data',
        api.download.download_arbitrary_file,
        name='arbitrary-file-data',
    ),
    path(
        'api/geodata/imagery/image_entry/<int:pk>/data',
        api.download.download_image_entry_file,
        name='image-entry-data',
    ),
    path(
        'api/geodata/common/spatial_entry/<int:pk>/',
        api.get.GetSpatialEntry.as_view(),
        name='spatial-entry',
    ),
    path('api/geodata/imagery/cog', api.post.CreateConvertedImageFile.as_view()),
    path(
        'api/geodata/imagery/cog/<int:pk>/',
        api.get.GetConvertedImageStatus.as_view(),
        name='cog',
    ),
    path(
        'api/geodata/imagery/cog/<int:pk>/data',
        api.download.download_cog_file,
        name='cog-data',
    ),
    path(
        'api/geodata/imagery/subsample/',
        api.post.CreateSubsampledImage.as_view(),
    ),
    path(
        'api/geodata/imagery/subsample/<int:pk>/',
        api.get.GetSubsampledImage.as_view(),
        name='subsampled',
    ),
]
