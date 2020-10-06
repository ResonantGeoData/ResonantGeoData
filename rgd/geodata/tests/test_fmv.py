import pytest

from rgd.geodata.models.fmv.etl import _populate_fmv_entry

from . import factories
from .datastore import datastore


@pytest.mark.django_db(transaction=True)
def test_populate_fmv_entry_from_klv_file():
    fmv_entry = factories.FMVEntryFactory(
        klv_file__filename='subset_metadata.klv',
        klv_file__from_path=datastore.fetch('subset_metadata.klv'),
    )

    assert _populate_fmv_entry(fmv_entry)

    assert fmv_entry.ground_frames is not None
