from django.urls import path

from . import rest, views

urlpatterns = [
    # Pages
    path(
        'rgd_geometry/<int:pk>/',
        views.GeometryEntryDetailView.as_view(),
        name='geometry-entry-detail',
    ),
    #############
    # Other
    path(
        'api/rgd_geometry/<int:pk>',
        rest.get.GetGeometryEntry.as_view(),
        name='geometry-entry',
    ),
    path(
        'api/rgd_geometry/<int:pk>/data',
        rest.get.GetGeometryEntryData.as_view(),
        name='geometry-entry-data',
    ),
]
