from django.contrib.gis.db.models import Extent
from rest_framework import serializers
from rest_framework.reverse import reverse as drf_reverse
from rgd.models import Collection
from rgd.permissions import filter_read_perm
from rgd_imagery.models import RasterMeta


# https://github.com/radiantearth/stac-api-spec/tree/master/ogcapi-features#example-collection-for-stac-api---features
class CollectionSerializer(serializers.BaseSerializer):
    def to_representation(self, collection: Collection) -> dict:
        request = self.context.get('request')

        def reverse(viewname, **kwargs):
            return drf_reverse(viewname, request=request, **kwargs)

        user = request and request.user or None
        collection_id = str(collection.pk) if collection.pk else 'default'
        collection_title = str(collection.name) if collection.pk else 'default'
        items = filter_read_perm(
            user,
            RasterMeta.objects.filter(
                parent_raster__image_set__images__file__collection=collection.pk
            ),
        )
        return {
            'type': 'Collection',
            'stac_version': '1.0.0',
            'description': f'STAC Collection {collection_title}',
            'conformsTo': ['https://api.stacspec.org/v1.0.0-beta.3/core'],
            'id': collection.pk,
            'title': collection_title,
            'extent': {
                'spatial': {
                    'bbox': [
                        list(items.aggregate(Extent('footprint'))['footprint__extent'])
                        if items
                        else []
                    ]
                },
                'temporal': {'interval': [[None, None]]},
            },
            'license': 'proprietary',
            'links': [
                {
                    'rel': 'items',
                    'type': 'application/json',
                    'href': reverse('stac-collection-items', args=[collection_id]),
                },
                {
                    'rel': 'root',
                    'type': 'application/json',
                    'href': reverse('stac-core'),
                },
                {
                    'rel': 'parent',
                    'type': 'application/json',
                    'href': reverse('stac-core'),
                },
                {
                    'rel': 'self',
                    'type': 'application/json',
                    'href': reverse('stac-collection', args=[collection_id]),
                },
            ],
        }
