import pytest

from rgd.geodata.datastore import datastore
from rgd.geodata.models import RasterMetaEntry

from . import factories

# These test files are dramatically downsampled for rapid testing
LandsatFiles = [
    'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band1.tif',
    'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band2.tif',
    'LC08_L1TP_034032_20200429_20200509_01_T1_sr_band3.tif',
]


@pytest.fixture
def sample_raster_a():
    imagefile = factories.ImageFileFactory(
        file__file__filename='RomanColosseum_WV2mulitband_10.tif',
        file__file__from_path=datastore.fetch('RomanColosseum_WV2mulitband_10.tif'),
    )
    image_set = factories.ImageSetFactory(
        images=[imagefile.imageentry.id],
    )
    raster = factories.RasterEntryFactory(
        name='20091021202517-01000100-VIS_0001.ntf',
        image_set=image_set,
    )
    return RasterMetaEntry.objects.get(parent_raster=raster)


@pytest.fixture
def sample_landsat_raster():
    b1 = factories.ImageFileFactory(
        file__file__filename=LandsatFiles[0],
        file__file__from_path=datastore.fetch(LandsatFiles[0]),
    )
    b2 = factories.ImageFileFactory(
        file__file__filename=LandsatFiles[1],
        file__file__from_path=datastore.fetch(LandsatFiles[1]),
    )
    b3 = factories.ImageFileFactory(
        file__file__filename=LandsatFiles[2],
        file__file__from_path=datastore.fetch(LandsatFiles[2]),
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
    return RasterMetaEntry.objects.get(parent_raster=raster)


def _check_conforms_stac(data):
    assert 'stac_version' in data
    assert 'assets' in data
    # TODO: make this better


@pytest.mark.django_db(transaction=True)
def test_raster_stac_serializer_simple(admin_api_client, sample_raster_a):
    id = sample_raster_a.id
    response = admin_api_client.get(f'/api/geodata/imagery/raster/{id}/stac')
    assert response.status_code == 200
    data = response.data
    assert data
    _check_conforms_stac(data)
    assets = data['assets']
    assert len(assets) == 1


@pytest.mark.django_db(transaction=True)
def test_raster_stac_serializer_multi_file_bands(admin_api_client, sample_landsat_raster):
    id = sample_landsat_raster.id
    response = admin_api_client.get(f'/api/geodata/imagery/raster/{id}/stac')
    assert response.status_code == 200
    data = response.data
    assert data
    _check_conforms_stac(data)
    assets = data['assets']
    assert len(assets) == 3
