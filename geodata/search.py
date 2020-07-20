import datetime
import json

import dateutil.parser
from django.contrib.gis.db.models import Collect, Extent
from django.contrib.gis.geos import Point
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Max, Min, Q
from django.db.models.functions import Coalesce
from django.http import HttpResponse, JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers as rfserializers
from rest_framework.decorators import api_view

from . import serializers
from .models import GeometryEntry, RasterEntry, SpatialEntry


class NearPointSerializer(rfserializers.Serializer):
    longitude = rfserializers.FloatField(required=False)
    latitude = rfserializers.FloatField(
        required=False, validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    radius = rfserializers.FloatField(
        required=False, default=0, validators=[MinValueValidator(0)], help_text='Radius in meters'
    )
    # altitude = rfserializers.FloatField(
    #     allow_null=True, required=False, help_text='Altitude in meters'
    # )
    time = rfserializers.DateTimeField(allow_null=True, required=False)
    timespan = rfserializers.FloatField(
        required=False,
        default=86400,
        validators=[MinValueValidator(0)],
        help_text='Span in seconds on either size of the specified time',
    )
    timefield = rfserializers.CharField(
        required=False,
        default='acquisition',
        help_text='A comma-separated list of fields to search.  This can include acquisition, created, modified.',
    )


def search_near_point_filter(params):
    """
    Get a filter object that can be used when searching SpatialEntry models.

    :param params: a dictionary of parameters, optionally including
        latitude, longitude, radius, time, timespan, and timefield.
    :returns: a Django query (Q) object.
    """
    query = Q()
    if params.get('latitude') is not None and params.get('longitude') is not None:
        geom = Point(float(params['longitude']), float(params['latitude']))
        query.add(Q(footprint__distance_lte=(geom, float(params['radius']))), Q.AND)
    if params.get('time') is not None:
        qtime = dateutil.parser.isoparser().isoparse(params['time'])
        timespan = datetime.timedelta(0, float(params['timespan']))
        starttime = qtime - timespan
        endtime = qtime + timespan
        timefields = [field.strip() for field in params.get('timefield', '').split(',')] or [
            'acquisition'
        ]
        subquery = []
        for field in timefields:
            field_name = {
                'acquisition': 'acquisition_date',
                'created': 'created',
                'modified': 'modified',
            }.get(field)
            if not field_name:
                raise Exception('Unrecognized time field %s' % field)
            subquery.append(
                Q(**{'%s__gte' % field_name: starttime, '%s__lte' % field_name: endtime})
            )
            if field == 'acquisition':
                subquery.append(
                    Q(acquisition_date__isnull=True, created__gte=starttime, created__lte=endtime)
                )
        if subquery:
            for subq in subquery[1:]:
                subquery[0].add(subq, Q.OR)
            query.add(subquery[0], Q.AND)
    return query


@swagger_auto_schema(
    method='GET',
    operation_description='List geospatial datasets near a specific latitude and longitude',
    query_serializer=NearPointSerializer,
)
@api_view(['GET'])
def search_near_point(request, *args, **kwargs):
    params = request.query_params
    results = SpatialEntry.objects.filter(search_near_point_filter(params))
    return JsonResponse(serializers.SpatialEntrySerializer(results, many=True).data, safe=False)


@swagger_auto_schema(
    method='GET',
    operation_description='List geospatial raster datasets near a specific latitude and longitude',
    query_serializer=NearPointSerializer,
)
@api_view(['GET'])
def search_near_point_raster(request, *args, **kwargs):
    params = request.query_params
    results = RasterEntry.objects.filter(search_near_point_filter(params))
    return JsonResponse(serializers.RasterEntrySerializer(results, many=True).data, safe=False)


@swagger_auto_schema(
    method='GET',
    operation_description='List geospatial geometry datasets near a specific latitude and longitude',
    query_serializer=NearPointSerializer,
)
@api_view(['GET'])
def search_near_point_geometry(request, *args, **kwargs):
    params = request.query_params
    results = GeometryEntry.objects.filter(search_near_point_filter(params))
    return JsonResponse(serializers.GeometryEntrySerializer(results, many=True).data, safe=False)


def extant_summary(found):
    """
    Given a query set of items, return an http response with the summary.

    :param found: a query set with SpatialEntry results.
    :returns: an HttpResponse.
    """
    summary = found.aggregate(
        Collect('footprint'),
        Extent('footprint'),
        Min('acquisition_date'),
        Max('acquisition_date'),
        Min('created'),
        Max('created'),
        Min('modified'),
        Max('modified'),
        acquisition__min=Min(Coalesce('acquisition_date', 'created')),
        acquisition__max=Max(Coalesce('acquisition_date', 'created')),
    )
    if found.count():
        results = {
            'count': found.count(),
            'collect': json.loads(summary['footprint__collect'].geojson),
            'convex_hull': json.loads(summary['footprint__collect'].convex_hull.geojson),
            'extent': {
                'xmin': summary['footprint__extent'][0],
                'ymin': summary['footprint__extent'][1],
                'xmax': summary['footprint__extent'][2],
                'ymax': summary['footprint__extent'][3],
            },
            'acquisition': [
                summary['acquisition__min'].isoformat(),
                summary['acquisition__max'].isoformat(),
            ],
            'acquisition_date': [
                summary['acquisition_date__min'].isoformat()
                if summary['acquisition_date__min'] is not None
                else None,
                summary['acquisition_date__max'].isoformat()
                if summary['acquisition_date__max'] is not None
                else None,
            ],
            'created': [summary['created__min'].isoformat(), summary['created__max'].isoformat()],
            'modified': [
                summary['modified__min'].isoformat(),
                summary['modified__max'].isoformat(),
            ],
        }
    else:
        results = {'count': 0}
    return HttpResponse(json.dumps(results), content_type='application/json')


@swagger_auto_schema(
    method='GET',
    operation_description='Get the convex hull and time range for geospatial datasets near a specific latitude and longitude',
    query_serializer=NearPointSerializer,
)
@api_view(['GET'])
def search_near_point_extent(request, *args, **kwargs):
    params = request.query_params
    found = SpatialEntry.objects.filter(search_near_point_filter(params))
    return extant_summary(found)


@swagger_auto_schema(
    method='GET',
    operation_description='Get the convex hull and time range for geospatial raster datasets near a specific latitude and longitude',
    query_serializer=NearPointSerializer,
)
@api_view(['GET'])
def search_near_point_extent_raster(request, *args, **kwargs):
    params = request.query_params
    found = RasterEntry.objects.filter(search_near_point_filter(params))
    return extant_summary(found)


@swagger_auto_schema(
    method='GET',
    operation_description='Get the convex hull and time range for geospatial geometry datasets near a specific latitude and longitude',
    query_serializer=NearPointSerializer,
)
@api_view(['GET'])
def search_near_point_extent_geometry(request, *args, **kwargs):
    params = request.query_params
    found = GeometryEntry.objects.filter(search_near_point_filter(params))
    return extant_summary(found)
