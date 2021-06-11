import pytest
from rgd.geodata.datastore import datastore
from rgd.geodata.models.threed.etl import read_point_cloud_file

from rgd.geodata import models

from . import factories


@pytest.mark.parametrize(
    'sample_file',
    [
        'topo.vtk',
    ],
)
@pytest.mark.django_db(transaction=True)
def test_point_cloud_etl(sample_file):
    pc_file = factories.PointCloudFileFactory(
        file__file__filename=sample_file,
        file__file__from_path=datastore.fetch(sample_file),
    )
    entry = models.PointCloudEntry.objects.filter(source=pc_file).first()
    assert entry.vtp_data is not None
    # Testing that we can repopulate a point cloud entry
    read_point_cloud_file(pc_file.id)
