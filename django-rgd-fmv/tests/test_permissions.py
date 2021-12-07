from rgd.rest.mixins import BaseRestViewMixin
from rgd.views import PermissionDetailView, PermissionListView, PermissionTemplateView
from rgd_fmv.urls import urlpatterns


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
