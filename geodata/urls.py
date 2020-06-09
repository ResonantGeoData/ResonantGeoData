from django.urls import path

from . import views

urlpatterns = [
    path('geodata/rasters/', views.RasterEntriesListView.as_view()),
    path(
        'geodata/rasters/<int:pk>/',
        views.RasterEntryDetailView.as_view(),
        name='raster-entry-detail',
    ),
]
