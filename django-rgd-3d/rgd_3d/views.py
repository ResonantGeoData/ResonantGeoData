from rgd.views import PermissionDetailView

from . import models


class PointCloudEntryDetailView(PermissionDetailView):
    model = models.PointCloudEntry
