from django.urls import path
from django.views.generic.base import RedirectView

from . import search, views

urlpatterns = [
    path(
        'geodata/spatial_entries/', views.SpatialEntriesListView.as_view(), name='spatial_entries'
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
    path(
        'api/geodata/download/<model>/<int:id>/<field>', views.download_file, name='download-file'
    ),
    path('api/geodata/near_point', search.search_near_point),
    path('api/geodata/raster/near_point', search.search_near_point_raster),
    path('api/geodata/geometry/near_point', search.search_near_point_geometry),
    path('api/geodata/near_point/extent', search.search_near_point_extent),
    path('api/geodata/raster/near_point/extent', search.search_near_point_extent_raster),
    path('api/geodata/geometry/near_point/extent', search.search_near_point_extent_geometry),
    path('api/geodata/bounding_box', search.search_bounding_box),
    path('api/geodata/raster/bounding_box', search.search_bounding_box_raster),
    path('api/geodata/geometry/bounding_box', search.search_bounding_box_geometry),
    path('api/geodata/bounding_box/extent', search.search_bounding_box_extent),
    path('api/geodata/raster/bounding_box/extent', search.search_bounding_box_extent_raster),
    path('api/geodata/geometry/bounding_box/extent', search.search_bounding_box_extent_geometry),
    path('api/geodata/geojson', search.search_geojson),
    path('api/geodata/raster/geojson', search.search_geojson_raster),
    path('api/geodata/geometry/geojson', search.search_geojson_geometry),
    path('api/geodata/geojson/extent', search.search_geojson_extent),
    path('api/geodata/raster/geojson/extent', search.search_geojson_extent_raster),
    path('api/geodata/geometry/geojson/extent', search.search_geojson_extent_geometry),
]
