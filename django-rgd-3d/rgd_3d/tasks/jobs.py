from celery import shared_task
from rgd.tasks import helpers


@shared_task(time_limit=86400)
def task_read_point_cloud_file(pc_file_id):
    from rgd_3d.models import PointCloud

    from .etl import read_point_cloud_file

    pc_file = PointCloud.objects.get(id=pc_file_id)
    helpers._run_with_failure_reason(pc_file, read_point_cloud_file, pc_file_id)


@shared_task(time_limit=86400)
def task_read_grib_file(grib):
    from rgd_3d.models import GRIB

    from .etl import read_grib_file

    grib_file = GRIB.objects.get(id=grib)
    helpers._run_with_failure_reason(grib_file, read_grib_file, grib)
