import pytest
from rgd.models import ChecksumFile, Collection
from rgd_imagery import models
from rgd_imagery.filters import RasterMetaFilter


@pytest.mark.django_db(transaction=True)
def test_raster_num_bands(sample_raster_b, sample_raster_c):
    # b has many bands and c has 1 band
    assert models.RasterMeta.objects.count() == 2
    filterset = RasterMetaFilter(
        data={
            'num_bands_max': 2,
        }
    )
    assert filterset.is_valid()
    qs = filterset.filter_queryset(models.RasterMeta.objects.all())
    assert qs.count() == 1


@pytest.mark.django_db(transaction=True)
def test_raster_filter_collections(sample_raster_a, sample_raster_multi):
    collection = Collection.objects.create(name='Test')
    files = sample_raster_multi.parent_raster.image_set.images.values_list('file')
    ChecksumFile.objects.filter(pk__in=files).update(collection=collection)
    assert models.RasterMeta.objects.count() == 2
    filterset = RasterMetaFilter(
        data={
            'collections': [
                collection.pk,
            ]
        }
    )
    assert filterset.is_valid()
    qs = filterset.filter_queryset(models.RasterMeta.objects.all())
    assert qs.count() == 1
    assert qs.first().pk == sample_raster_multi.pk
