from django.urls import path

from . import models, rest, views

urlpatterns = [
    # Pages
    path(
        'rgd_fmv/<int:pk>/',
        views.FMVEntryDetailView.as_view(),
        name=models.FMVEntry.detail_view_name,
    ),
    #############
    # Other
    path(
        'api/rgd_fmv/<int:pk>',
        rest.get.GetFMVEntry.as_view(),
        name='fmv-entry',
    ),
    path(
        'api/rgd_fmv/<int:pk>/data',
        rest.get.GetFMVDataEntry.as_view(),
        name='fmv-entry-data',
    ),
]
