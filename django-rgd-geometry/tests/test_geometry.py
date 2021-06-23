import pytest
from rgd.datastore import datastore
from rgd_geometry import models
from rgd_geometry.tasks.etl import read_geometry_archive

from . import factories


@pytest.mark.parametrize(
    'sample_file',
    ['Streams.zip', 'dlwatersan.zip'],
)
@pytest.mark.django_db(transaction=True)
def test_geometry_etl(sample_file):
    geom_archive = factories.GeometryArchiveFactory(
        file__file__filename=sample_file,
        file__file__from_path=datastore.fetch(sample_file),
    )
    entry = models.Geometry.objects.filter(geometry_archive=geom_archive).first()
    assert entry.data is not None
    # Testing that we can repopulate a geometry archive again
    read_geometry_archive(geom_archive.id)
    # test the field file validator
    models.validate_archive(geom_archive.file.file)
