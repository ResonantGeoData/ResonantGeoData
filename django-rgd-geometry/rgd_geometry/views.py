from rgd.views import _SpatialDetailView

from . import models


class GeometryDetailView(_SpatialDetailView):
    model = models.Geometry

    def _get_extent(self, object):
        extent = super()._get_extent(object)
        extent['data'] = object.data.json
        return extent
