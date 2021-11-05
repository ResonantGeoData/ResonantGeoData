import os
import tempfile

from celery.utils.log import get_task_logger
from rgd.models import ChecksumFile
from rgd.utility import get_or_create_no_commit, get_temp_dir
from rgd_3d.models import PointCloud, PointCloudMeta

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
    import pyvista as pv

    points = pv.PolyData(mesh.points)
    points.point_arrays.update(mesh.point_arrays)
    points.save(output_path)


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


def read_point_cloud_file(pc_file):
    """Read a PointCloud object and create a new PointCloudMeta."""
    if not isinstance(pc_file, PointCloud):
        pc_file = PointCloud.objects.get(pk=pc_file)
    pc_entry, _ = get_or_create_no_commit(PointCloudMeta, source=pc_file)
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
    if not pc_entry.vtp_data.file_set:
        pc_entry.vtp_data.file_set = pc_file.file.file_set
    _file_conversion_helper(pc_file.file, pc_entry.vtp_data.file, method, extension='.vtp')
    # Save the record
    pc_entry.save()
