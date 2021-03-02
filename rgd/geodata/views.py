import json

from django.shortcuts import redirect
from django.views import generic
from django.views.generic import DetailView
from rest_framework.reverse import reverse

from rgd.geodata import permissions

from .api import search
from .filters import SpatialEntryFilter
from .models.common import SpatialEntry
from .models.fmv.base import FMVEntry
from .models.geometry import GeometryEntry
from .models.imagery.base import RasterMetaEntry


def query_params(params):
    query = params.copy()

    if query.get('page'):
        del query['page']

    return '&' + query.urlencode() if query.urlencode() else ''


class _SpatialListView(generic.ListView):
    paginate_by = 15

    def get_queryset(self):
        filterset = SpatialEntryFilter(data=self.request.GET)
        assert filterset.is_valid()
        queryset = filterset.filter_queryset(self.model.objects.all())
        return permissions.filter_read_perm(self.request.user, queryset)

    def _get_extent_summary(self, object_list):
        return search.extent_summary_spatial(object_list)

    def get_context_data(self, *args, **kwargs):
        # Pagination happens here
        context = super().get_context_data(*args, **kwargs)
        summary = self._get_extent_summary(context['object_list'])
        context['extents'] = json.dumps(summary)
        context['search_params'] = json.dumps(self.request.GET)
        # Have a smaller dict of meta fields to parse for menu bar
        # This keeps us from parsing long GeoJSON fields twice
        meta = {
            'count': len(self.object_list),  # This is the amount in the full results
        }
        context['extents_meta'] = json.dumps(meta)
        context['query_params'] = query_params(self.request.GET)
        return context


class SpatialEntriesListView(_SpatialListView):
    model = SpatialEntry
    context_object_name = 'spatial_entries'
    template_name = 'geodata/spatial_entries.html'


class _SpatialDetailView(DetailView):
    def get_object(self):
        obj = super().get_object()
        permissions.check_read_perm(self.request.user, obj)
        return obj

    def _get_extent(self):
        if self.object.footprint is None:
            extent = {
                'count': 0,
            }
        else:
            extent = {
                'count': 1,
                'collect': self.object.footprint.json,
                'outline': self.object.outline.json,
                'extent': {
                    'xmin': self.object.footprint.extent[0],
                    'ymin': self.object.footprint.extent[1],
                    'xmax': self.object.footprint.extent[2],
                    'ymax': self.object.footprint.extent[3],
                },
            }
        return extent

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['extents'] = json.dumps(self._get_extent())
        context['search_params'] = json.dumps({})
        return context


class RasterEntryDetailView(_SpatialDetailView):
    model = RasterMetaEntry

    def _get_extent(self):
        extent = super()._get_extent()
        # Add a thumbnail of the first image in the raster set
        image_entries = self.object.parent_raster.image_set.images.all()
        image_urls = {}
        for image_entry in image_entries:
            thumbnail = image_entry.thumbnail
            image_urls[thumbnail.image_entry.id] = thumbnail.base_thumbnail.url
        extent['thumbnails'] = image_urls
        return extent


class FMVEntryDetailView(_SpatialDetailView):
    model = FMVEntry

    def _get_extent(self):
        extent = super()._get_extent()
        if self.object.ground_union is not None:
            # All or none of these will be set, only check one
            extent['collect'] = self.object.ground_union.json
            extent['ground_frames'] = self.object.ground_frames.json
            extent['frame_numbers'] = self.object._blob_to_array(self.object.frame_numbers)
        return extent

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['frame_rate'] = json.dumps(self.object.fmv_file.frame_rate)
        return context


class GeometryEntryDetailView(_SpatialDetailView):
    model = GeometryEntry

    def _get_extent(self):
        extent = super()._get_extent()
        extent['data'] = self.object.data.json
        return extent


def spatial_entry_redirect_view(request, pk):
    spat = SpatialEntry.objects.get(pk=pk)
    sub = spat.subentry
    if isinstance(sub, RasterMetaEntry):
        name = 'raster-entry-detail'
    elif isinstance(sub, GeometryEntry):
        name = 'geometry-entry-detail'
    elif isinstance(sub, FMVEntry):
        name = 'fmv-entry-detail'
    else:
        raise ValueError()
    return redirect(reverse(name, kwargs={'pk': sub.pk}))
