from celery import shared_task
from rgd.tasks import helpers


@shared_task(time_limit=86400)
def task_read_point_cloud_file(pc_file_pk):
    from rgd_3d.models import PointCloud

    from .etl import read_point_cloud_file

    pc_file = PointCloud.objects.get(pk=pc_file_pk)
    helpers._run_with_failure_reason(pc_file, read_point_cloud_file, pc_file_pk)
