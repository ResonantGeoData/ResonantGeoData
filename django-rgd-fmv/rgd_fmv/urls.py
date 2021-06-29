from django.urls import path

from . import models, rest, views

urlpatterns = [
    # Pages
    path(
        'rgd_fmv/<int:pk>/',
        views.FMVMetaDetailView.as_view(),
        name=models.FMVMeta.detail_view_name,
    ),
    #############
    # Other
    path(
        'api/rgd_fmv/<int:pk>',
        rest.get.GetFMVMeta.as_view(),
        name='fmv-entry',
    ),
    path(
        'api/rgd_fmv/<int:pk>/data',
        rest.get.GetFMVDataEntry.as_view(),
        name='fmv-entry-data',
    ),
]
