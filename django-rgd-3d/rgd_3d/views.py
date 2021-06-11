from rgd.views import PermissionDetailView
from rgd_3d import models


class PointCloudEntryDetailView(PermissionDetailView):
    model = models.PointCloudEntry
