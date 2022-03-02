from rest_framework.reverse import reverse as drf_reverse

from . import get_collection


# https://github.com/radiantearth/stac-api-spec/tree/master/collections
def get_collections(values, request):
    def reverse(viewname, **kwargs):
        return drf_reverse(viewname, request=request, **kwargs)

    return {
        'collections': [get_collection(value, request) for value in values],
        'links': [
            {
                'rel': 'root',
                'type': 'application/json',
                'href': reverse('stac-root'),
            },
            {
                'rel': 'parent',
                'type': 'application/json',
                'href': reverse('stac-root'),
            },
            {
                'rel': 'self',
                'type': 'application/json',
                'href': reverse('stac-collections'),
            },
        ],
    }
