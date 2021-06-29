from rgd.views import _SpatialDetailView

from . import models


class GeometryDetailView(_SpatialDetailView):
    model = models.Geometry

    def _get_extent(self):
        extent = super()._get_extent()
        extent['data'] = self.object.data.json
        return extent
