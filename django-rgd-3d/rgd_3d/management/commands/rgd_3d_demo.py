from typing import List

from pooch.processors import Unzip
from rgd.datastore import datastore
from rgd.management.commands._data_helper import SynchronousTasksCommand, _get_or_create_file_model
from rgd_3d import models
from rgd_3d.models.tiles import create_tiles3d_from_paths

SUCCESS_MSG = 'Finished loading all demo data.'

# Names of files in the datastore
POINT_CLOUD_FILES = ['topo.vtk']
TILES_3D_FILES = ['jacksonville-untextured.zip', 'jacksonville-textured.zip', 'dragon.zip']


def load_mesh_3d_files(pc_files: List[str]):
    ids = []
    for f in pc_files:
        entry = _get_or_create_file_model(models.Mesh3D, f)
        ids.append(entry.pk)
    return ids


def load_tiles_3d_files(t3d_files: List[str]):
    ids = []
    for f in t3d_files:
        paths = datastore.fetch(f, processor=Unzip())
        entry = create_tiles3d_from_paths(paths)
        ids.append(entry.pk)
    return ids


class Command(SynchronousTasksCommand):
    help = 'Populate database with demo data.'

    def handle(self, *args, **options):

        self.set_synchronous()
        # Run the command
        load_mesh_3d_files(POINT_CLOUD_FILES)

        load_tiles_3d_files(TILES_3D_FILES)

        self.stdout.write(self.style.SUCCESS(SUCCESS_MSG))
        self.reset_celery()
