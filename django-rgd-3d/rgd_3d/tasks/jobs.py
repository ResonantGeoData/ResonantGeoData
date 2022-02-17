from celery import shared_task
from django.conf import settings
from rgd.tasks import helpers


@shared_task(time_limit=settings.CELERY_TASK_TIME_LIMIT)
def task_read_mesh_3d_file(pc_file_pk):
    from rgd_3d.models import Mesh3D

    from .etl import read_mesh_3d_file

    pc_file = Mesh3D.objects.get(pk=pc_file_pk)
    helpers._run_with_failure_reason(pc_file, read_mesh_3d_file, pc_file_pk)


@shared_task(time_limit=settings.CELERY_TASK_TIME_LIMIT)
def task_read_3d_tiles_file(tiles_3d_pk: int):
    from rgd_3d.models import Tiles3D

    from .etl import read_3d_tiles_tileset_json

    tiles_3d = Tiles3D.objects.get(pk=tiles_3d_pk)
    helpers._run_with_failure_reason(tiles_3d, read_3d_tiles_tileset_json, tiles_3d_pk)
