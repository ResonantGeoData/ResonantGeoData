import pytest

from rgd.geodata.models.fmv.etl import _populate_fmv_entry

from . import factories
from .datastore import datastore


@pytest.mark.django_db(transaction=True)
def test_populate_fmv_entry_from_klv_file():
    fmv_entry = factories.FMVEntryFactory(
        klv_file__filename='09172008flight1tape3_2.mpg.klv',
        klv_file__from_path=datastore.fetch('09172008flight1tape3_2.mpg.klv'),
    )

    assert _populate_fmv_entry(fmv_entry)

    assert fmv_entry.ground_frames is not None
