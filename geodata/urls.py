from django.urls import path

from . import search, views

urlpatterns = [
    path('geodata/rasters/', views.RasterEntriesListView.as_view(), name='rasters'),
    path(
        'geodata/rasters/<int:pk>/',
        views.RasterEntryDetailView.as_view(),
        name='raster-entry-detail',
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
]
