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
def task_convert_to_cog(conv_id):
    from rgd_imagery.models import ConvertedImage
    from rgd_imagery.tasks.subsample import convert_to_cog

    cog = ConvertedImage.objects.get(id=conv_id)
    helpers._run_with_failure_reason(cog, convert_to_cog, conv_id)


@shared_task(time_limit=86400)
def task_populate_region_image(subsampled_id):
    from rgd_imagery.models import RegionImage
    from rgd_imagery.tasks.subsample import populate_region_image

    cog = RegionImage.objects.get(id=subsampled_id)
    helpers._run_with_failure_reason(cog, populate_region_image, subsampled_id)
