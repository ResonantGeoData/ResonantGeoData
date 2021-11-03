from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import SimpleRouter
from rgd import rest, views
from rgd.rest import viewsets

router = SimpleRouter(trailing_slash=False)
router.register(r'api/rgd/collection', viewsets.CollectionViewSet)
router.register(r'api/rgd/collection_permission', viewsets.CollectionPermissionViewSet)

urlpatterns = [
    # API Key Authentication
    path('api/api-token-auth', obtain_auth_token, name='api-token-auth'),
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
        'api/rgd/spatial_asset',
        rest.post.CreateSpatialAsset.as_view(),
        name='spatial-asset-create',
    ),
    path(
        'api/rgd/spatial_asset/<int:pk>',
        rest.get.GetSpatialAsset.as_view(),
        name='spatial-asset',
    ),
] + router.urls
