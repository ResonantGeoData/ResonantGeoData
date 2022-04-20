from django.urls import path
from rest_framework.routers import SimpleRouter
from rgd_3d import models, views
from rgd_3d.rest import viewsets

router = SimpleRouter(trailing_slash=False)
router.register(r'api/rgd_3d/mesh', viewsets.Mesh3DViewSet, basename='mesh-3d')
router.register(r'api/rgd_3d/tiles3d', viewsets.Tiles3DViewSet, basename='tiles-3d')

urlpatterns = [
    # Pages
    path('rgd_3d/mesh/', views.Mesh3DListView.as_view(), name='meshes'),
    path(
        'rgd_3d/mesh/<int:pk>/',
        views.Mesh3DDetailView.as_view(),
        name=models.Mesh3D.detail_view_name,
    ),
    path(
        'rgd_3d/tiles3d/<int:pk>/',
        views.Tiles3DDetailView.as_view(),
        name=models.Tiles3D.detail_view_name,
    ),
] + router.urls
