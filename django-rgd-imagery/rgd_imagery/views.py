from rgd.views import SpatialEntriesListView, _SpatialDetailView

from . import filters, models


class ImageSetSpatialDetailView(_SpatialDetailView):
    model = models.ImageSetSpatial


class RasterMetaEntriesListView(SpatialEntriesListView):
    model = models.RasterMeta
    filter = filters.RasterMetaFilter
    context_object_name = 'spatial_entries'
    template_name = 'rgd_imagery/rastermeta_list.html'


class RasterDetailView(_SpatialDetailView):
    model = models.RasterMeta
