import json

from rgd.views import (
    PermissionDetailView,
    PermissionListView,
    PermissionTemplateView,
    SpatialDetailView,
    SpatialEntriesListView,
)

from . import filters, models


class ImageSetDetailView(PermissionDetailView):
    model = models.ImageSet


class RasterMetaEntriesListView(SpatialEntriesListView):
    queryset = models.RasterMeta.objects.all()
    template_name = 'rgd_imagery/rastermeta_list.html'
    filterset_class = filters.RasterMetaFilter


class RasterDetailView(SpatialDetailView):
    model = models.RasterMeta

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        import cmocean  # noqa
        import matplotlib.pyplot

        colorlist = {'mpl': list(matplotlib.pyplot.colormaps())}
        context['colormaps'] = json.dumps(colorlist)
        return context


class STACBrowserView(PermissionTemplateView):
    template_name = 'rgd_imagery/stac/stac_browser.html'


class ImageSetListView(PermissionListView):
    paginate_by = 15
    context_object_name = 'image_sets'
    queryset = models.ImageSet.objects.all()
    template_name = 'rgd_imagery/imageset_list.html'
