import json

import pytest

from rgd_client import Rgdc

client = Rgdc(username='test', password='testing', api_url='http://localhost:8000/api')
bbox = {
    'type': 'Polygon',
    'coordinates': [
        [
            [-105.45091240368326, 39.626245373878696],
            [-105.45091240368326, 39.929904289147274],
            [-104.88775649170178, 39.929904289147274],
            [-104.88775649170178, 39.626245373878696],
            [-105.45091240368326, 39.626245373878696],
        ]
    ],
}


def test_basic_search(rgd_imagery_demo):

    q = client.search(query=json.dumps(bbox), predicate='intersects')

    assert any(x['subentry_name'] == 'afie_1.jpg' for x in q)

    assert any(
        x['subentry_name'] == 'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band1.tif' for x in q
    )


def test_inspect_raster(rgd_imagery_demo):

    q = client.search(query=json.dumps(bbox), predicate='intersects')

    raster_meta = next(
        (
            x
            for x in q
            if x['subentry_name'] == 'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band1.tif'
        ),
        None,
    )

    assert raster_meta is not None

    try:
        raster = client.get_raster(raster_meta)
        count = len(raster['parent_raster']['image_set']['images'])
    except Exception:
        pytest.fail('Failed to get raster from meta')

    for i in range(count):
        try:
            client.download_raster_thumbnail(raster_meta, band=i)
        except Exception:
            pytest.fail(f'Failed to download raster thumbnail {i}')


# TODO: figure out minio hostname issue
def test_download_raster(rgd_imagery_demo):

    q = client.search(query=json.dumps(bbox), predicate='intersects')

    assert len(q) >= 1

    try:
        client.download_raster(q[0])
    except Exception as e:
        print(e)
        pytest.fail('Failed to download raster image set')


# TODO: figure out TemplateDoesNotExist error
# def test_basic_stac_search(rgd_imagery_demo):

#     try:
#         client.search_raster_stac(query=json.dumps(bbox), predicate='intersects')
#     except Exception:
#         pytest.fail('Failed STAC search')
