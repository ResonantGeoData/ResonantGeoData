from django.apps import apps
from rgd.mixins import BaseRestViewMixin
from rgd.views import PermissionDetailView, PermissionListView, PermissionTemplateView
from rgd_imagery.urls import urlpatterns
from rgd_testing_utils.helpers import check_model_permissions


def test_check_permissions_path_rgd_imagery():
    for model in apps.get_app_config('rgd_imagery').get_models():
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
                    PermissionTemplateView,
                    PermissionDetailView,
                    PermissionListView,
                ),
            )
