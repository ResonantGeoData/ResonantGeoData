import json

from django.contrib.gis.db.models import Collect, Extent
from django.db.models import Max, Min
from django.shortcuts import redirect
from django.views import generic
from django.views.generic import DetailView
from rest_framework.reverse import reverse

from rgd.geodata import permissions

from .filters import RasterMetaEntryFilter, SpatialEntryFilter
from .models.common import SpatialEntry
from .models.fmv.base import FMVEntry
from .models.geometry import GeometryEntry
from .models.imagery import RasterMetaEntry
from .models.threed import PointCloudEntry, PointCloudMetaEntry


class PermissionDetailView(DetailView):
    def get_object(self):
        obj = super().get_object()
        permissions.check_read_perm(self.request.user, obj)
        return obj


def query_params(params):
    query = params.copy()

    if query.get('page'):
        del query['page']

    return '&' + query.urlencode() if query.urlencode() else ''


class _SpatialListView(generic.ListView):
    paginate_by = 15

    def get_queryset(self):
        filterset = self.filter(data=self.request.GET)
        assert filterset.is_valid()
        queryset = filterset.filter_queryset(self.model.objects.all())
        return permissions.filter_read_perm(self.request.user, queryset).order_by('spatial_id')

    def _get_extent_summary(self, object_list):
        ids = [o.spatial_id for o in object_list]
        queryset = self.model.objects.filter(spatial_id__in=ids)
        summary = queryset.aggregate(
            Collect('outline'),
            Extent('outline'),
        )
        extents = {
            'count': queryset.count(),
        }
        if queryset.count():
            extents.update(
                {
                    'collect': json.loads(summary['outline__collect'].geojson),
                    'convex_hull': json.loads(summary['outline__collect'].convex_hull.geojson),
                    'extent': {
                        'xmin': summary['outline__extent'][0],
                        'ymin': summary['outline__extent'][1],
                        'xmax': summary['outline__extent'][2],
                        'ymax': summary['outline__extent'][3],
                    },
                }
            )
        return extents

    def get_context_data(self, *args, **kwargs):
        # Pagination happens here
        context = super().get_context_data(*args, **kwargs)
        summary = self._get_extent_summary(context['object_list'])
        context['extents'] = json.dumps(summary)
        # Have a smaller dict of meta fields to parse for menu bar
        # This keeps us from parsing long GeoJSON fields twice
        meta = {
            'count': self.get_queryset().count(),  # This is the amount in the full results
        }
        context['extents_meta'] = json.dumps(meta)
        context['search_params'] = json.dumps(self.request.GET)
        context['query_params'] = query_params(self.request.GET)
        return context


class SpatialEntriesListView(_SpatialListView):
    model = SpatialEntry
    filter = SpatialEntryFilter
    context_object_name = 'spatial_entries'
    template_name = 'geodata/spatial_entries.html'


class StatisticsView(generic.ListView):
    paginate_by = None
    model = SpatialEntry
    context_object_name = 'spatial_entries'
    template_name = 'geodata/statistics.html'

    def get_queryset(self):
        queryset = self.model.objects.all()
        return permissions.filter_read_perm(self.request.user, queryset).order_by('spatial_id')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        q = self.get_queryset()
        context['count'] = q.count()
        context['coordinates'] = json.dumps([o.footprint.centroid.json for o in self.object_list])
        context['raster_count'] = q.filter(rastermetaentry__isnull=False).count()
        instrumentation = (
            q.filter(instrumentation__isnull=False).values_list('instrumentation').distinct()
        )
        context['instrumentation_count'] = instrumentation.count()
        dates = q.filter(acquisition_date__isnull=False).aggregate(
            Min('acquisition_date'),
            Max('acquisition_date'),
        )
        context['acquisition_date__min'] = dates['acquisition_date__min']
        context['acquisition_date__max'] = dates['acquisition_date__max']
        return context


class RasterMetaEntriesListView(_SpatialListView):
    model = RasterMetaEntry
    filter = RasterMetaEntryFilter
    context_object_name = 'spatial_entries'
    template_name = 'geodata/raster_entries.html'


class _SpatialDetailView(PermissionDetailView):
    def get_object(self):
        obj = super().get_object()
        permissions.check_read_perm(self.request.user, obj)
        return obj

    def _get_extent(self):
        extent = {
            'count': 0,
        }
        if self.object.footprint:
            extent.update(
                {
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
            )
        return extent

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['extents'] = json.dumps(self._get_extent())
        return context


class RasterEntryDetailView(_SpatialDetailView):
    model = RasterMetaEntry


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
    elif isinstance(sub, PointCloudMetaEntry):
        name = 'point-cloud-entry-detail'
        sub = sub.parent_point_cloud
    else:
        raise ValueError()
    return redirect(reverse(name, kwargs={'pk': sub.pk}))


class PointCloudEntryDetailView(PermissionDetailView):
    model = PointCloudEntry
