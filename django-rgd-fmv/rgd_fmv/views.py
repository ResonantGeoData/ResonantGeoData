import json

from rgd.views import SpatialDetailView

from . import models


class FMVMetaDetailView(SpatialDetailView):
    model = models.FMVMeta

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['frame_rate'] = json.dumps(self.object.fmv_file.frame_rate)
        extents = context['extents']
        if self.object.ground_union is not None:
            # All or none of these will be set, only check one
            extents['collect'] = self.object.ground_union.json
            extents['ground_frames'] = self.object.ground_frames.json
            extents['frame_numbers'] = self.object._blob_to_array(self.object.frame_numbers)
        return context
