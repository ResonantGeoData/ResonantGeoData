from typing import Iterable

from rest_framework import serializers
from rest_framework.reverse import reverse
from rgd.models import Collection


class STACRootSerializer(serializers.BaseSerializer):
    def to_representation(self, collections: Iterable[Collection]) -> dict:
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
                    'href': reverse('stac-root', request=self.context.get('request')),
                },
                {
                    'rel': 'root',
                    'type': 'application/json',
                    'href': reverse('stac-root', request=self.context.get('request')),
                },
                {
                    'rel': 'search',
                    'type': 'application/json',
                    'href': reverse('stac-search', request=self.context.get('request')),
                },
                {
                    'rel': 'child',
                    'type': 'application/json',
                    'title': 'default',
                    'href': reverse(
                        'stac-collection-default',
                        request=self.context.get('request'),
                    ),
                },
            ]
            + [
                {
                    'rel': 'child',
                    'type': 'application/json',
                    'title': collection.name,
                    'href': reverse(
                        'stac-collection',
                        args=[collection.pk],
                        request=self.context.get('request'),
                    ),
                }
                for collection in collections
            ],
        }
