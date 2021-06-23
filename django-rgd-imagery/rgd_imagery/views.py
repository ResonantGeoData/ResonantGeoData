from rgd.views import _SpatialDetailView, SpatialEntriesListView

from . import filters, models


class ImageSetSpatialDetailView(_SpatialDetailView):
    model = models.ImageSetSpatial


class RasterMetaEntriesListView(SpatialEntriesListView):
    model = models.RasterMetaEntry
    filter = filters.RasterMetaEntryFilter
    context_object_name = 'spatial_entries'
    template_name = 'rgd_imagery/raster_entries.html'


class RasterEntryDetailView(_SpatialDetailView):
    model = models.RasterMetaEntry
