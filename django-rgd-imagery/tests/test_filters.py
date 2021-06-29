import pytest
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
