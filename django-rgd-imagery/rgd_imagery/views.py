from rgd.views import (
    PermissionDetailView,
    PermissionTemplateView,
    SpatialEntriesListView,
    _SpatialDetailView,
)

from . import filters, models


class ImageSetDetailView(PermissionDetailView):
    model = models.ImageSet


class RasterMetaEntriesListView(SpatialEntriesListView):
    model = models.RasterMeta
    filter = filters.RasterMetaFilter
    context_object_name = 'spatial_entries'
    template_name = 'rgd_imagery/rastermeta_list.html'


class RasterDetailView(_SpatialDetailView):
    model = models.RasterMeta


class STACBrowserView(PermissionTemplateView):
    template_name = 'rgd_imagery/stac_browser.html'
