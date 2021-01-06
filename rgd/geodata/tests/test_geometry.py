import pytest

from rgd.geodata import models
from rgd.geodata.datastore import datastore
from rgd.geodata.models.geometry.etl import read_geometry_archive

from . import factories


@pytest.mark.parametrize(
    'sample_file',
    ['Streams.zip', 'dlwatersan.zip'],
)
@pytest.mark.django_db(transaction=True)
def test_geometry_etl(sample_file):
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
