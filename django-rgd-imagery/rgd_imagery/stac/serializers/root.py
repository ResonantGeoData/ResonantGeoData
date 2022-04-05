from rest_framework.reverse import reverse as drf_reverse

from ..constants import CONFORMANCE


# https://github.com/radiantearth/stac-api-spec/tree/master/core
def get_root(collections, request):
    def reverse(viewname, **kwargs):
        return drf_reverse(viewname, request=request, **kwargs)

    return {
        'type': 'Catalog',
        'stac_version': '1.0.0',
        'id': 'rgd',
        'title': 'Resonant GeoData STAC API',
        'description': 'All collections visible to the viewer',
        'conformsTo': CONFORMANCE,
        'links': [
            {
                'rel': 'self',
                'type': 'application/json',
                'href': reverse('stac-root'),
            },
            {
                'rel': 'root',
                'type': 'application/json',
                'href': reverse('stac-root'),
            },
            {
                'rel': 'search',
                'type': 'application/json',
                'href': reverse('stac-search'),
            },
            {
                'rel': 'service-desc',
                'type': 'application/vnd.oai.openapi+json;version=3.1',
                'href': reverse('stac-service-desc'),
            },
            {
                'rel': 'service-doc',
                'type': 'text/html',
                'href': reverse('stac-service-doc'),
            },
            {
                'rel': 'conformance',
                'type': 'application/json',
                'href': reverse('stac-conformance'),
            },
            {
                'rel': 'data',
                'type': 'application/json',
                'href': reverse('stac-collections'),
            },
        ]
        + [
            {
                'rel': 'child',
                'type': 'application/json',
                'title': collection['name'] or '',
                'href': reverse('stac-collection', args=[f'{collection["id"]}']),
            }
            for collection in collections
        ],
    }
