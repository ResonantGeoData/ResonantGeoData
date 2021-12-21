import json
import os
import tempfile
from typing import Union

from celery.utils.log import get_task_logger
from django.contrib.gis.geos import Polygon
import numpy as np
import pyproj
from rgd.models import DB_SRID, ChecksumFile
from rgd.utility import get_or_create_no_commit, get_temp_dir
from rgd_3d.models import Mesh3D, Tiles3D, Tiles3DMeta
from shapely import affinity
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.ops import transform as shapely_transform

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
    tileset_json = json.load(tiles_3d.json_file.file)

    tiles_3d_meta, created = get_or_create_no_commit(Tiles3DMeta, source=tiles_3d)

    volume = tileset_json['root']['boundingVolume']
    logger.debug(f'3D tiles bounding volume: {volume}')

    # The coordinates should be in EPSG:4978 by convention in 3D Tiles
    # See https://github.com/CesiumGS/3d-tiles/tree/main/specification#coordinate-reference-system-crs
    srid = 4978
    if 'region' in volume:
        xmin, ymin, xmax, ymax, _, _ = volume['region']
        # The region bounding volume specifies bounds using a geographic coordinate system (latitude, longitude, height), specifically EPSG 4979.
        # See https://github.com/CesiumGS/3d-tiles/tree/main/specification#coordinate-reference-system-crs
        srid = 4979
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

    coords = np.array(
        [
            (xmin, ymax),
            (xmax, ymax),
            (xmax, ymin),
            (xmin, ymin),
            (xmin, ymax),  # Close the loop
        ]
    )

    if 'transform' in tileset_json['root']:
        # Apply transform if required
        transform = tileset_json['root']['transform']
        # The transform is stored in column-major order in the JSON, so reorder
        # to produce the  full 3D Affine matrix in the form of:
        #      [x']    / a  b  c xoff \ [x]
        #      [y'] =  | d  e  f yoff | [y]
        #      [z']    | g  h  i zoff | [z]
        #      [1 ]    \ 0  0  0   1  / [1]
        t = np.array(transform).reshape((4, 4), order='F')
        # But we want the 2D subcomponent which would be:
        #      [x']    / a  b xoff \ [x]
        #      [y'] =  | d  e yoff | [y]
        #      [1 ]    \ 0  0   1  / [1]
        # This would effectively be: np.hstack((t[0:2,0:2], t[0:2,-1,None]))
        # but, shapely expects the following form as a 1D array:
        #           [a, b, d, e, xoff, yoff]
        affine = np.append(t[0:2, 0:2].ravel(), t[0:2, -1])
        # Use shapely to apply the affine tranformation
        transformed = affinity.affine_transform(ShapelyPolygon(coords).exterior, affine)
        coords = np.array(transformed.coords)

    # Transform from 3DTiles SRID to Database SRID
    # Convert the coordinates using pyproj to database SRID from source SRID
    # This might work on proj>=8 and pyproj>=3.1 - large_image_wheels gives us these versions
    src = pyproj.CRS(f'EPSG:{srid}')
    dest = pyproj.CRS(f'EPSG:{DB_SRID}')
    project = pyproj.Transformer.from_crs(src, dest, always_xy=True).transform
    result = shapely_transform(project, ShapelyPolygon(coords))
    logger.info(f'the coords: {list(result.exterior.coords)}')

    outline = Polygon(list(result.exterior.coords), srid=DB_SRID)

    # Save out
    tiles_3d_meta.outline = outline
    tiles_3d_meta.footprint = outline  # TODO: handle oriented bounding boxes

    tiles_3d_meta.save()
