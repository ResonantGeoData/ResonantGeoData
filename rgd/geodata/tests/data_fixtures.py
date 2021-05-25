import pytest

from rgd.geodata import models
from rgd.geodata.datastore import datastore

from . import factories


@pytest.fixture
def checksum_file():
    return factories.ChecksumFileFactory()


@pytest.fixture
def checksum_file_url():
    return factories.ChecksumFileFactory(
        file=None,
        url=datastore.get_url('stars.png'),
        type=models.FileSourceType.URL,
    )


@pytest.fixture
def geotiff_image_entry():
    imagefile = factories.ImageFileFactory(
        file__file__filename='paris_france_10.tiff',
        file__file__from_path=datastore.fetch('paris_france_10.tiff'),
    )
    return imagefile.imageentry


@pytest.fixture
def astro_image():
    name = 'astro.png'
    imagefile = factories.ImageFileFactory(
        file__file__filename=name,
        file__file__from_path=datastore.fetch(name),
    )
    return imagefile.imageentry


@pytest.fixture
def sample_raster_a():
    imagefile = factories.ImageFileFactory(
        file__file__filename='20091021202517-01000100-VIS_0001.ntf',
        file__file__from_path=datastore.fetch('20091021202517-01000100-VIS_0001.ntf'),
    )
    image_set = factories.ImageSetFactory(
        images=[imagefile.imageentry.id],
    )
    raster = factories.RasterEntryFactory(
        name='20091021202517-01000100-VIS_0001.ntf',
        image_set=image_set,
    )
    return raster.rastermetaentry


@pytest.fixture
def sample_raster_b():
    imagefile = factories.ImageFileFactory(
        file__file__filename='cclc_schu_100.tif',
        file__file__from_path=datastore.fetch('cclc_schu_100.tif'),
    )
    image_set = factories.ImageSetFactory(
        images=[imagefile.imageentry.id],
    )
    raster = factories.RasterEntryFactory(
        name='cclc_schu_100.tif',
        image_set=image_set,
    )
    return raster.rastermetaentry


@pytest.fixture
def sample_raster_c():
    imagefile = factories.ImageFileFactory(
        file__file__filename='RomanColosseum_WV2mulitband_10.tif',
        file__file__from_path=datastore.fetch('RomanColosseum_WV2mulitband_10.tif'),
    )
    image_set = factories.ImageSetFactory(
        images=[imagefile.imageentry.id],
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
    b1 = factories.ImageFileFactory(
        file__file__filename=landsat_files[0],
        file__file__from_path=datastore.fetch(landsat_files[0]),
    )
    b2 = factories.ImageFileFactory(
        file__file__filename=landsat_files[1],
        file__file__from_path=datastore.fetch(landsat_files[1]),
    )
    b3 = factories.ImageFileFactory(
        file__file__filename=landsat_files[2],
        file__file__from_path=datastore.fetch(landsat_files[2]),
    )
    image_set = factories.ImageSetFactory(
        images=[
            b1.imageentry.id,
            b2.imageentry.id,
            b3.imageentry.id,
        ],
    )
    # Create a RasterEntry from the three band image entries
    raster = factories.RasterEntryFactory(
        name='Multi File Test',
        image_set=image_set,
    )
    return raster.rastermetaentry


@pytest.fixture
def fmv_klv_file():
    return factories.FMVFileFactory(
        klv_file__filename='subset_metadata.klv',
        klv_file__from_path=datastore.fetch('subset_metadata.klv'),
    )


@pytest.fixture
def fmv_video_file():
    return factories.FMVFileFactory(
        file__file__filename='test_fmv.ts',
        file__file__from_path=datastore.fetch('test_fmv.ts'),
        klv_file=None,
        web_video_file=None,
    )
