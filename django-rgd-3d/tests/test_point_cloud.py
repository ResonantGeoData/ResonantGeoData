import pytest
from rgd.datastore import datastore
from rgd_3d.tasks.etl import read_mesh_3d_file

from . import factories


@pytest.mark.parametrize(
    'sample_file',
    [
        'topo.vtk',
    ],
)
@pytest.mark.django_db(transaction=True)
def test_mesh_3d_etl(sample_file):
    entry = factories.Mesh3DFactory(
        file__file__filename=sample_file,
        file__file__from_path=datastore.fetch(sample_file),
    )
    entry.refresh_from_db()
    assert entry.vtp_data is not None
    # Testing that we can repopulate a point cloud entry
    read_mesh_3d_file(entry.id)
