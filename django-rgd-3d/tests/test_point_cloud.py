from pathlib import Path
import tempfile

import pytest
from rgd.datastore import datastore
from rgd.models import FileSourceType
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


@pytest.mark.django_db(transaction=True)
def test_mesh_3d_etl_custom_output_handler(settings):

    directory = tempfile.gettempdir()

    def output_file_handler(instance, file_handle, name):
        # save to path on disk and give `file://` URL to ChecksumFile
        path = Path(directory, name)
        with open(path, 'wb') as f:
            f.write(file_handle.read())
        instance.type = FileSourceType.URL
        instance.url = f'file://{path}'
        instance.file = None

    settings.RGD_OUTPUT_FILE_HANDLER = output_file_handler

    entry = factories.Mesh3DFactory(
        file__file__filename='topo.vtk',
        file__file__from_path=datastore.fetch(
            'topo.vtk',
        ),
    )
    entry.refresh_from_db()
    assert entry.vtp_data is not None
    assert entry.vtp_data.url.startswith(f'file://{directory}')
