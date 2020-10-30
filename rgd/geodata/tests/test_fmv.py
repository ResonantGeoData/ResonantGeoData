import pytest

from rgd.geodata.models.fmv.base import FMVEntry

from . import factories
from .datastore import datastore


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
