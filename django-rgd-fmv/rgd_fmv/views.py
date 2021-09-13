import json

from rgd.views import _SpatialDetailView

from . import models


class FMVMetaDetailView(_SpatialDetailView):
    model = models.FMVMeta

    def _get_extent(self, object):
        extent = super()._get_extent(object)
        if object.ground_union is not None:
            # All or none of these will be set, only check one
            extent['collect'] = object.ground_union.json
            extent['ground_frames'] = object.ground_frames.json
            extent['frame_numbers'] = object._blob_to_array(object.frame_numbers)
        return extent

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['frame_rate'] = json.dumps(self.object.fmv_file.frame_rate)
        return context
