from django.urls import path
from rgd_3d import rest, views

urlpatterns = [
    # Pages
    path(
        'rgd_3d/point_cloud/<int:pk>/',
        views.PointCloudEntryDetailView.as_view(),
        name='point-cloud-entry-detail',
    ),
    #############
    # Other
    path(
        'api/rgd_3d/point_cloud/<int:pk>',
        rest.get.GetPointCloudEntry.as_view(),
        name='point-cloud-entry',
    ),
    path(
        'api/rgd_3d/point_cloud/<int:pk>/base64',
        rest.get.GetPointCloudEntryData.as_view(),
        name='point-cloud-entry-data',
    ),
]
