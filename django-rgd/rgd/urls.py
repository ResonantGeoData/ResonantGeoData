from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import SimpleRouter
from rgd import views
from rgd.rest import viewsets

router = SimpleRouter(trailing_slash=False)
router.register(r'api/rgd/collection', viewsets.CollectionViewSet)
router.register(r'api/rgd/collection_permission', viewsets.CollectionPermissionViewSet)
router.register(r'api/rgd/checksum_file', viewsets.ChecksumFileViewSet)
router.register(r'api/rgd/spatial_entry', viewsets.SpatialEntryViewSet)
router.register(r'api/rgd/spatial_asset', viewsets.SpatialAssetViewSet)

urlpatterns = [
    # API Key Authentication
    path('api/api-token-auth', obtain_auth_token, name='api-token-auth'),
    path('api/signature', viewsets.SignatureView.as_view(), name='signature'),
    # Pages
    path('', views.SpatialEntriesListView.as_view(), name='rgd-index'),
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
    # Deprecated
    # TODO: remove route. duplicated functionality in 'rgd.viewsets.SpatialEntryViewSet'
    path(
        'api/rgd/search',
        viewsets.SpatialEntryViewSet.as_view({'get': 'list'}),
    ),
] + router.urls
