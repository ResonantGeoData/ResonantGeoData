from django.contrib.gis.db.models import Extent
from django.db.models import DateTimeField, Max, Min, Q, TextField, Value
from django.db.models.functions import Cast, Coalesce, JSONObject
from rgd.models import SpatialEntry
from rgd.permissions import filter_read_perm


def get_queryset(user=None, pk=None):
    queryset = SpatialEntry.objects.all()
    if user is not None:
        queryset = filter_read_perm(user, queryset)
    if pk is not None:
        if pk == 'default':
            pk = None
        queryset = queryset.filter(
            Q(rastermeta__parent_raster__image_set__images__file__collection_id=pk)
            | Q(imagesetspatial__image_set__images__file__collection_id=pk)
        )
    queryset = (
        queryset.values(
            group_key=Coalesce(
                'rastermeta__parent_raster__image_set__images__file__collection_id',
                'imagesetspatial__image_set__images__file__collection_id',
            )
        )
        .annotate(
            datetimes=JSONObject(
                min_acquisition_date=Min(
                    Coalesce(
                        'acquisition_date',
                        'rastermeta__created',
                        'imagesetspatial__created',
                        output_field=DateTimeField(),
                    )
                ),
                max_acquisition_date=Max(
                    Coalesce(
                        'acquisition_date',
                        'rastermeta__created',
                        'imagesetspatial__created',
                        output_field=DateTimeField(),
                    )
                ),
            ),
            bbox=Extent('footprint'),
        )
        .values(
            'datetimes',
            'bbox',
            stac_id=Coalesce(
                Cast(
                    'rastermeta__parent_raster__image_set__images__file__collection_id',
                    TextField(),
                ),
                Cast(
                    'imagesetspatial__image_set__images__file__collection_id',
                    TextField(),
                ),
                Value('default', TextField()),
            ),
            stac_title=Coalesce(
                Cast(
                    'rastermeta__parent_raster__image_set__images__file__collection__name',
                    TextField(),
                ),
                Cast(
                    'imagesetspatial__image_set__images__file__collection__name',
                    TextField(),
                ),
                Value('default', TextField()),
            ),
            stac_description=Coalesce(
                'rastermeta__parent_raster__image_set__images__file__collection__description',
                'imagesetspatial__image_set__images__file__collection__description',
                Value('default', TextField()),
            ),
        )
    )

    return queryset
