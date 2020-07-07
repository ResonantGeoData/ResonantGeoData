from django.urls import path

from . import search
from . import views

urlpatterns = [
    path('geodata/rasters/', views.RasterEntriesListView.as_view()),
    path(
        'geodata/rasters/<int:pk>/',
        views.RasterEntryDetailView.as_view(),
        name='raster-entry-detail',
    ),
    path(
        'api/geodata/download/<model>/<int:id>/<field>', views.download_file, name='download-file'
    ),
    path('api/geodata/near_point', search.search_near_point),
]
