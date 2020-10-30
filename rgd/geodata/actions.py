from .models.imagery import ImageSet, RasterEntry


def make_image_set(modeladmin, request, queryset):
    """Make a `ImageSet` of the selected `ImageEntry`s.

    This is an action on `ImageEntry`.
    """
    imset = ImageSet()
    imset.save()  # Have to save before adding to ManyToManyField?
    for image in queryset.all():
        imset.images.add(image)
    imset.save()
    return imset


def _make_raster_from_image_set(imset):
    raster = RasterEntry()
    raster.image_set = imset
    raster.save()
    return raster


def make_raster_from_image_entries(modeladmin, request, queryset):
    """Make a raster of the selected `ImageEntry`s.

    This is an action on `ImageEntry`
    """
    imset = make_image_set(modeladmin, request, queryset)
    return _make_raster_from_image_set(imset)


def make_raster_from_image_set(modeladmin, request, queryset):
    """Make a raster of the selected `ImageSet`.

    This is an action on `ImageSet`.
    """
    rasters = []
    for imset in queryset.all():
        rasters.append(_make_raster_from_image_set(imset))
    return rasters
