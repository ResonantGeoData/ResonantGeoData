from . import tasks
from .models.imagery import ImageFile, ImageSet, RasterEntry


def _make_image_set_from_images(images):
    """Images should be an iterable, not a queryset."""
    imset = ImageSet()
    imset.save()  # Have to save before adding to ManyToManyField?
    for image in images:
        imset.images.add(image)
    imset.save()
    return imset


def make_image_files(modeladmin, request, queryset):
    """Make ImageFile from ChecksumFile."""
    for file in queryset.all():
        ImageFile.objects.get_or_create(file=file)


def make_image_set_from_image_entries(modeladmin, request, queryset):
    """Make an `ImageSet` of the selected `ImageEntry`s.

    This is an action on `ImageEntry`.
    """
    return _make_image_set_from_images(queryset.all())


def _make_raster_from_image_set(imset):
    raster = RasterEntry()
    raster.image_set = imset
    raster.save()
    return raster


def make_raster_from_image_entries(modeladmin, request, queryset):
    """Make a raster of the selected `ImageEntry`s.

    This is an action on `ImageEntry`
    """
    imset = make_image_set_from_image_entries(modeladmin, request, queryset)
    return _make_raster_from_image_set(imset)


def make_raster_from_image_set(modeladmin, request, queryset):
    """Make a raster of the selected `ImageSet`.

    This is an action on `ImageSet`.
    """
    rasters = []
    for imset in queryset.all():
        rasters.append(_make_raster_from_image_set(imset))
    return rasters


def make_raster_for_each_image_entry(modeladmin, request, queryset):
    """Make a raster for each of the selected `ImageEntry`s.

    This is an action on `ImageEntry`.

    This creates one raster for each image entry.
    """
    rasters = []
    for img in queryset.all():
        imset = _make_image_set_from_images(
            [
                img,
            ]
        )
        rasters.append(_make_raster_from_image_set(imset))
    return rasters


def reprocess(modeladmin, request, queryset):
    """Trigger the save event task for each entry."""
    for entry in queryset.all():
        entry.save()


def generate_valid_data_footprint(modeladmin, request, queryset):
    """Generate a valid data footprint for each raster."""
    for rast in queryset.all():
        tasks.task_populate_raster_footprint.delay(rast.id)


def clean_empty_image_sets(modeladmin, request, queryset):
    """Delete empty `ImageSet`s."""
    for imset in queryset.all():
        if len(imset.images) < 1:
            imset.delete()


def clean_empty_rasters(modeladmin, request, queryset):
    """Delete if associated `ImageSet` is empty."""
    for raster in queryset.all():
        if len(raster.image_set.images) < 1:
            raster.image_set.delete()
