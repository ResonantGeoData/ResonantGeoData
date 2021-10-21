from django.apps import apps
from rgd.rest.mixins import BaseRestViewMixin
from rgd.views import PermissionDetailView, PermissionListView, PermissionTemplateView
from rgd_fmv.urls import urlpatterns
from rgd_testing_utils.helpers import check_model_permissions


def test_check_permissions_path_rgd_fmv():
    for model in apps.get_app_config('rgd_fmv').get_models():
        check_model_permissions(model)


def test_urls():
    for pattern in urlpatterns:
        if hasattr(pattern.callback, 'view_class') and 'WrappedAPIView' not in str(
            pattern.callback
        ):
            assert issubclass(
                pattern.callback.view_class,
                (
                    BaseRestViewMixin,
                    PermissionDetailView,
                    PermissionTemplateView,
                    PermissionListView,
                ),
            )
