import json

from django.contrib.gis.db.models import Collect, Extent
from django.db.models import Max, Min
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from rgd.geodata import serializers
from rgd.geodata.filters import RasterMetaEntryFilter, SpatialEntryFilter
from rgd.geodata.models import RasterMetaEntry, SpatialEntry
from rgd.geodata.permissions import filter_read_perm


def extent_summary_spatial(found):
    """
    Given a query set of SpatialEntry, return a result dictionary with the summary.

    :param found: a query set with SpatialEntry results.
    :returns: a dictionary with count, collect, convex_hull, extent,
        acquisition, acqusition_date.  collect and convex_hull are geojson
        objects.
    """
    results = {'count': 0}
    if found and found.count():
        summary = found.aggregate(
            Collect('outline'),
            Extent('outline'),
            Min('acquisition_date'),
            Max('acquisition_date'),
        )
        results.update(
            {
                'count': found.count(),
                'collect': json.loads(summary['outline__collect'].geojson),
                'convex_hull': json.loads(summary['outline__collect'].convex_hull.geojson),
                'extent': {
                    'xmin': summary['outline__extent'][0],
                    'ymin': summary['outline__extent'][1],
                    'xmax': summary['outline__extent'][2],
                    'ymax': summary['outline__extent'][3],
                },
                'acquisition_date': [
                    summary['acquisition_date__min'].isoformat()
                    if summary['acquisition_date__min'] is not None
                    else None,
                    summary['acquisition_date__max'].isoformat()
                    if summary['acquisition_date__max'] is not None
                    else None,
                ],
            }
        )
    return results


def extent_summary_modifiable(found, has_created=False):
    """
    Given a query set of ModifiableEntry, return a result dictionary with the summary.

    :param found: a query set with SpatialEntry results.
    :returns: a dictionary with count, collect, convex_hull, extent,
        acquisition, acqusition_date, created, modified.  collect and
        convex_hull are geojson objects.
    """
    if found and found.count():
        results = {
            'count': found.count(),
        }
        if has_created:
            summary = found.aggregate(
                Min('created'),
                Max('created'),
                Min('modified'),
                Max('modified'),
            )
            results.update(
                {
                    'created': [
                        summary['created__min'].isoformat(),
                        summary['created__max'].isoformat(),
                    ],
                    'modified': [
                        summary['modified__min'].isoformat(),
                        summary['modified__max'].isoformat(),
                    ],
                }
            )
    else:
        results = {'count': 0}
    return results


def extent_summary(found, has_created=False):
    results = extent_summary_modifiable(found, has_created)
    results.update(extent_summary_spatial(found))
    if found and found.count():
        if has_created:
            summary = found.aggregate(
                acquisition__min=Min(Coalesce('acquisition_date', 'created')),
                acquisition__max=Max(Coalesce('acquisition_date', 'created')),
            )
        else:
            summary = found.aggregate(
                acquisition__min=Min('acquisition_date'),
                acquisition__max=Max('acquisition_date'),
            )
        if summary['acquisition__min'] is not None:
            results['acquisition'] = [
                summary['acquisition__min'].isoformat(),
                summary['acquisition__max'].isoformat(),
            ]
    return results


def extent_summary_fmv(found):
    results = extent_summary(found)
    if found and found.count():
        summary = found.aggregate(
            Collect('ground_union'),
            Extent('ground_union'),
        )
        results.update(
            {
                'count': found.count(),
                'collect': json.loads(summary['ground_union__collect'].geojson),
                'convex_hull': json.loads(summary['ground_union__collect'].convex_hull.geojson),
                'extent': {
                    'xmin': summary['ground_union__extent'][0],
                    'ymin': summary['ground_union__extent'][1],
                    'xmax': summary['ground_union__extent'][2],
                    'ymax': summary['ground_union__extent'][3],
                },
            }
        )
    return results


def extent_summary_http(found, has_created=False):
    """
    Given a query set of items, return an http response with the summary.

    :param found: a query set with SpatialEntry results.
    :returns: a DRF Response.
    """
    results = extent_summary(found, has_created)
    return Response(results)


class SearchSpatialEntryView(ListAPIView):
    queryset = SpatialEntry.objects.all()
    serializer_class = serializers.SpatialEntrySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = SpatialEntryFilter

    def get_queryset(self):
        return filter_read_perm(self.request.user, super().get_queryset())


class SearchRasterMetaEntrySTACView(ListAPIView):
    queryset = RasterMetaEntry.objects.all()
    serializer_class = serializers.STACRasterSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RasterMetaEntryFilter

    def get_queryset(self):
        return filter_read_perm(self.request.user, super().get_queryset())
