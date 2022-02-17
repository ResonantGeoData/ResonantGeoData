from rgd.views import PermissionDetailView
from rgd_3d import models


class Mesh3DDetailView(PermissionDetailView):
    model = models.Mesh3D


class Tiles3DDetailView(PermissionDetailView):
    model = models.Tiles3D
