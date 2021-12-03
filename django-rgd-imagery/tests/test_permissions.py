from rgd.rest.mixins import BaseRestViewMixin
from rgd.views import PermissionDetailView, PermissionListView, PermissionTemplateView
from rgd_imagery.urls import urlpatterns


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
