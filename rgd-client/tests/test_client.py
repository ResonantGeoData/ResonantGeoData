import json

from django.forms.models import model_to_dict
import pytest
from rgd.models.common import ChecksumFile
from rgd_imagery.models.base import Image, ImageSet

from rgd_client import Rgdc

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


@pytest.mark.django_db(transaction=True)
def test_basic_search(py_client, rgd_imagery_demo):

    q = py_client.search(query=json.dumps(bbox), predicate='intersects')

    assert any(x['subentry_name'] == 'afie_1.jpg' for x in q)

    assert any(
        x['subentry_name'] == 'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band1.tif' for x in q
    )


@pytest.mark.django_db(transaction=True)
def test_inspect_raster(py_client, rgd_imagery_demo):

    q = py_client.search(query=json.dumps(bbox), predicate='intersects')

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
        raster = py_client.get_raster(raster_meta)
        count = len(raster['parent_raster']['image_set']['images'])
    except Exception:
        pytest.fail('Failed to get raster from meta')

    for i in range(count):
        try:
            py_client.download_raster_thumbnail(raster_meta, band=i)
        except Exception:
            pytest.fail(f'Failed to download raster thumbnail {i}')


@pytest.mark.django_db(transaction=True)
def test_download_raster(py_client, rgd_imagery_demo):

    q = py_client.search(query=json.dumps(bbox), predicate='intersects')

    assert len(q) >= 1

    try:
        py_client.download_raster(q[0])
    except Exception as e:
        print(e)
        pytest.fail('Failed to download raster image set')


# TODO: figure out TemplateDoesNotExist error
# def test_basic_stac_search(rgd_imagery_demo):

#     try:
#         py_client.search_raster_stac(query=json.dumps(bbox), predicate='intersects')
#     except Exception:
#         pytest.fail('Failed STAC search')


@pytest.mark.django_db(transaction=True)
def test_create_file_from_url(py_client: Rgdc, rgd_imagery_demo):
    """Test that creation of a ChecksumFile with a URL succeeds."""
    # Get existing file and use it's URL to create a new ChecksumFile
    file: ChecksumFile = ChecksumFile.objects.first()
    file_url = file.get_url()

    file_dict = py_client.create_file_from_url(file_url)
    assert file_dict['url'] == file_url
    assert file_dict['type'] == 2


@pytest.mark.django_db(transaction=True)
def test_create_image_from_file(py_client: Rgdc, rgd_imagery_demo):
    """Test that creation of an Image with a ChecksumFile succeeds."""
    # Get existing ChecksumFile to use in image creation
    file: ChecksumFile = ChecksumFile.objects.first()

    image_dict = py_client.create_image_from_file(model_to_dict(file))
    assert image_dict['file']['id'] == file.id


@pytest.mark.django_db(transaction=True)
def test_create_image_set(py_client: Rgdc, rgd_imagery_demo):
    """Test that creation of an ImageSet succeeds."""
    # Get existing Images to use in ImageSet creation
    images = [model_to_dict(im) for im in Image.objects.all()[:5]]
    imageset_dict = py_client.create_image_set(images)

    imageset_dict_image_ids = {im['id'] for im in imageset_dict['images']}
    assert all(im['id'] in imageset_dict_image_ids for im in images)


@pytest.mark.django_db(transaction=True)
def test_create_raster_from_image_set(py_client: Rgdc, rgd_imagery_demo):
    """Test that creation of an ImageSet succeeds."""
    # Create ImageSet from existing images to use in Raster creation
    images = [model_to_dict(im) for im in Image.objects.all()[:5]]
    imageset_dict = py_client.create_image_set(images)

    ancillary_files = [model_to_dict(file) for file in ChecksumFile.objects.all()[:5]]
    raster_dict = py_client.create_raster_from_image_set(imageset_dict, ancillary_files)

    # Make assertions
    assert raster_dict['image_set']['id'] == imageset_dict['id']

    sorted_ancillary_files_ids = sorted(file['id'] for file in ancillary_files)
    sorted_raster_ancillary_file_ids = sorted(file['id'] for file in raster_dict['ancillary_files'])
    assert sorted_ancillary_files_ids == sorted_raster_ancillary_file_ids
