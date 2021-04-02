import datetime
import json

import pytest

from rgd.geodata.datastore import datastore

from . import factories

SampleFiles = [
    {'name': '20091021202517-01000100-VIS_0001.ntf'},
    {'name': 'aerial_rgba_000003.tiff'},
    {'name': 'cclc_schu_100.tif'},
    {'name': 'landcover_sample_2000.tif'},
    {'name': 'paris_france_10.tiff'},
    {'name': 'rgb_geotiff.tiff'},
    {'name': 'RomanColosseum_WV2mulitband_10.tif'},
]


def _load_sample_files():
    for testfile in SampleFiles:
        imagefile = factories.ImageFileFactory(
            file__file__filename=testfile['name'],
            file__file__from_path=datastore.fetch(testfile['name']),
        )
        image_set = factories.ImageSetFactory(
            images=[imagefile.imageentry.id],
        )
        factories.RasterEntryFactory(
            name=testfile['name'],
            image_set=image_set,
        )


@pytest.mark.django_db(transaction=True)
def test_search_near_point(admin_api_client):
    _load_sample_files()
    items = admin_api_client.get('/api/geosearch/near_point').data
    assert len(items) == len(SampleFiles)
    items = admin_api_client.get(
        '/api/geosearch/near_point', {'longitude': -79, 'latitude': 43}
    ).data
    assert len(items) == 1
    items = admin_api_client.get(
        '/api/geosearch/near_point', {'longitude': -79, 'latitude': 43, 'radius': 1000000}
    ).data
    assert len(items) == 3
    timestr = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    items = admin_api_client.get(
        '/api/geosearch/raster/near_point',
        {'time': timestr, 'timefield': 'acquisition', 'timespan': 86400},
    ).data
    assert len(items) == len(SampleFiles)
    items = admin_api_client.get(
        '/api/geosearch/raster/near_point',
        {'time': timestr, 'timefield': 'acquisition', 'timespan': 0},
    ).data
    assert len(items) == 0


@pytest.mark.django_db(transaction=True)
def test_search_near_point_extent(admin_api_client):
    _load_sample_files()
    results = admin_api_client.get('/api/geosearch/near_point/extent').data
    assert results['count'] == len(SampleFiles)
    results = admin_api_client.get(
        '/api/geosearch/near_point/extent', {'longitude': -79, 'latitude': 43}
    ).data
    assert results['count'] == 1
    results = admin_api_client.get(
        '/api/geosearch/near_point/extent', {'longitude': -79, 'latitude': 43, 'radius': 1000000}
    ).data
    assert results['count'] == 3
    timestr = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    results = admin_api_client.get(
        '/api/geosearch/raster/near_point/extent',
        {'time': timestr, 'timefield': 'acquisition', 'timespan': 86400},
    ).data
    assert results['count'] == len(SampleFiles)
    results = admin_api_client.get(
        '/api/geosearch/raster/near_point/extent',
        {'time': timestr, 'timefield': 'acquisition', 'timespan': 0},
    ).data
    assert results['count'] == 0


@pytest.mark.django_db(transaction=True)
def test_search_bounding_box(admin_api_client):
    _load_sample_files()
    items = admin_api_client.get('/api/geosearch/bounding_box').data
    assert len(items) == len(SampleFiles)
    items = admin_api_client.get(
        '/api/geosearch/bounding_box',
        {
            'minimum_longitude': -80,
            'maximum_longitude': -79,
            'minimum_latitude': 43,
            'maximum_latitude': 44,
        },
    ).data
    assert len(items) == 1
    items = admin_api_client.get(
        '/api/geosearch/bounding_box',
        {
            'minimum_longitude': -90,
            'maximum_longitude': -70,
            'minimum_latitude': 30,
            'maximum_latitude': 50,
        },
    ).data
    assert len(items) == 3
    timestr = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    oldtimestr = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime(
        '%Y-%m-%d %H:%M:%S'
    )
    items = admin_api_client.get(
        '/api/geosearch/raster/bounding_box',
        {'start_time': oldtimestr, 'end_time': timestr, 'timefield': 'acquisition'},
    ).data
    assert len(items) == len(SampleFiles)
    items = admin_api_client.get(
        '/api/geosearch/raster/bounding_box',
        {'start_time': timestr, 'end_time': timestr, 'timefield': 'acquisition'},
    ).data
    assert len(items) == 0


@pytest.mark.django_db(transaction=True)
def test_search_bounding_box_extent(admin_api_client):
    _load_sample_files()
    results = admin_api_client.get('/api/geosearch/bounding_box/extent').data
    assert results['count'] == len(SampleFiles)
    results = admin_api_client.get(
        '/api/geosearch/bounding_box/extent',
        {
            'minimum_longitude': -80,
            'maximum_longitude': -79,
            'minimum_latitude': 43,
            'maximum_latitude': 44,
        },
    ).data
    assert results['count'] == 1
    results = admin_api_client.get(
        '/api/geosearch/bounding_box/extent',
        {
            'minimum_longitude': -90,
            'maximum_longitude': -70,
            'minimum_latitude': 30,
            'maximum_latitude': 50,
        },
    ).data
    assert results['count'] == 3
    timestr = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    oldtimestr = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime(
        '%Y-%m-%d %H:%M:%S'
    )
    results = admin_api_client.get(
        '/api/geosearch/raster/bounding_box/extent',
        {'start_time': oldtimestr, 'end_time': timestr, 'timefield': 'acquisition'},
    ).data
    assert results['count'] == len(SampleFiles)
    results = admin_api_client.get(
        '/api/geosearch/raster/bounding_box/extent',
        {'start_time': timestr, 'end_time': timestr, 'timefield': 'acquisition'},
    ).data
    assert results['count'] == 0


@pytest.mark.django_db(transaction=True)
def test_search_geojson(admin_api_client):
    _load_sample_files()
    items = admin_api_client.get('/api/geosearch/geojson').data
    assert len(items) == len(SampleFiles)
    items = admin_api_client.get(
        '/api/geosearch/geojson',
        {
            'geojson': json.dumps(
                {
                    'type': 'Polygon',
                    'coordinates': [[[-80, 43], [-80, 44], [-79, 44], [-79, 43], [-80, 43]]],
                }
            )
        },
    ).data
    assert len(items) == 1
    items = admin_api_client.get(
        '/api/geosearch/geojson',
        {
            'geojson': json.dumps(
                {
                    'type': 'Polygon',
                    'coordinates': [[[-90, 30], [-90, 50], [-70, 50], [-70, 30], [-90, 30]]],
                }
            )
        },
    ).data
    assert len(items) == 3
    timestr = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    oldtimestr = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime(
        '%Y-%m-%d %H:%M:%S'
    )
    items = admin_api_client.get(
        '/api/geosearch/raster/geojson',
        {'start_time': oldtimestr, 'end_time': timestr, 'timefield': 'acquisition'},
    ).data
    assert len(items) == len(SampleFiles)
    items = admin_api_client.get(
        '/api/geosearch/raster/geojson',
        {'start_time': timestr, 'end_time': timestr, 'timefield': 'acquisition'},
    ).data
    assert len(items) == 0


@pytest.mark.django_db(transaction=True)
def test_search_geojson_extent(admin_api_client):
    _load_sample_files()
    results = admin_api_client.get('/api/geosearch/geojson/extent').data
    assert results['count'] == len(SampleFiles)
    results = admin_api_client.get(
        '/api/geosearch/geojson/extent',
        {
            'geojson': json.dumps(
                {
                    'type': 'Polygon',
                    'coordinates': [[[-80, 43], [-80, 44], [-79, 44], [-79, 43], [-80, 43]]],
                }
            )
        },
    ).data
    assert results['count'] == 1
    results = admin_api_client.get(
        '/api/geosearch/geojson/extent',
        {
            'geojson': json.dumps(
                {
                    'type': 'Polygon',
                    'coordinates': [[[-90, 30], [-90, 50], [-70, 50], [-70, 30], [-90, 30]]],
                }
            )
        },
    ).data
    assert results['count'] == 3
    timestr = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    oldtimestr = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime(
        '%Y-%m-%d %H:%M:%S'
    )
    results = admin_api_client.get(
        '/api/geosearch/raster/geojson/extent',
        {'start_time': oldtimestr, 'end_time': timestr, 'timefield': 'acquisition'},
    ).data
    assert results['count'] == len(SampleFiles)
    results = admin_api_client.get(
        '/api/geosearch/raster/geojson/extent',
        {'start_time': timestr, 'end_time': timestr, 'timefield': 'acquisition'},
    ).data
    assert results['count'] == 0
