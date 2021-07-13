from django.urls import path

from . import rest, views

urlpatterns = [
    # Pages
    path('rgd', views.SpatialEntriesListView.as_view(), name='rgd-index'),
    path(
        'rgd/statistics',
        views.StatisticsView.as_view(),
        name='statistics',
    ),
    path(
        'rgd/spatial_entries/<int:pk>/',
        views.spatial_entry_redirect_view,
        name='spatial-entry-detail',
    ),
    #############
    # Search
    path('api/rgd/search', rest.search.SearchSpatialEntryView.as_view()),
    #############
    # Other
    path(
        'api/rgd/status/<model>/<int:pk>',
        rest.download.get_status,
        name='get-status',
    ),
    path(
        'api/rgd/spatial_entry/<int:spatial_id>',
        rest.get.GetSpatialEntry.as_view(),
        name='spatial-entry',
    ),
    path(
        'api/rgd/spatial_entry/<int:spatial_id>/footprint',
        rest.get.GetSpatialEntryFootprint.as_view(),
        name='spatial-entry-footprint',
    ),
    path(
        'api/rgd/checksum_file/<int:pk>',
        rest.get.GetChecksumFile.as_view(),
        name='checksum-file',
    ),
    path(
        'api/rgd/checksum_file/<int:pk>/data',
        rest.download.download_checksum_file,
        name='checksum-file-data',
    ),
]
