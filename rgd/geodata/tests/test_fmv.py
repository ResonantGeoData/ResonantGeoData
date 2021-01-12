import pytest

from rgd.geodata.datastore import datastore
from rgd.geodata.models.fmv.base import FMVEntry

from . import factories


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


@pytest.mark.django_db(transaction=True)
def test_full_fmv_etl():
    fmv_file = factories.FMVFileFactory(
        file__filename='test_fmv.ts',
        file__from_path=datastore.fetch('test_fmv.ts'),
    )

    fmv_entry = FMVEntry.objects.filter(fmv_file=fmv_file).first()

    assert fmv_entry.ground_frames is not None
