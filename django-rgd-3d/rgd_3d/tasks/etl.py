import json
import os
import tempfile
from typing import Union

from celery.utils.log import get_task_logger
from django.contrib.gis.geos import Polygon
from rgd.models import ChecksumFile
from rgd.models.transform import transform_geometry
from rgd.utility import get_or_create_no_commit, get_temp_dir
from rgd_3d.models import Mesh3D, Tiles3D, Tiles3DMeta
from shapely import affinity
from shapely.geometry import Polygon as ShapelyPolygon

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


def read_mesh_3d_file(mesh_3d: Union[Mesh3D, int]):
    """Read a Mesh3D object and populate the vtp_data field."""
    if not isinstance(mesh_3d, Mesh3D):
        mesh_3d = Mesh3D.objects.get(pk=mesh_3d)
    if not mesh_3d.name:
        mesh_3d.name = mesh_3d.file.name
    # Parse the point cloud file format and convert
    ext = mesh_3d.file.name.split('.')[-1].strip().lower()
    try:
        method = _get_readers()[ext]
    except KeyError:
        raise ValueError(f'Extension `{ext}` unsupported for point cloud conversion.')
    if not mesh_3d.vtp_data:
        mesh_3d.vtp_data = ChecksumFile()
    if not mesh_3d.vtp_data.collection:
        mesh_3d.vtp_data.collection = mesh_3d.file.collection
    _file_conversion_helper(mesh_3d.file, mesh_3d.vtp_data.file, method, extension='.vtp')
    # Save the record
    mesh_3d.save(
        update_fields=[
            'name',
            'vtp_data',
        ]
    )


def read_3d_tiles_tileset_json(tiles_3d: Union[Tiles3D, int]):
    if not isinstance(tiles_3d, Tiles3D):
        tiles_3d = Tiles3D.objects.get(pk=tiles_3d)
    with tiles_3d.json_file.yield_local_path() as path:
        with open(path, 'r') as f:
            tileset_json = json.load(f)

    tiles_3d_meta, created = get_or_create_no_commit(Tiles3DMeta, source=tiles_3d)

    volume = tileset_json['root']['boundingVolume']
    logger.debug(f'3D tiles bounding volume: {volume}')

    if 'region' in volume:
        xmin, ymin, xmax, ymax, _, _ = volume['region']
    elif 'box' in volume:
        b = volume['box']
        center, x, y = b[0:3], b[3:6], b[6:9]
        xmin = min(center[0], x[0], y[0])
        xmax = max(center[0], x[0], y[0])
        ymin = min(center[1], x[1], y[1])
        ymax = max(center[1], x[1], y[1])
        # TODO: for the oriented bounding box, use it as the `footprint` field
    elif 'sphere' in volume:
        raise NotImplementedError
    else:
        raise ValueError(f'Bounding volume of unknown type: {volume}')

    coords = [
        (xmin, ymax),
        (xmax, ymax),
        (xmax, ymin),
        (xmin, ymin),
        (xmin, ymax),  # Close the loop
    ]

    if 'transform' in tileset_json['root']:
        # Apply transform if required
        # TODO: this isn't correct.... having trouble debugging the transform
        transform = tileset_json['root']['transform'][:-4]  # ignore last 4 (z component)
        logger.info(f'Bounding volume transform: {transform}')
        trans = affinity.affine_transform(ShapelyPolygon(coords), transform)
        outline = Polygon(list(trans.exterior.coords))
        logger.info(list(trans.exterior.coords))
    else:
        # 3D tiles documentation states that these are always in EPSG:4929
        outline = transform_geometry(Polygon(coords), 'EPSG:4929')

    tiles_3d_meta.outline = outline
    tiles_3d_meta.footprint = outline  # TODO: handle oriented bounding boxes

    tiles_3d_meta.save()
