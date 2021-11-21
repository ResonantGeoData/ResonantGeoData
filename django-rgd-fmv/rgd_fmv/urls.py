from django.urls import path
from rest_framework.routers import SimpleRouter
from rgd_fmv import models, views
from rgd_fmv.rest import viewsets

router = SimpleRouter(trailing_slash=False)
router.register(r'api/rgd_fmv', viewsets.FMVViewSet)

urlpatterns = [
    # Pages
    path(
        'rgd_fmv/<int:pk>/',
        views.FMVMetaDetailView.as_view(),
        name=models.FMVMeta.detail_view_name,
    ),
] + router.urls
