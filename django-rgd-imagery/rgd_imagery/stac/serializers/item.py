import decimal
from decimal import Decimal
import json

from bidict import bidict
from dateutil import parser, tz
from rest_framework.reverse import reverse as drf_reverse
from rgd.models import ChecksumFile


def isotime(timestr):
    return parser.isoparse(timestr).astimezone(tz.tzutc()).strftime('%G-%m-%dT%H:%M:%S.%fZ')


BAND_RANGE_BY_COMMON_NAMES = bidict(
    {
        'coastal': (Decimal(0.40), Decimal(0.45)),
        'blue': (Decimal(0.45), Decimal(0.50)),
        'green': (Decimal(0.50), Decimal(0.60)),
        'red': (Decimal(0.60), Decimal(0.70)),
        'yellow': (Decimal(0.58), Decimal(0.62)),
        'pan': (Decimal(0.50), Decimal(0.70)),
        'rededge': (Decimal(0.70), Decimal(0.79)),
        'nir': (Decimal(0.75), Decimal(1.00)),
        'nir08': (Decimal(0.75), Decimal(0.90)),
        'nir09': (Decimal(0.85), Decimal(1.05)),
        'cirrus': (Decimal(1.35), Decimal(1.40)),
        'swir16': (Decimal(1.55), Decimal(1.75)),
        'swir22': (Decimal(2.10), Decimal(2.30)),
        'lwir': (Decimal(10.5), Decimal(12.5)),
        'lwir11': (Decimal(10.5), Decimal(11.5)),
        'lwir12': (Decimal(11.5), Decimal(12.5)),
    }
)


# https://github.com/radiantearth/stac-api-spec/blob/master/stac-spec/item-spec/README.md
def get_item(value, request):
    def reverse(viewname, **kwargs):
        return drf_reverse(viewname, request=request, **kwargs)

    assets = dict()
    data = {
        'stac_version': '1.0.0',
        'stac_extensions': [
            'https://stac-extensions.github.io/eo/v1.0.0/schema.json',
        ],
        'id': value['stac_id'],
        'title': value['title'] or '',
        'description': value['description'] or '',
        'type': 'Feature',
        'properties': {
            'datetime': isotime(value['datetimes']['datetime']),
            'created': isotime(value['datetimes']['createdtime']),
            'updated': isotime(value['datetimes']['updatedtime']),
        },
        'collection': value['collection_id'],
        'links': [
            {
                'rel': 'items',
                'type': 'application/json',
                'href': reverse('stac-collection-items', args=[value['collection_id']]),
            },
            {
                'rel': 'root',
                'type': 'application/json',
                'href': reverse('stac-root'),
            },
            {
                'rel': 'parent',
                'type': 'application/json',
                'href': reverse('stac-collection', args=[value['collection_id']]),
            },
            {
                'rel': 'collection',
                'type': 'application/json',
                'href': reverse('stac-collection', args=[value['collection_id']]),
            },
            {
                'rel': 'self',
                'type': 'application/json',
                'href': reverse(
                    'stac-collection-item', args=[value['collection_id'], value['stac_id']]
                ),
            },
        ],
    }

    # geometry
    geojson = json.loads(value['geojson'])
    data['bbox'] = geojson.pop('bbox')
    data['geometry'] = geojson

    # eo
    if value['eo_cloud_cover']:
        data['properties']['eo:cloud_cover'] = value['eo_cloud_cover']
    # image files
    for file_dict in value['image_files']:
        assets[file_dict['id']] = {
            'title': file_dict['title'],
            'href': file_dict['url']
            or ChecksumFile._meta.get_field('file').storage.url(file_dict['filename']),
            'roles': ['data'],
            'properties': {
                'created': isotime(file_dict['created']),
                'modified': isotime(file_dict['modified']),
            },
        }

    # thumbnails
    for file_dict in value['image_files']:
        assets[f'thumbnail_{file_dict["id"]}'] = {
            'href': reverse('image-tiles-thumbnail-png', args=[file_dict['id']]),
            'roles': ['thumbnail'],
            'type': 'image/png',
        }

    # metadata files
    for file_dict in value['ancillary_files'] + value['sidecar_files']:
        assets[file_dict['id']] = {
            'title': file_dict['title'],
            'href': file_dict['url']
            or ChecksumFile._meta.get_field('file').storage.url(file_dict['filename']),
            'roles': ['metadata'],
            'properties': {
                'created': isotime(file_dict['created']),
                'modified': isotime(file_dict['modified']),
            },
        }

    # eo asset definitions
    for bandinfo in value['eo_asset_bandinfo']:
        if 'eo:bands' not in assets[bandinfo['file_id']]['properties']:
            assets[bandinfo['file_id']]['properties']['eo:bands'] = []
        eo_band = {
            'name': f'B{bandinfo["band_number"]}',
            'description': bandinfo['description'] or '',
        }
        if (
            bandinfo['band_range_lower'],
            bandinfo['band_range_upper'],
        ) in BAND_RANGE_BY_COMMON_NAMES.inverse:
            eo_band['common_name'] = BAND_RANGE_BY_COMMON_NAMES.inverse[
                (bandinfo['band_range_lower'], bandinfo['band_range_upper'])
            ]
        elif bandinfo['common_name'] in BAND_RANGE_BY_COMMON_NAMES:
            eo_band['common_name'] = bandinfo['common_name']
        if bandinfo['band_range_lower'] is not None and bandinfo['band_range_upper'] is not None:
            with decimal.localcontext(decimal.BasicContext):
                eo_band['full_width_half_max'] = (
                    float((bandinfo['band_range_upper'] - bandinfo['band_range_lower'])),
                )
                eo_band['center_wavelength'] = (
                    float((bandinfo['band_range_lower'] + bandinfo['band_range_upper']) / 2),
                )

        assets[bandinfo['file_id']]['properties']['eo:bands'].append(eo_band)

    # file derivation graph
    for derivationinfo in value['derivationinfo']:
        source_href = reverse(
            'stac-collection-item',
            args=[derivationinfo['source_collection_id'], derivationinfo['source_item_id']],
        )
        if 'derivations' not in assets[derivationinfo['output_file_id']]['properties']:
            assets[derivationinfo['output_file_id']]['properties']['derivations'] = []
        assets[derivationinfo['output_file_id']]['properties']['derivations'].append(
            {
                'id': derivationinfo['id'],
                'type': derivationinfo['type'],
                'href': source_href + f'#/assets/{derivationinfo["source_file_id"]}',
            }
        )

    if assets:
        data['assets'] = assets
    return data
