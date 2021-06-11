from rgd import permissions
from rgd.views import _SpatialDetailView, _SpatialListView

from . import filters, models


class ImageSetSpatialDetailView(_SpatialDetailView):
    model = models.ImageSetSpatial


class RasterMetaEntriesListView(_SpatialListView):
    model = models.RasterMetaEntry
    filter = filters.RasterMetaEntryFilter
    context_object_name = 'spatial_entries'
    template_name = 'rgd_imagery/raster_entries.html'

    def get_queryset(self):
        filterset = self.filter(data=self.request.GET)
        assert filterset.is_valid()
        queryset = filterset.filter_queryset(self.model.objects.select_related('parent_raster'))
        return permissions.filter_read_perm(self.request.user, queryset).order_by('spatial_id')


class RasterEntryDetailView(_SpatialDetailView):
    model = models.RasterMetaEntry
