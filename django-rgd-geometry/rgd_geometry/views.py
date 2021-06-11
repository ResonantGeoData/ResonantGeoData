from rgd.views import _SpatialDetailView

from . import models


class GeometryEntryDetailView(_SpatialDetailView):
    model = models.GeometryEntry

    def _get_extent(self):
        extent = super()._get_extent()
        extent['data'] = self.object.data.json
        return extent
