from celery import shared_task
from rgd.tasks import helpers


@shared_task(time_limit=86400)
def task_load_image(file_pk):
    from rgd_imagery.models import Image
    from rgd_imagery.tasks.etl import load_image

    image_file = Image.objects.get(pk=file_pk)
    helpers._run_with_failure_reason(image_file, load_image, file_pk)


@shared_task(time_limit=86400)
def task_populate_raster(raster_pk):
    from rgd_imagery.models import Raster
    from rgd_imagery.tasks.etl import populate_raster

    raster = Raster.objects.get(pk=raster_pk)
    helpers._run_with_failure_reason(raster, populate_raster, raster_pk)


@shared_task(time_limit=86400)
def task_populate_raster_footprint(raster_pk):
    from rgd_imagery.models import Raster
    from rgd_imagery.tasks.etl import populate_raster_footprint

    raster = Raster.objects.get(pk=raster_pk)
    helpers._run_with_failure_reason(raster, populate_raster_footprint, raster_pk)


@shared_task(time_limit=86400)
def task_populate_raster_outline(raster_pk):
    from rgd_imagery.models import Raster
    from rgd_imagery.tasks.etl import populate_raster_outline

    raster = Raster.objects.get(pk=raster_pk)
    helpers._run_with_failure_reason(raster, populate_raster_outline, raster_pk)


@shared_task(time_limit=86400)
def task_run_processed_image(processed_pk):
    from rgd_imagery.models import ProcessedImage
    from rgd_imagery.tasks.subsample import run_processed_image

    obj = ProcessedImage.objects.get(pk=processed_pk)
    helpers._run_with_failure_reason(obj, run_processed_image, processed_pk)
