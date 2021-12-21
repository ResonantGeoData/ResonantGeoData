from pathlib import Path
from typing import List

from pooch.processors import Unzip
from rgd.datastore import datastore
from rgd.management.commands._data_helper import (
    SynchronousTasksCommand,
    _get_or_create_checksum_file,
    _get_or_create_file_model,
)
from rgd.models import FileSet
from rgd_3d import models

SUCCESS_MSG = 'Finished loading all demo data.'

# Names of files in the datastore
POINT_CLOUD_FILES = ['topo.vtk']
TILES_3D_FILES = ['jacksonville.zip', 'dragon.zip']


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

        # Start by ingesting tileset.json
        tileset_json_path = Path(
            [path for path in paths if path.split('/')[-1] == 'tileset.json'][0]
        )
        tileset_json_name = '/'.join(str(tileset_json_path).split('/')[-2:])
        dataset_name = str(tileset_json_path.relative_to(datastore.path)).split('/')[-2]

        # Create a FileSet for the 3D tiles dataset
        fileset, created = FileSet.objects.get_or_create(name=dataset_name)

        tileset_json_checksum_file = _get_or_create_checksum_file(
            tileset_json_path, tileset_json_name
        )
        tileset_json_checksum_file.file_set = fileset
        tileset_json_checksum_file.save(update_fields=['file_set'])

        # Filter out tileset.json as we have already ingested that
        paths = [path for path in paths if path.split('/')[-1] != 'tileset.json']

        for path in paths:
            # Strip off irrelevant parts of file path
            file_name = '/'.join(str(Path(path).relative_to(datastore.path)).split('/')[1:])
            checksum_file = _get_or_create_checksum_file(path, file_name)
            checksum_file.file_set = fileset
            checksum_file.save(update_fields=['file_set'])

        entry, created = models.Tiles3D.objects.get_or_create(
            name=dataset_name, json_file=tileset_json_checksum_file
        )
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
