from rgd.views import PermissionDetailView
from rgd_3d import models


class PointCloudMetaDetailView(PermissionDetailView):
    model = models.PointCloudMeta
