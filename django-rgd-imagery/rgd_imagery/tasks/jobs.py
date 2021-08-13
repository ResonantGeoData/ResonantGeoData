from celery import shared_task
from rgd.tasks import helpers


@shared_task(time_limit=86400)
def task_load_image(file_id):
    from rgd_imagery.models import Image
    from rgd_imagery.tasks.etl import load_image

    image_file = Image.objects.get(id=file_id)
    helpers._run_with_failure_reason(image_file, load_image, file_id)


@shared_task(time_limit=86400)
def task_populate_raster(raster_id):
    from rgd_imagery.models import Raster
    from rgd_imagery.tasks.etl import populate_raster

    raster = Raster.objects.get(id=raster_id)
    helpers._run_with_failure_reason(raster, populate_raster, raster_id)


@shared_task(time_limit=86400)
def task_populate_raster_footprint(raster_id):
    from rgd_imagery.models import Raster
    from rgd_imagery.tasks.etl import populate_raster_footprint

    raster = Raster.objects.get(id=raster_id)
    helpers._run_with_failure_reason(raster, populate_raster_footprint, raster_id)


@shared_task(time_limit=86400)
def task_populate_raster_outline(raster_id):
    from rgd_imagery.models import Raster
    from rgd_imagery.tasks.etl import populate_raster_outline

    raster = Raster.objects.get(id=raster_id)
    helpers._run_with_failure_reason(raster, populate_raster_outline, raster_id)


@shared_task(time_limit=86400)
def task_load_kwcoco_dataset(kwcoco_dataset_id):
    from rgd_imagery.models import KWCOCOArchive
    from rgd_imagery.tasks.kwcoco_etl import load_kwcoco_dataset

    ds_entry = KWCOCOArchive.objects.get(id=kwcoco_dataset_id)
    helpers._run_with_failure_reason(ds_entry, load_kwcoco_dataset, kwcoco_dataset_id)


@shared_task(time_limit=86400)
def task_run_processed_image(conv_id):
    from rgd_imagery.models import ProcessedImage
    from rgd_imagery.tasks.subsample import run_processed_image

    obj = ProcessedImage.objects.get(id=conv_id)
    helpers._run_with_failure_reason(obj, run_processed_image, conv_id)
