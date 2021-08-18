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
    path(
        'api/rgd/checksum_file',
        rest.post.CreateChecksumFile.as_view(),
        name='checksum-create',
    ),
    path(
        'api/rgd/collection',
        rest.post.CreateCollection.as_view(),
        name='collection-create',
    ),
    path(
        'api/rgd/collection/<int:pk>',
        rest.get.GetCollection.as_view(),
        name='collection',
    ),
    path(
        'api/rgd/collection_permission',
        rest.post.CreateCollectionPermission.as_view(),
        name='collection-permission-create',
    ),
    path(
        'api/rgd/collection_permission/<int:pk>',
        rest.get.GetCollectionPermission.as_view(),
        name='collection-permission',
    ),
    path(
        'api/rgd/spatial_asset',
        rest.post.CreateSpatialAsset.as_view(),
        name='spatial-asset-create',
    ),
    path(
        'api/rgd/spatial_asset/<int:pk>',
        rest.get.GetSpatialAsset.as_view(),
        name='spatial-asset',
    ),
]
