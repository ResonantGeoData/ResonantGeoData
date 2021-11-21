from django.urls import path
from rest_framework.routers import SimpleRouter
from rgd_geometry import models, views
from rgd_geometry.rest import viewsets

router = SimpleRouter(trailing_slash=False)
router.register(r'api/rgd_geometry', viewsets.GeometryViewSet)
router.register(r'api/rgd_geometry/geometry_archive', viewsets.GeometryArchiveViewSet)

urlpatterns = [
    # Pages
    path(
        'rgd_geometry/<int:pk>/',
        views.GeometryDetailView.as_view(),
        name=models.Geometry.detail_view_name,
    ),
] + router.urls
