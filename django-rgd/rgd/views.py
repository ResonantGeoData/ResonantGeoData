import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.db.models import Collect, Extent
from django.contrib.gis.db.models.functions import AsGeoJSON, Centroid
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Count, Max, Min, Q
from django.shortcuts import redirect
from django.views import generic
from django.views.generic import DetailView, TemplateView
from rest_framework.reverse import reverse
from rgd import permissions

from . import filters, models


class PermissionTemplateView(LoginRequiredMixin, TemplateView):
    pass


class PermissionDetailView(LoginRequiredMixin, DetailView):
    def get_object(self):
        obj = super().get_object()
        permissions.check_read_perm(self.request.user, obj)
        return obj


class PermissionListView(LoginRequiredMixin, generic.ListView):
    def get_queryset(self):
        queryset = super().get_queryset()
        return permissions.filter_read_perm(self.request.user, queryset)


def query_params(params):
    query = params.copy()

    if query.get('page'):
        del query['page']

    return '&' + query.urlencode() if query.urlencode() else ''


class SpatialListView(PermissionListView):
    paginate_by = 15

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        summary = self.object_list.aggregate(
            Collect('outline'),
            Extent('outline'),
            Count('pk'),
        )
        # Have a smaller dict of meta fields to parse for menu bar
        # This keeps us from parsing long GeoJSON fields twice
        context['extents_meta'] = json.dumps({'count': summary['pk__count']})
        extents = {'count': summary['pk__count']}
        if summary['pk__count']:
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
        context['extents'] = json.dumps(extents)
        context['search_params'] = json.dumps(self.request.GET)
        context['query_params'] = query_params(self.request.GET)
        return context


class SpatialEntriesListView(SpatialListView):
    queryset = models.SpatialEntry.objects.select_subclasses()
    context_object_name = 'spatial_entries'
    template_name = 'rgd/spatialentry_list.html'
    filterset_class = filters.SpatialEntryFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        filterset = self.filterset_class(data=self.request.GET)
        if not filterset.is_valid():
            message = 'Filter parameters illformed. Full results returned.'
            all_error_messages_content = [
                msg.message
                for msg in list(messages.get_messages(self.request))
                if msg.level_tag == 'error'
            ]
            if message not in all_error_messages_content:
                messages.add_message(self.request, messages.ERROR, message)
        else:
            queryset = filterset.filter_queryset(queryset)
        return queryset


class StatisticsView(PermissionListView):
    paginate_by = None
    model = models.SpatialEntry
    context_object_name = 'spatial_entries'
    template_name = 'rgd/statistics.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            self.object_list.aggregate(
                count=Count('spatial_id', distinct=True),
                coordinates=ArrayAgg(AsGeoJSON(Centroid('footprint'))),
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


class SpatialDetailView(PermissionDetailView):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        extents = {'count': 0}
        if self.object.footprint:
            extents.update(
                {
                    'count': 1,
                    'collect': self.object.footprint.json,
                    'outline': self.object.outline.json,
                    'extent': self.object.bounds,
                }
            )
        context['extents'] = json.dumps(extents)
        return context


def spatial_entry_redirect_view(request, pk):
    # NOTE HACK: this is dirty but it works
    spat = models.SpatialEntry.objects.filter(pk=pk).select_subclasses().first()
    if hasattr(spat, 'detail_view_pk'):
        pk = spat
        for f in spat.detail_view_pk.split('__'):
            pk = getattr(pk, f)
    else:
        pk = spat.pk
    return redirect(reverse(spat.detail_view_name, kwargs={'pk': pk}))
