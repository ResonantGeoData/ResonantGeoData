from django.urls import path
from rest_framework.routers import SimpleRouter
from rgd_3d import models, views
from rgd_3d.rest import viewsets

router = SimpleRouter(trailing_slash=False)
router.register(r'api/rgd_3d/mesh', viewsets.Mesh3DMetaViewSet, basename='mesh-3d')

urlpatterns = [
    # Pages
    path(
        'rgd_3d/mesh/<int:pk>/',
        views.Mesh3DMetaDetailView.as_view(),
        name=models.Mesh3DMeta.detail_view_name,
    ),
] + router.urls
