import pytest

from geodata import models
from geodata.models.geometry.etl import read_geometry_archive

from . import factories
from .datastore import datastore


@pytest.mark.django_db(transaction=True)
def test_geometry_etl():
    sample_file = 'Streams.zip'
    geom_archive = factories.GeometryArchiveFactory(
        file__filename=sample_file,
        file__from_path=datastore.fetch(sample_file),
    )
    entry = models.GeometryEntry.objects.filter(geometry_archive=geom_archive).first()
    assert entry.data is not None
    # Testing that we can repopulate a geometry archive again
    read_geometry_archive(geom_archive.id)
    # test the field file validator
    models.geometry.base.validate_archive(geom_archive.file)
