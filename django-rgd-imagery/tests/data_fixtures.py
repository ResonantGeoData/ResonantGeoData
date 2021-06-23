import pytest
from rgd.datastore import datastore
from rgd.models import FileSourceType

from . import factories


@pytest.fixture
def geotiff_image_entry():
    image = factories.ImageFactory(
        file__file__filename='paris_france_10.tiff',
        file__file__from_path=datastore.fetch('paris_france_10.tiff'),
    )
    return image


@pytest.fixture
def astro_image():
    name = 'astro.png'
    image = factories.ImageFactory(
        file__file__filename=name,
        file__file__from_path=datastore.fetch(name),
    )
    return image


@pytest.fixture
def sample_raster_a():
    image = factories.ImageFactory(
        file__file__filename='20091021202517-01000100-VIS_0001.ntf',
        file__file__from_path=datastore.fetch('20091021202517-01000100-VIS_0001.ntf'),
    )
    image_set = factories.ImageSetFactory(
        images=[image.id],
    )
    raster = factories.RasterEntryFactory(
        name='20091021202517-01000100-VIS_0001.ntf',
        image_set=image_set,
    )
    return raster.rastermetaentry


@pytest.fixture
def sample_raster_b():
    image = factories.ImageFactory(
        file__file__filename='cclc_schu_100.tif',
        file__file__from_path=datastore.fetch('cclc_schu_100.tif'),
    )
    image_set = factories.ImageSetFactory(
        images=[image.id],
    )
    raster = factories.RasterEntryFactory(
        name='cclc_schu_100.tif',
        image_set=image_set,
    )
    return raster.rastermetaentry


@pytest.fixture
def sample_raster_c():
    image = factories.ImageFactory(
        file__file__filename='RomanColosseum_WV2mulitband_10.tif',
        file__file__from_path=datastore.fetch('RomanColosseum_WV2mulitband_10.tif'),
    )
    image_set = factories.ImageSetFactory(
        images=[image.id],
    )
    raster = factories.RasterEntryFactory(
        name='RomanColosseum_WV2mulitband_10.tif',
        image_set=image_set,
    )
    return raster.rastermetaentry


@pytest.fixture
def sample_raster_multi():
    # These test files are dramatically downsampled for rapid testing
    landsat_files = [
        'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band1.tif',
        'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band2.tif',
        'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band3.tif',
    ]
    images = [
        factories.ImageFactory(
            file__file__filename=landsat_files[0],
            file__file__from_path=datastore.fetch(f),
        )
        for f in landsat_files
    ]
    image_set = factories.ImageSetFactory(
        images=images,
    )
    # Create a RasterEntry from the three band image entries
    raster = factories.RasterEntryFactory(
        name='Multi File Test',
        image_set=image_set,
    )
    return raster.rastermetaentry


@pytest.fixture
def sample_raster_url():
    landsat_files = [
        'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band1.tif',
        'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band2.tif',
        'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band3.tif',
    ]
    images = [
        factories.ImageFactory(
            file__type=FileSourceType.URL,
            file__file=None,
            file__url=datastore.get_url(f),
        )
        for f in landsat_files
    ]
    image_set = factories.ImageSetFactory(
        images=images,
    )
    anc = factories.ChecksumFileFactory(
        file=None,
        url=datastore.get_url('stars.png'),
        type=FileSourceType.URL,
    )
    # Create a RasterEntry from the three band image entries
    raster = factories.RasterEntryFactory(
        name='Multi File Test',
        image_set=image_set,
    )
    raster.ancillary_files.add(anc)
    raster.save()
    return raster.rastermetaentry


@pytest.fixture
def elevation():
    name = 'Elevation.tif'
    image = factories.ImageFactory(
        file__file__filename=name,
        file__file__from_path=datastore.fetch(name),
    )
    return image
