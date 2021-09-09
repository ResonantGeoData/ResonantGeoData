from typing import Iterable

from rest_framework import serializers
from rest_framework.reverse import reverse as drf_reverse
from rgd.models import Collection


# https://github.com/radiantearth/stac-api-spec/tree/master/core
class CoreSerializer(serializers.BaseSerializer):
    def to_representation(self, collections: Iterable[Collection]) -> dict:
        def reverse(viewname, **kwargs):
            return drf_reverse(viewname, request=self.context.get('request'), **kwargs)

        return {
            'type': 'Catalog',
            'stac_version': '1.0.0',
            'id': 'rgd-stac',
            'title': 'Resonant GeoData STAC API',
            'description': 'All collections visible to the viewer',
            'conformsTo': ['https://api.stacspec.org/v1.0.0-beta.3/core'],
            'links': [
                {
                    'rel': 'self',
                    'type': 'application/json',
                    'href': reverse('stac-core'),
                },
                {
                    'rel': 'root',
                    'type': 'application/json',
                    'href': reverse('stac-core'),
                },
                {
                    'rel': 'search',
                    'type': 'application/json',
                    'href': reverse('stac-search'),
                },
                {
                    'rel': 'child',
                    'type': 'application/json',
                    'title': 'default',
                    'href': reverse('stac-collection', args=['default']),
                },
            ]
            + [
                {
                    'rel': 'child',
                    'type': 'application/json',
                    'title': collection.name,
                    'href': reverse('stac-collection', args=[f'{collection.pk}']),
                }
                for collection in collections
            ],
        }
