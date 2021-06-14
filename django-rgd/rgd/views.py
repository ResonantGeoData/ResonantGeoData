import json

from django.contrib.gis.db.models import Collect, Extent
from django.contrib.gis.db.models.functions import AsGeoJSON, Centroid
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Count, Max, Min, Q
from django.views import generic
from django.views.generic import DetailView
from rgd import permissions

from . import filters, models


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
    model = models.SpatialEntry
    filter = filters.SpatialEntryFilter
    context_object_name = 'spatial_entries'
    template_name = 'rgd/spatial_entries.html'

    def get_queryset(self):
        filterset = self.filter(data=self.request.GET)
        assert filterset.is_valid()
        queryset = filterset.filter_queryset(
            self.model.objects.select_related(
                'rastermetaentry',
                'rastermetaentry__parent_raster',
                'geometryentry',
                'fmventry',
                'pointcloudmetaentry',
                'imagesetspatial',
            )
        )
        return permissions.filter_read_perm(self.request.user, queryset).order_by('spatial_id')


class StatisticsView(generic.ListView):
    paginate_by = None
    model = models.SpatialEntry
    context_object_name = 'spatial_entries'
    template_name = 'rgd/statistics.html'

    def get_queryset(self):
        queryset = self.model.objects.all()
        return permissions.filter_read_perm(self.request.user, queryset)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            self.get_queryset().aggregate(
                count=Count('spatial_id', distinct=True),
                coordinates=ArrayAgg(AsGeoJSON(Centroid('footprint'))),
                raster_count=Count(
                    'spatial_id',
                    distinct=True,
                    filter=Q(rastermetaentry__isnull=False),
                ),
                instrumentation_count=Count(
                    'instrumentation',
                    distinct=True,
                    filter=Q(instrumentation__isnull=False),
                ),
                acquisition_date__min=Min(
                    'acquisition_date', filter=Q(acquisition_date__isnull=False)
                ),
                acquisition_date__max=Max(
                    'acquisition_date', filter=Q(acquisition_date__isnull=False)
                ),
                extents=Extent('outline'),
            )
        )
        context['coordinates'] = '[' + ','.join(context['coordinates']) + ']'
        extents = context['extents'] or [None] * 4
        context['extents'] = json.dumps(
            {
                'xmin': extents[0],
                'ymin': extents[1],
                'xmax': extents[2],
                'ymax': extents[3],
            }
        )
        return context


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


def spatial_entry_redirect_view(request, pk):
    spat = models.SpatialEntry.objects.get(pk=pk)  # noqa
    # sub = spat.subentry
    # if isinstance(sub, RasterMetaEntry):
    #     name = 'raster-entry-detail'
    # elif isinstance(sub, GeometryEntry):
    #     name = 'geometry-entry-detail'
    # elif isinstance(sub, FMVEntry):
    #     name = 'fmv-entry-detail'
    # elif isinstance(sub, PointCloudMetaEntry):
    #     name = 'point-cloud-entry-detail'
    #     sub = sub.parent_point_cloud
    # elif isinstance(sub, ImageSetSpatial):
    #     name = 'image-set-spatial-detail'
    # else:
    #     raise ValueError()
    # return redirect(reverse(name, kwargs={'pk': sub.pk}))
    raise ValueError()