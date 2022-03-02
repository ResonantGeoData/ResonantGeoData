from rest_framework.reverse import reverse as drf_reverse

from ..constants import CONFORMANCE


def get_conformance(request):
    def reverse(viewname, **kwargs):
        return drf_reverse(viewname, request=request, **kwargs)

    return {
        'conformsTo': CONFORMANCE,
        'links': [
            {
                'rel': 'root',
                'type': 'application/json',
                'href': reverse('stac-root'),
            },
            {
                'rel': 'self',
                'type': 'application/json',
                'href': reverse('stac-conformance'),
            },
        ],
    }
