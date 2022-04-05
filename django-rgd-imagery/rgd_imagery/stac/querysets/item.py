import json

from dateutil import parser as datetimeparse
from django.contrib.gis.db.models.functions import AsGeoJSON
from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.contrib.postgres.aggregates import JSONBAgg
from django.db.models import DateTimeField, F, Q, TextField, Value
from django.db.models.functions import Cast, Coalesce, JSONObject, NullIf
from rgd.models import SpatialEntry
from rgd.permissions import filter_read_perm


def strnorm(field_name):
    """Make a string NULL if blank."""
    return NullIf(Cast(field_name, TextField()), Value('', TextField()))


def datenorm(field_name):
    """Normalize datetimes."""
    return Cast(field_name, DateTimeField())


def intstr(field_name):
    """Cast int to string."""
    return Cast(field_name, TextField())


def get_queryset(
    user=None,
    pk=None,
    bbox=None,
    intersects=None,
    ids=None,
    collection=None,
    collections=None,
    datetime=None,
):
    queryset = SpatialEntry.objects.all()
    if user is not None:
        queryset = filter_read_perm(user, queryset)
    if pk is not None:
        queryset = queryset.filter(pk=pk)
    if bbox is not None:
        queryset = queryset.filter(
            footprint__intersects=Polygon.from_bbox([float(v) for v in bbox.split(',')])
        )
    if intersects is not None:
        queryset = queryset.filter(footprint__intersects=GEOSGeometry(json.loads(intersects)))
    if ids is not None:
        queryset = queryset.filter(pk__in=[int(v) for v in bbox.split(',')])
    if collection is not None:
        if collection == 'default':
            collection = None
        queryset = queryset.filter(
            Q(rastermeta__parent_raster__image_set__images__file__collection_id=collection)
            | Q(imagesetspatial__image_set__images__file__collection_id=collection)
        )
    if collections is not None:
        condition = Q()
        for collection in collections.split(','):
            if collection == 'default':
                collection = None
            condition |= Q(
                rastermeta__parent_raster__image_set__images__file__collection_id=collection
            )
            condition |= Q(imagesetspatial__image_set__images__file__collection_id=collection)
        queryset = queryset.filter(condition)
    if datetime is not None:
        split_datetime = datetime.split('/')
        if len(split_datetime) == 1:
            datetime_obj = datetimeparse(split_datetime[0])
            return queryset.filter(acquisition_date=datetime_obj)
        else:
            start = split_datetime[0]
            end = split_datetime[1]
            if start != '..':
                datetime_obj = datetimeparse(start)
                queryset = queryset.filter(
                    Q(acquisition_date__gte=datetime_obj)
                    | Q(imagesetspatial__created__gte=datetime_obj)
                    | Q(rastermeta__created__gte=datetime_obj)
                )
            if end != '..':
                datetime_obj = datetimeparse(end)
                queryset = queryset.filter(
                    Q(acquisition_date__lte=datetime_obj)
                    | Q(imagesetspatial__created__lte=datetime_obj)
                    | Q(rastermeta__created__lte=datetime_obj)
                )
    queryset = queryset.values(
        stac_id=intstr('pk'),
        description=Coalesce(
            strnorm('rastermeta__parent_raster__description'),
            strnorm('rastermeta__parent_raster__image_set__description'),
            strnorm('imagesetspatial__image_set__description'),
        ),
        title=Coalesce(
            strnorm('rastermeta__parent_raster__name'),
            strnorm('rastermeta__parent_raster__image_set__name'),
            strnorm('imagesetspatial__image_set__name'),
        ),
        collection_id=Coalesce(
            intstr('rastermeta__parent_raster__image_set__images__file__collection_id'),
            intstr('imagesetspatial__image_set__images__file__collection_id'),
            Value('default', TextField()),
        ),
        datetimes=JSONObject(
            datetime=Coalesce(
                datenorm('acquisition_date'),
                datenorm('rastermeta__created'),
                datenorm('imagesetspatial__created'),
            ),
            createdtime=Coalesce(
                datenorm('rastermeta__created'),
                datenorm('imagesetspatial__created'),
            ),
            updatedtime=Coalesce(
                datenorm('rastermeta__modified'),
                datenorm('imagesetspatial__modified'),
            ),
        ),
        geojson=AsGeoJSON('footprint', bbox=True),
        eo_cloud_cover=F('rastermeta__cloud_cover'),
        eo_asset_bandinfo=JSONBAgg(
            JSONObject(
                file_id=Coalesce(
                    intstr('rastermeta__parent_raster__image_set__images__file__pk'),
                    intstr('imagesetspatial__image_set__images__file__pk'),
                ),
                common_name=Coalesce(
                    'rastermeta__parent_raster__image_set__images__bandmeta__interpretation',
                    'imagesetspatial__image_set__images__bandmeta__interpretation',
                ),
                description=Coalesce(
                    'rastermeta__parent_raster__image_set__images__bandmeta__description',
                    'imagesetspatial__image_set__images__bandmeta__description',
                ),
                band_number=Coalesce(
                    'rastermeta__parent_raster__image_set__images__bandmeta__band_number',
                    'imagesetspatial__image_set__images__bandmeta__band_number',
                ),
                band_range_lower=Coalesce(
                    'rastermeta__parent_raster__image_set__images__bandmeta__band_range__startswith',
                    'imagesetspatial__image_set__images__bandmeta__band_range__startswith',
                ),
                band_range_upper=Coalesce(
                    'rastermeta__parent_raster__image_set__images__bandmeta__band_range__endswith',
                    'imagesetspatial__image_set__images__bandmeta__band_range__endswith',
                ),
            ),
            distinct=True,
            filter=(
                Q(rastermeta__parent_raster__image_set__images__bandmeta__isnull=False)
                | Q(imagesetspatial__image_set__images__bandmeta__isnull=False)
            ),
        ),
        ancillary_files=JSONBAgg(
            JSONObject(
                id=intstr('rastermeta__parent_raster__ancillary_files__pk'),
                title=strnorm('rastermeta__parent_raster__ancillary_files__name'),
                filename=strnorm('rastermeta__parent_raster__ancillary_files__file'),
                url=strnorm('rastermeta__parent_raster__ancillary_files__url'),
                created=Cast(
                    'rastermeta__parent_raster__ancillary_files__created', DateTimeField()
                ),
                modified=Cast(
                    'rastermeta__parent_raster__ancillary_files__modified', DateTimeField()
                ),
            ),
            distinct=True,
            filter=Q(rastermeta__parent_raster__ancillary_files__isnull=False),
        ),
        sidecar_files=JSONBAgg(
            JSONObject(
                id=Coalesce(
                    intstr(
                        'rastermeta__parent_raster__image_set__images__file__file_set__checksumfile__pk'
                    ),
                    intstr('imagesetspatial__image_set__images__file__file_set__checksumfile__pk'),
                ),
                title=Coalesce(
                    strnorm(
                        'rastermeta__parent_raster__image_set__images__file__file_set__checksumfile__name'
                    ),
                    strnorm(
                        'imagesetspatial__image_set__images__file__file_set__checksumfile__name'
                    ),
                ),
                filename=Coalesce(
                    strnorm(
                        'rastermeta__parent_raster__image_set__images__file__file_set__checksumfile__file'
                    ),
                    strnorm(
                        'imagesetspatial__image_set__images__file__file_set__checksumfile__file'
                    ),
                ),
                url=Coalesce(
                    strnorm(
                        'rastermeta__parent_raster__image_set__images__file__file_set__checksumfile__url'
                    ),
                    strnorm(
                        'imagesetspatial__image_set__images__file__file_set__checksumfile__url'
                    ),
                ),
                created=Coalesce(
                    datenorm(
                        'rastermeta__parent_raster__image_set__images__file__file_set__checksumfile__created'
                    ),
                    datenorm(
                        'imagesetspatial__image_set__images__file__file_set__checksumfile__created'
                    ),
                ),
                modified=Coalesce(
                    datenorm(
                        'rastermeta__parent_raster__image_set__images__file__file_set__checksumfile__modified'
                    ),
                    datenorm(
                        'imagesetspatial__image_set__images__file__file_set__checksumfile__modified'
                    ),
                ),
            ),
            filter=(
                Q(
                    rastermeta__parent_raster__image_set__images__file__file_set__checksumfile__isnull=False
                )
                | Q(imagesetspatial__image_set__images__file__file_set__checksumfile__isnull=False)
            ),
            distinct=True,
        ),
        image_files=JSONBAgg(
            JSONObject(
                id=Coalesce(
                    intstr('rastermeta__parent_raster__image_set__images__file__pk'),
                    intstr('imagesetspatial__image_set__images__file__pk'),
                ),
                title=Coalesce(
                    strnorm('rastermeta__parent_raster__image_set__images__file__name'),
                    strnorm('imagesetspatial__image_set__images__file__name'),
                ),
                filename=Coalesce(
                    strnorm('rastermeta__parent_raster__image_set__images__file__file'),
                    strnorm('imagesetspatial__image_set__images__file__file'),
                ),
                url=Coalesce(
                    strnorm('rastermeta__parent_raster__image_set__images__file__url'),
                    strnorm('imagesetspatial__image_set__images__file__url'),
                ),
                created=Coalesce(
                    datenorm('rastermeta__parent_raster__image_set__images__file__created'),
                    datenorm('imagesetspatial__image_set__images__file__created'),
                ),
                modified=Coalesce(
                    datenorm('rastermeta__parent_raster__image_set__images__file__modified'),
                    datenorm('imagesetspatial__image_set__images__file__modified'),
                ),
            ),
            filter=(
                Q(rastermeta__parent_raster__image_set__images__file__isnull=False)
                | Q(imagesetspatial__image_set__images__file__isnull=False)
            ),
            distinct=True,
        ),
        derivationinfo=JSONBAgg(
            JSONObject(
                id=Coalesce(
                    intstr(
                        'rastermeta__parent_raster__image_set__images__sourceprocessimage_set__group__pk'
                    ),
                    intstr('imagesetspatial__image_set__images__sourceprocessimage_set__group__pk'),
                ),
                type=Coalesce(
                    strnorm(
                        'rastermeta__parent_raster__image_set__images__sourceprocessimage_set__group__process_type'
                    ),
                    strnorm(
                        'imagesetspatial__image_set__images__sourceprocessimage_set__group__process_type'
                    ),
                ),
                source_file_id=Coalesce(
                    intstr(
                        'rastermeta__parent_raster__image_set__images__sourceprocessimage_set__source_images__file__pk'
                    ),
                    intstr(
                        'imagesetspatial__image_set__images__sourceprocessimage_set__source_images__file__pk'
                    ),
                ),
                output_file_id=Coalesce(
                    intstr(
                        'rastermeta__parent_raster__image_set__images__sourceprocessimage_set__processed_image__pk'
                    ),
                    intstr(
                        'imagesetspatial__image_set__images__sourceprocessimage_set__processed_image__pk'
                    ),
                ),
                source_item_id=Coalesce(
                    intstr(
                        'rastermeta__parent_raster__image_set__images__sourceprocessimage_set__source_images__imageset__raster__rastermeta__pk',
                    ),
                    intstr(
                        'rastermeta__parent_raster__image_set__images__sourceprocessimage_set__source_images__imageset__imagesetspatial__pk',
                    ),
                    intstr(
                        'imagesetspatial__image_set__images__sourceprocessimage_set__source_images__imageset__raster__rastermeta__pk',
                    ),
                    intstr(
                        'imagesetspatial__image_set__images__sourceprocessimage_set__source_images__imageset__imagesetspatial__pk',
                    ),
                ),
                source_collection_id=Coalesce(
                    intstr(
                        'rastermeta__parent_raster__image_set__images__sourceprocessimage_set__source_images__file__collection__pk'
                    ),
                    intstr(
                        'imagesetspatial__image_set__images__sourceprocessimage_set__source_images__file__collection__pk'
                    ),
                ),
            ),
            distinct=True,
            filter=(
                Q(
                    rastermeta__parent_raster__image_set__images__sourceprocessimage_set__isnull=False
                )
                | Q(imagesetspatial__image_set__images__sourceprocessimage_set__isnull=False)
            ),
        ),
    )

    return queryset
