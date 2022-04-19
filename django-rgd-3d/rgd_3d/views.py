from rgd.views import PermissionDetailView, PermissionListView
from rgd_3d import models


class Mesh3DListView(PermissionListView):
    paginate_by = 15
    context_object_name = 'mesh3ds'
    queryset = models.Mesh3D.objects.all()
    template_name = 'rgd_3d/mesh3d_list.html'


class Mesh3DDetailView(PermissionDetailView):
    model = models.Mesh3D


class Tiles3DDetailView(PermissionDetailView):
    model = models.Tiles3D
