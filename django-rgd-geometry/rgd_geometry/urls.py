from django.urls import path

from . import models, rest, views

urlpatterns = [
    # Pages
    path(
        'rgd_geometry/<int:pk>/',
        views.GeometryDetailView.as_view(),
        name=models.Geometry.detail_view_name,
    ),
    #############
    # Other
    path(
        'api/rgd_geometry/<int:pk>',
        rest.get.GetGeometry.as_view(),
        name='geometry-entry',
    ),
    path(
        'api/rgd_geometry/<int:pk>/data',
        rest.get.GetGeometryData.as_view(),
        name='geometry-entry-data',
    ),
]
