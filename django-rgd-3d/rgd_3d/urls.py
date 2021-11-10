from django.urls import path
from rest_framework.routers import SimpleRouter
from rgd_3d import models, views
from rgd_3d.rest import viewsets

router = SimpleRouter(trailing_slash=False)
router.register(r'api/rgd_3d/point_cloud', viewsets.PointCloudMetaViewSet)

urlpatterns = [
    # Pages
    path(
        'rgd_3d/point_cloud/<int:pk>/',
        views.PointCloudMetaDetailView.as_view(),
        name=models.PointCloudMeta.detail_view_name,
    ),
] + router.urls
