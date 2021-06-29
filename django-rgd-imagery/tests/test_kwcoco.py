import pytest
from rgd.datastore import datastore
from rgd_imagery.models import Image, ImageMeta, RLESegmentation

from . import factories


def _run_kwcoco_import(demo):
    f_image_archive = demo['archive']
    f_spec_file = demo['spec']

    return factories.KWCOCOArchiveFactory(
        image_archive__file__filename=f_image_archive,
        image_archive__file__from_path=datastore.fetch(f_image_archive),
        spec_file__file__filename=f_spec_file,
        spec_file__file__from_path=datastore.fetch(f_spec_file),
    )


@pytest.mark.django_db(transaction=True)
def test_kwcoco_basic_demo():
    demo = {
        'archive': 'demodata.zip',
        'spec': 'demo.kwcoco.json',
        'n_images': 3,
        'n_annotations': 11,
    }

    kwds = _run_kwcoco_import(demo)
    assert kwds.image_set.count == demo['n_images']
    annotations = [a for anns in kwds.image_set.get_all_annotations().values() for a in anns]
    assert len(annotations) == demo['n_annotations']
    # Trigger save event and make sure original images were deleted
    image_file_ids = [im.id for im in kwds.image_set.images.all()]
    kwds.save()
    for id in image_file_ids:
        with pytest.raises(Image.DoesNotExist):
            Image.objects.get(id=id)
    # Now do same for delete
    image_file_ids = [im.id for im in kwds.image_set.images.all()]
    kwds.delete()
    for id in image_file_ids:
        with pytest.raises(Image.DoesNotExist):
            Image.objects.get(id=id)


@pytest.mark.django_db(transaction=True)
def test_kwcoco_rle_demo():
    demo = {
        'archive': 'demo_rle.zip',
        'spec': 'demo_rle.kwcoco.json',
        'n_images': 2,
        'n_annotations': 15,
    }

    kwds = _run_kwcoco_import(demo)
    assert kwds.image_set.count == demo['n_images']
    annotations = [a for anns in kwds.image_set.get_all_annotations().values() for a in anns]
    assert len(annotations) == demo['n_annotations']

    # Test the RLESegmentation methods
    seg = RLESegmentation.objects.all().first()
    image_meta = ImageMeta.objects.get(parent_image=seg.annotation.image)
    assert seg.width == image_meta.width
    assert seg.height == image_meta.height

    rle = seg.to_rle()
    assert 'counts' in rle
    assert 'size' in rle
    assert rle['size'] == [seg.height, seg.width]

    mask = seg.to_mask()
    assert mask.shape == (seg.height, seg.width)
