import pytest
from rgd import models
from rgd.datastore import datastore

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
