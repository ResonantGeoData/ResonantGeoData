from rgd.views import SpatialDetailView

from . import models


class GeometryDetailView(SpatialDetailView):
    model = models.Geometry

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        extents = context['extents']
        extents['data'] = self.object.data.json
        return context
