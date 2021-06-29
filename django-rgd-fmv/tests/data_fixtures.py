import pytest
from rgd.datastore import datastore

from . import factories


@pytest.fixture
def fmv_klv_file():
    return factories.FMVFactory(
        klv_file__filename='subset_metadata.klv',
        klv_file__from_path=datastore.fetch('subset_metadata.klv'),
    )


@pytest.fixture
def fmv_video_file():
    return factories.FMVFactory(
        file__file__filename='test_fmv.ts',
        file__file__from_path=datastore.fetch('test_fmv.ts'),
        klv_file=None,
        web_video_file=None,
    )
