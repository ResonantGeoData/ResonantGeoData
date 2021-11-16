from rgd.views import PermissionDetailView
from rgd_3d import models


class Mesh3DMetaDetailView(PermissionDetailView):
    model = models.Mesh3DMeta
