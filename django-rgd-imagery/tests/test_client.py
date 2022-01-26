import json

from django.forms.models import model_to_dict
import pytest
from rgd.models import ChecksumFile
from rgd_imagery.models.base import Image, ImageSet
from rgd_imagery.models.raster import RasterMeta
from rgd_imagery_client import ImageryClient

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
def test_inspect_raster(py_client: ImageryClient, sample_raster_multi):
    q = py_client.rgd.search(query=json.dumps(bbox), predicate='intersects')
    raster_meta = next(
        (x for x in q if x['subentry_name'] == 'Multi File Test'),
        None,
    )

    assert raster_meta is not None

    try:
        raster = py_client.imagery.get_raster(raster_meta)
        count = len(raster['parent_raster']['image_set']['images'])
    except Exception as e:
        pytest.fail(f'Failed to get raster from meta: {e}')

    for i in range(count):
        try:
            py_client.imagery.download_raster_thumbnail(raster_meta, band=i)
        except Exception as e:
            pytest.fail(f'Failed to download raster thumbnail {i}: {e}')


@pytest.mark.django_db(transaction=True)
def test_get_raster(py_client: ImageryClient, sample_raster_multi):
    raster = py_client.imagery.get_raster(sample_raster_multi.pk)
    assert raster
    stac = py_client.imagery.get_raster(sample_raster_multi.pk, stac=True)
    assert stac


@pytest.mark.django_db(transaction=True)
def test_download_raster(py_client: ImageryClient, sample_raster_multi):
    q = py_client.rgd.search(query=json.dumps(bbox), predicate='intersects')

    assert len(q) >= 1

    try:
        py_client.imagery.download_raster(q[0])
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
def test_create_image_from_file(py_client: ImageryClient, sample_raster_multi):
    """Test that creation of an Image with a ChecksumFile succeeds."""
    # Get existing ChecksumFile to use in image creation
    file: ChecksumFile = ChecksumFile.objects.first()

    image_dict = py_client.imagery.create_image_from_file(model_to_dict(file))
    assert image_dict['file']['id'] == file.id


@pytest.mark.django_db(transaction=True)
def test_create_image_set(py_client: ImageryClient, astro_image, geotiff_image_entry):
    """Test that creation of an ImageSet succeeds."""
    # Get existing Images to use in ImageSet creation
    images = [model_to_dict(im) for im in Image.objects.all()]
    imageset_dict = py_client.imagery.create_image_set(images)

    imageset_dict_image_ids = {im['id'] for im in imageset_dict['images']}
    assert all(im['id'] in imageset_dict_image_ids for im in images)


@pytest.mark.django_db(transaction=True)
def test_create_raster_from_image_set(py_client: ImageryClient, sample_raster_multi: RasterMeta):
    """Test that creation of an ImageSet succeeds."""
    # Get image set from supplied raster
    image_set: ImageSet = sample_raster_multi.parent_raster.image_set
    imageset_dict = model_to_dict(image_set)

    # Delete raster, keeping image set so the raster can be re-created
    sample_raster_multi.parent_raster.delete()

    # Ancillary files are the same used in the image set from sample_raster_multi
    ancillary_files = [model_to_dict(file) for file in ChecksumFile.objects.all()[:5]]
    raster_dict = py_client.imagery.create_raster_from_image_set(imageset_dict, ancillary_files)

    # Make assertions
    assert raster_dict['image_set']['id'] == imageset_dict['id']

    sorted_ancillary_files_ids = sorted(file['id'] for file in ancillary_files)
    sorted_raster_ancillary_file_ids = sorted(file['id'] for file in raster_dict['ancillary_files'])
    assert sorted_ancillary_files_ids == sorted_raster_ancillary_file_ids
