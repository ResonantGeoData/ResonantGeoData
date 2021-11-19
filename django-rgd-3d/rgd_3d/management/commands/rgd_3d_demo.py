from rgd.management.commands._data_helper import SynchronousTasksCommand, _get_or_create_file_model
from rgd_3d import models

SUCCESS_MSG = 'Finished loading all demo data.'

# Names of files in the datastore
POINT_CLOUD_FILES = [
    'topo.vtk',
]


def load_mesh_3d_files(pc_files):
    ids = []
    for f in pc_files:
        entry = _get_or_create_file_model(models.Mesh3D, f)
        ids.append(entry.pk)
    return ids


class Command(SynchronousTasksCommand):
    help = 'Populate database with demo data.'

    def handle(self, *args, **options):

        self.set_synchronous()
        # Run the command
        load_mesh_3d_files(POINT_CLOUD_FILES)

        self.stdout.write(self.style.SUCCESS(SUCCESS_MSG))
        self.reset_celery()
