import pytest

from geodata.models.fmv.base import FMVEntry
from geodata.models.fmv.etl import _populate_fmv_entry

from . import factories
from .datastore import datastore


@pytest.mark.django_db(transaction=True)
def test_populate_fmv_entry_from_klv_file():
    fmv_entry = factories.FMVEntryFactory(
        klv_file__filename='09172008flight1tape3_2.mpg.klv',
        klv_file__from_path=datastore.fetch('09172008flight1tape3_2.mpg.klv'),
    )

    assert _populate_fmv_entry(fmv_entry)

    assert fmv_entry.ground_frame is not None


@pytest.mark.django_db(transaction=True)
def test_full_fmv_etl():
    fmv_file = factories.FMVFileFactory(
        file__filename='test_fmv.ts',
        file__from_path=datastore.fetch('test_fmv.ts'),
    )

    fmv_entry = FMVEntry.objects.filter(fmv_file=fmv_file).first()

    assert fmv_entry.ground_frame is not None
