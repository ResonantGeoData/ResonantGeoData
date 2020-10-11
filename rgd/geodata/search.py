import datetime
import json

import dateutil.parser
from django.contrib.gis.db.models import Collect, Extent
from django.contrib.gis.geos import Point, Polygon
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Max, Min, Q
from django.db.models.functions import Coalesce
from django.http import HttpResponse, JsonResponse
from django.utils.timezone import make_aware
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


class BoundingBoxSerializer(rfserializers.Serializer):
    minimum_longitude = rfserializers.FloatField(required=False)
    minimum_latitude = rfserializers.FloatField(
        required=False, validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    maximum_longitude = rfserializers.FloatField(required=False)
    maximum_latitude = rfserializers.FloatField(
        required=False, validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    # minimum_altitude = rfserializers.FloatField(
    #     allow_null=True, required=False, help_text='Altitude in meters'
    # )
    # maximum_altitude = rfserializers.FloatField(
    #     allow_null=True, required=False, help_text='Altitude in meters'
    # )
    start_time = rfserializers.DateTimeField(allow_null=True, required=False)
    end_time = rfserializers.DateTimeField(allow_null=True, required=False)
    timefield = rfserializers.CharField(
        required=False,
        default='acquisition',
        help_text='A comma-separated list of fields to search.  This can include acquisition, created, modified.',
    )


class GeoJsonSerializer(rfserializers.Serializer):
    geojson = rfserializers.CharField(
        required=False,
        help_text='A URL-encoded text of a GeoJSON Geometry object describing a geometry to search.'
    )
    within = rfserializers.BooleanField(
        default=False,
        allow_null=True,
        help_text='Return data entirely within (rather than intersecting) the provided geometry.'
    )
    start_time = rfserializers.DateTimeField(allow_null=True, required=False)
    end_time = rfserializers.DateTimeField(allow_null=True, required=False)
    timefield = rfserializers.CharField(
        required=False,
        default='acquisition',
        help_text='A comma-separated list of fields to search.  This can include acquisition, created, modified.',
    )


def _add_time_to_query(query, timefield, starttime, endtime, has_created=False):
    starttime = make_aware(starttime)
    endtime = make_aware(endtime)
    timefields = [field.strip() for field in timefield.split(',')] or ['acquisition']
    subquery = []
    for field in timefields:
        field_name = {
            'acquisition': 'acquisition_date',
            'created': 'created',
            'modified': 'modified',
        }.get(field)
        if not field_name:
            raise Exception('Unrecognized time field %s' % field)
        subquery.append(Q(**{'%s__gte' % field_name: starttime, '%s__lte' % field_name: endtime}))
        if field == 'acquisition' and has_created:
            subquery.append(
                Q(acquisition_date__isnull=True, created__gte=starttime, created__lte=endtime)
            )
    if subquery:
        for subq in subquery[1:]:
            subquery[0].add(subq, Q.OR)
        query.add(subquery[0], Q.AND)


def search_near_point_filter(params, has_created=False):
    """
    Get a filter object that can be used when searching SpatialEntry models.

    :param params: a dictionary of parameters, optionally including
        latitude, longitude, radius, time, timespan, and timefield.
    :param has_created: if True, searching acquisition time will fallback to
        include created times.
    :returns: a Django query (Q) object.
    """
    query = Q()
    if params.get('latitude') is not None and params.get('longitude') is not None:
        geom = Point(float(params['longitude']), float(params['latitude']))
        query.add(Q(footprint__distance_lte=(geom, float(params.get('radius', 0)))), Q.AND)
    if params.get('time') is not None:
        qtime = dateutil.parser.isoparser().isoparse(params['time'])
        timespan = datetime.timedelta(0, float(params['timespan']))
        starttime = qtime - timespan
        endtime = qtime + timespan
        _add_time_to_query(query, params.get('timefield', ''), starttime, endtime, has_created)
    return query


def search_bounding_box_filter(params, has_created=False):
    """
    Get a filter object that can be used when searching SpatialEntry models.

    :param params: a dictionary of parameters, optionally including
        minimum_latitude, minimum_longitude, maximum_latitude,
        maximum_longitude, start_time, end_time, and timefield.
    :param has_created: if True, searching acquisition time will fallback to
        include created times.
    :returns: a Django query (Q) object.
    """
    query = Q()
    if all(
        params.get(key) is not None
        for key in {
            'minimum_longitude',
            'minimum_latitude',
            'maximum_longitude',
            'maximum_latitude',
        }
    ):
        geom = Polygon(
            (
                (float(params['minimum_longitude']), float(params['minimum_latitude'])),
                (float(params['maximum_longitude']), float(params['minimum_latitude'])),
                (float(params['maximum_longitude']), float(params['maximum_latitude'])),
                (float(params['minimum_longitude']), float(params['maximum_latitude'])),
                (float(params['minimum_longitude']), float(params['minimum_latitude'])),
            )
        )
        query.add(Q(footprint__intersects=(geom)), Q.AND)
    if params.get('start_time') is not None or params.get('end_time') is not None:
        if params.get('start_time') is not None:
            starttime = dateutil.parser.isoparser().isoparse(params['start_time'])
        if params.get('end_time') is not None:
            endtime = dateutil.parser.isoparser().isoparse(params['end_time'])
        else:
            endtime = starttime
        if params.get('start_time') is None:
            starttime = endtime
        _add_time_to_query(query, params.get('timefield', ''), starttime, endtime, has_created)
    return query


def search_geojson_filter(params, has_created=False):
    """
    Get a filter object that can be used when searching SpatialEntry models.

    :param params: a dictionary of parameters, optionally including
        geojson, within, start_time, end_time, and timefield.
    :param has_created: if True, searching acquisition time will fallback to
        include created times.
    :raises ValueError: The GeoJSON is invalid.
    :returns: a Django query (Q) object.
    """
    pass


@swagger_auto_schema(
    method='GET',
    operation_summary='List geospatial datasets near a point',
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
    operation_summary='List raster datasets near a point',
    operation_description='List geospatial raster datasets near a specific latitude and longitude',
    query_serializer=NearPointSerializer,
)
@api_view(['GET'])
def search_near_point_raster(request, *args, **kwargs):
    params = request.query_params
    results = RasterEntry.objects.filter(search_near_point_filter(params, True))
    return JsonResponse(serializers.RasterEntrySerializer(results, many=True).data, safe=False)


@swagger_auto_schema(
    method='GET',
    operation_summary='List geometry datasets near a point',
    operation_description='List geospatial geometry datasets near a specific latitude and longitude',
    query_serializer=NearPointSerializer,
)
@api_view(['GET'])
def search_near_point_geometry(request, *args, **kwargs):
    params = request.query_params
    results = GeometryEntry.objects.filter(search_near_point_filter(params))
    return JsonResponse(serializers.GeometryEntrySerializer(results, many=True).data, safe=False)


@swagger_auto_schema(
    method='GET',
    operation_summary='List geospatial datasets in a bounding box',
    operation_description='List geospatial datasets that intersect a bounding box in latitude and longitude',
    query_serializer=BoundingBoxSerializer,
)
@api_view(['GET'])
def search_bounding_box(request, *args, **kwargs):
    params = request.query_params
    results = SpatialEntry.objects.filter(search_bounding_box_filter(params))
    return JsonResponse(serializers.SpatialEntrySerializer(results, many=True).data, safe=False)


@swagger_auto_schema(
    method='GET',
    operation_summary='List raster datasets in a bounding box',
    operation_description='List geospatial raster datasets that intersect a bounding box in latitude and longitude',
    query_serializer=BoundingBoxSerializer,
)
@api_view(['GET'])
def search_bounding_box_raster(request, *args, **kwargs):
    params = request.query_params
    results = RasterEntry.objects.filter(search_bounding_box_filter(params, True))
    return JsonResponse(serializers.RasterEntrySerializer(results, many=True).data, safe=False)


@swagger_auto_schema(
    method='GET',
    operation_summary='List geometry datasets in a bounding box',
    operation_description='List geospatial geometry datasets that intersect a bounding box in latitude and longitude',
    query_serializer=BoundingBoxSerializer,
)
@api_view(['GET'])
def search_bounding_box_geometry(request, *args, **kwargs):
    params = request.query_params
    results = GeometryEntry.objects.filter(search_bounding_box_filter(params))
    return JsonResponse(serializers.GeometryEntrySerializer(results, many=True).data, safe=False)


def extent_summary_spatial(found):
    """
    Given a query set of SpatialEntry, return a result dictionary with the summary.

    :param found: a query set with SpatialEntry results.
    :returns: a dictionary with count, collect, convex_hull, extent,
        acquisition, acqusition_date.  collect and convex_hull are geojson
        objects.
    """
    if found and found.count():
        summary = found.aggregate(
            Collect('footprint'),
            Extent('footprint'),
            Min('acquisition_date'),
            Max('acquisition_date'),
        )
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
            'acquisition_date': [
                summary['acquisition_date__min'].isoformat()
                if summary['acquisition_date__min'] is not None
                else None,
                summary['acquisition_date__max'].isoformat()
                if summary['acquisition_date__max'] is not None
                else None,
            ],
        }
    else:
        results = {'count': 0}
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
    :returns: an HttpResponse.
    """
    results = extent_summary(found, has_created)
    return HttpResponse(json.dumps(results), content_type='application/json')


@swagger_auto_schema(
    method='GET',
    operation_summary='Extents of geospatial datasets near a point',
    operation_description='Get the convex hull and time range for geospatial datasets near a specific latitude and longitude',
    query_serializer=NearPointSerializer,
)
@api_view(['GET'])
def search_near_point_extent(request, *args, **kwargs):
    params = request.query_params
    found = SpatialEntry.objects.filter(search_near_point_filter(params))
    return extent_summary_http(found)


@swagger_auto_schema(
    method='GET',
    operation_summary='Extents of raster datasets near a point',
    operation_description='Get the convex hull and time range for geospatial raster datasets near a specific latitude and longitude',
    query_serializer=NearPointSerializer,
)
@api_view(['GET'])
def search_near_point_extent_raster(request, *args, **kwargs):
    params = request.query_params
    found = RasterEntry.objects.filter(search_near_point_filter(params, True))
    return extent_summary_http(found, True)


@swagger_auto_schema(
    method='GET',
    operation_summary='Extents of geometry datasets near a point',
    operation_description='Get the convex hull and time range for geospatial geometry datasets near a specific latitude and longitude',
    query_serializer=NearPointSerializer,
)
@api_view(['GET'])
def search_near_point_extent_geometry(request, *args, **kwargs):
    params = request.query_params
    found = GeometryEntry.objects.filter(search_near_point_filter(params))
    return extent_summary_http(found)


@swagger_auto_schema(
    method='GET',
    operation_summary='Extents of geospatial datasets in a bounding box',
    operation_description='Get the convex hull and time range for geospatial datasets that intersect a bounding box in latitude and longitude',
    query_serializer=BoundingBoxSerializer,
)
@api_view(['GET'])
def search_bounding_box_extent(request, *args, **kwargs):
    params = request.query_params
    found = SpatialEntry.objects.filter(search_bounding_box_filter(params))
    return extent_summary_http(found)


@swagger_auto_schema(
    method='GET',
    operation_summary='Extents of raster datasets in a bounding box',
    operation_description='Get the convex hull and time range for geospatial raster datasets that intersect a bounding box in latitude and longitude',
    query_serializer=BoundingBoxSerializer,
)
@api_view(['GET'])
def search_bounding_box_extent_raster(request, *args, **kwargs):
    params = request.query_params
    found = RasterEntry.objects.filter(search_bounding_box_filter(params, True))
    return extent_summary_http(found, True)


@swagger_auto_schema(
    method='GET',
    operation_summary='Extents of geometry datasets in a bounding box',
    operation_description='Get the convex hull and time range for geospatial geometry datasets that intersect a bounding box in latitude and longitude',
    query_serializer=BoundingBoxSerializer,
)
@api_view(['GET'])
def search_bounding_box_extent_geometry(request, *args, **kwargs):
    params = request.query_params
    found = GeometryEntry.objects.filter(search_bounding_box_filter(params))
    return extent_summary_http(found)
