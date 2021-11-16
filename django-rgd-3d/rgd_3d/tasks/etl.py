import os
import tempfile

from celery.utils.log import get_task_logger
from rgd.models import ChecksumFile
from rgd.utility import get_or_create_no_commit, get_temp_dir
from rgd_3d.models import Mesh3D, Mesh3DMeta

logger = get_task_logger(__name__)


def _file_conversion_helper(source, output_field, method, prefix='', extension='', **kwargs):
    workdir = get_temp_dir()
    with tempfile.TemporaryDirectory(dir=workdir) as tmpdir:
        # NOTE: cannot use FUSE with PyntCloud because it checks file extension
        #       in path. Additionally, The `name` field for the file MUST have
        #       the extension.
        with source.yield_local_path(try_fuse=False) as file_path:
            output_path = os.path.join(tmpdir, prefix + os.path.basename(source.name) + extension)
            method(str(file_path), str(output_path), **kwargs)
        with open(output_path, 'rb') as f:
            output_field.save(os.path.basename(output_path), f)


def _save_pyvista(mesh, output_path):
    surf = mesh.extract_surface()
    surf.save(output_path)


def _use_pyntcloud_pyvista(input_path, output_path):
    from pyntcloud import PyntCloud

    cloud = PyntCloud.from_file(input_path)
    mesh = cloud.to_instance('pyvista', mesh=False)
    _save_pyvista(mesh, output_path)


def _use_pyvista(input_path, output_path):
    import pyvista as pv

    mesh = pv.read(input_path)
    _save_pyvista(mesh, output_path)


def _get_readers():
    import pyvista as pv

    methods = {
        'las': _use_pyntcloud_pyvista,
        'npy': _use_pyntcloud_pyvista,
        'npz': _use_pyntcloud_pyvista,
    }
    methods.update({k[1::]: _use_pyvista for k in pv.utilities.fileio.READERS.keys()})
    return methods


def read_mesh_3d_file(pc_file):
    """Read a Mesh3D object and create a new Mesh3DMeta."""
    if not isinstance(pc_file, Mesh3D):
        pc_file = Mesh3D.objects.get(pk=pc_file)
    pc_entry, _ = get_or_create_no_commit(Mesh3DMeta, source=pc_file)
    pc_entry.name = pc_file.file.name
    # Parse the point cloud file format and convert
    ext = pc_file.file.name.split('.')[-1].strip().lower()
    try:
        method = _get_readers()[ext]
    except KeyError:
        raise ValueError(f'Extension `{ext}` unsupported for point cloud conversion.')
    try:
        pc_entry.vtp_data
    except ChecksumFile.DoesNotExist:
        pc_entry.vtp_data = ChecksumFile()
    if not pc_entry.vtp_data.collection:
        pc_entry.vtp_data.collection = pc_file.file.collection
    _file_conversion_helper(pc_file.file, pc_entry.vtp_data.file, method, extension='.vtp')
    # Save the record
    pc_entry.save()
