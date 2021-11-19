from rgd.views import PermissionDetailView
from rgd_3d import models


class Mesh3DDetailView(PermissionDetailView):
    model = models.Mesh3D
