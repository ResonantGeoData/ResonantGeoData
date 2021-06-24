from rgd.views import SpatialEntriesListView, _SpatialDetailView

from . import filters, models


class ImageSetSpatialDetailView(_SpatialDetailView):
    model = models.ImageSetSpatial


class RasterMetaEntriesListView(SpatialEntriesListView):
    model = models.RasterMetaEntry
    filter = filters.RasterMetaEntryFilter
    context_object_name = 'spatial_entries'
    template_name = 'rgd_imagery/rastermetaentry_list.html'


class RasterEntryDetailView(_SpatialDetailView):
    model = models.RasterMetaEntry
