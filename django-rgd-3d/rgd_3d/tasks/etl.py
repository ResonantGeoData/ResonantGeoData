import os
import tempfile

from celery.utils.log import get_task_logger
from django.conf import settings
import numpy as np
from rgd.models import ChecksumFile
from rgd.utility import get_or_create_no_commit
from rgd_3d.models import GRIB, PointCloud, PointCloudMeta

logger = get_task_logger(__name__)


def _file_conversion_helper(source, output_field, method, prefix='', extension='', **kwargs):
    workdir = getattr(settings, 'GEODATA_WORKDIR', None)
    with tempfile.TemporaryDirectory(dir=workdir) as tmpdir:
        with source.yield_local_path() as file_path:
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
        pc_file = PointCloud.objects.get(id=pc_file)
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
    if not pc_entry.vtp_data.collection:
        pc_entry.vtp_data.collection = pc_file.file.collection
    _file_conversion_helper(pc_file.file, pc_entry.vtp_data.file, method, extension='.vtp')
    # Save the record
    pc_entry.save()


def read_grib_file(grib):
    import pygrib
    import pyvista

    if not isinstance(grib, GRIB):
        grib = GRIB.objects.get(id=grib)

    with grib.file.yield_local_path() as file_path:
        grbs = pygrib.open(str(file_path))

        # Loop through data and collect vars and levels information
        data_vars = {}
        list_of_vars = grbs.select()
        for i in range(len(list_of_vars)):
            d = grbs.select()[i]
            if data_vars.get(d.name) is None:
                data_vars[d.name] = []
            data_vars[d.name].insert(len(data_vars[d.name]), d.level)

        # Verify that every dataset in the file has the same size - thus there is a single underlying mesh in the XY plane
        shapes = set()
        for dl in grbs.select():
            shapes.add(dl.values.shape)
        assert len(shapes) == 1
        nx, ny = list(shapes)[0]
        nz = max([len(e) for e in data_vars.values()])
        vol = pyvista.UniformGrid((nx, ny, nz))

        for name in data_vars.keys():
            levels = grbs.select(name=name)
            level = levels.pop(0)
            data = level.values[:, :, np.newaxis]
            for level in levels:
                data = np.dstack((data, level.values[:, :, np.newaxis]))
            temp = np.empty((nx, ny, nz))
            temp[:] = np.nan
            temp[:, :, 0 : data.shape[2]] = data
            vol[name] = temp.ravel(order='F')

    if not grib.vti_data:
        grib.vti_data = ChecksumFile()

    if not grib.vti_data.collection:
        grib.vti_data.collection = grib.file.collection

    workdir = getattr(settings, 'GEODATA_WORKDIR', None)
    with tempfile.TemporaryDirectory(dir=workdir) as tmpdir:
        output_path = os.path.join(tmpdir, os.path.basename(grib.file.name) + '.vti')
        vol.save(output_path)
        with open(output_path, 'rb') as f:
            grib.vti_data.file.save(os.path.basename(output_path), f)

    grib.save(
        update_fields=[
            'vti_data',
        ]
    )
