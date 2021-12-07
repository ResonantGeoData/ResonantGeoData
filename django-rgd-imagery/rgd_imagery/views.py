from rgd.views import (
    PermissionDetailView,
    PermissionTemplateView,
    SpatialDetailView,
    SpatialEntriesListView,
)

from . import filters, models


class ImageSetDetailView(PermissionDetailView):
    model = models.ImageSet


class RasterMetaEntriesListView(SpatialEntriesListView):
    queryset = models.RasterMeta.objects.all()
    template_name = 'rgd_imagery/rastermeta_list.html'
    filterset_class = filters.RasterMetaFilter


class RasterDetailView(SpatialDetailView):
    model = models.RasterMeta


class STACBrowserView(PermissionTemplateView):
    template_name = 'rgd_imagery/stac/stac_browser.html'
