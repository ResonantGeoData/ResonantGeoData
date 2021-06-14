from celery import shared_task
from rgd.tasks import helpers


@shared_task(time_limit=86400)
def task_read_image_file(file_id):
    from rgd_imagery.models import ImageFile
    from rgd_imagery.tasks.etl import read_image_file

    image_file = ImageFile.objects.get(id=file_id)
    helpers._run_with_failure_reason(image_file, read_image_file, file_id)


@shared_task(time_limit=86400)
def task_populate_raster_entry(raster_id):
    from rgd_imagery.models import RasterEntry
    from rgd_imagery.tasks.etl import populate_raster_entry

    raster_entry = RasterEntry.objects.get(id=raster_id)
    helpers._run_with_failure_reason(raster_entry, populate_raster_entry, raster_id)


@shared_task(time_limit=86400)
def task_populate_raster_footprint(raster_id):
    from rgd_imagery.models import RasterEntry
    from rgd_imagery.tasks.etl import populate_raster_footprint

    raster_entry = RasterEntry.objects.get(id=raster_id)
    helpers._run_with_failure_reason(raster_entry, populate_raster_footprint, raster_id)


@shared_task(time_limit=86400)
def task_populate_raster_outline(raster_id):
    from rgd_imagery.models import RasterEntry
    from rgd_imagery.tasks.etl import populate_raster_outline

    raster_entry = RasterEntry.objects.get(id=raster_id)
    helpers._run_with_failure_reason(raster_entry, populate_raster_outline, raster_id)


@shared_task(time_limit=86400)
def task_load_kwcoco_dataset(kwcoco_dataset_id):
    from rgd_imagery.models import KWCOCOArchive
    from rgd_imagery.tasks.kwcoco_etl import load_kwcoco_dataset

    ds_entry = KWCOCOArchive.objects.get(id=kwcoco_dataset_id)
    helpers._run_with_failure_reason(ds_entry, load_kwcoco_dataset, kwcoco_dataset_id)


@shared_task(time_limit=86400)
def task_convert_to_cog(conv_id):
    from rgd_imagery.models import ConvertedImageFile
    from rgd_imagery.tasks.subsample import convert_to_cog

    cog = ConvertedImageFile.objects.get(id=conv_id)
    helpers._run_with_failure_reason(cog, convert_to_cog, conv_id)


@shared_task(time_limit=86400)
def task_populate_subsampled_image(subsampled_id):
    from rgd_imagery.models import SubsampledImage
    from rgd_imagery.tasks.subsample import populate_subsampled_image

    cog = SubsampledImage.objects.get(id=subsampled_id)
    helpers._run_with_failure_reason(cog, populate_subsampled_image, subsampled_id)