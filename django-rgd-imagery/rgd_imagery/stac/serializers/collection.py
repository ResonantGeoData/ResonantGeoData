from dateutil import parser, tz
from rest_framework.reverse import reverse as drf_reverse

from ..constants import CONFORMANCE


def isotime(timestr):
    return parser.isoparse(timestr).astimezone(tz.tzutc()).strftime('%G-%m-%dT%H:%M:%S.%fZ')


# https://github.com/radiantearth/stac-api-spec/tree/master/collections
def get_collection(value, request):
    def reverse(viewname, **kwargs):
        return drf_reverse(viewname, request=request, **kwargs)

    return {
        'type': 'Collection',
        'stac_version': '1.0.0',
        'conformsTo': CONFORMANCE,
        'title': value['stac_title'] or '',
        'description': value['stac_description'] or '',
        'id': value['stac_id'],
        'extent': {
            'spatial': {'bbox': [value['bbox']]},
            'temporal': {
                'interval': [
                    [
                        isotime(value['datetimes']['min_acquisition_date']),
                        isotime(value['datetimes']['max_acquisition_date']),
                    ]
                ]
            },
        },
        'license': 'proprietary',
        'links': [
            {
                'rel': 'items',
                'type': 'application/json',
                'href': reverse('stac-collection-items', args=[value['stac_id']]),
            },
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
                'href': reverse('stac-collection', args=[value['stac_id']]),
            },
        ],
    }
