from rgd.views import PermissionDetailView, SpatialEntriesListView
from rgd_3d import filters, models


class Mesh3DDetailView(PermissionDetailView):
    model = models.Mesh3D


class Mesh3DListView(SpatialEntriesListView):
    queryset = models.Mesh3DSpatial.objects.all()
    template_name = 'rgd_3d/mesh3d_list.html'
    filterset_class = filters.Mesh3DFilter
