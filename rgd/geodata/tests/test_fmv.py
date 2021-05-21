import os

import pytest

from rgd.geodata.datastore import datastore
from rgd.geodata.models.fmv import FMVEntry
from rgd.geodata.models.mixins import Status

from . import factories

NO_KWIVER = os.environ.get('NO_KWIVER', False)


@pytest.mark.django_db(transaction=True)
def test_populate_fmv_entry_from_klv_file():
    # Since we provide the KLV file and the factory provides a dummpy MP4 file,
    #   the ETL routine will skip over those parts and just generate the FMVEntry
    fmv_file = factories.FMVFileFactory(
        klv_file__filename='subset_metadata.klv',
        klv_file__from_path=datastore.fetch('subset_metadata.klv'),
    )
    fmv_entry = FMVEntry.objects.filter(fmv_file=fmv_file).first()
    assert fmv_entry.ground_frames is not None


@pytest.mark.skipif(NO_KWIVER, reason='User set NO_KWIVER')
@pytest.mark.django_db(transaction=True)
def test_full_fmv_etl():
    fmv_file = factories.FMVFileFactory(
        file__file__filename='test_fmv.ts',
        file__file__from_path=datastore.fetch('test_fmv.ts'),
        klv_file=None,
        web_video_file=None,
    )
    assert fmv_file.status == Status.SUCCEEDED, fmv_file.failure_reason
    fmv_entry = FMVEntry.objects.get(fmv_file=fmv_file)
    assert fmv_entry.ground_frames is not None
