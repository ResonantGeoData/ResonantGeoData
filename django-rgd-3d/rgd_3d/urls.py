from django.urls import path
from rgd_3d import models, rest, views

urlpatterns = [
    # Pages
    path(
        'rgd_3d/point_cloud/<int:pk>/',
        views.PointCloudMetaDetailView.as_view(),
        name=models.PointCloudMeta.detail_view_name,
    ),
    #############
    # Other
    path(
        'api/rgd_3d/point_cloud/<int:pk>',
        rest.get.GetPointCloudMeta.as_view(),
        name='point-cloud-entry',
    ),
    path(
        'api/rgd_3d/point_cloud/<int:pk>/base64',
        rest.get.GetPointCloudMetaData.as_view(),
        name='point-cloud-entry-data',
    ),
]
