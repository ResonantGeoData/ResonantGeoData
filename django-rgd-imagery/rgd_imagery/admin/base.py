from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.admin.mixins import (
    MODIFIABLE_FILTERS,
    SPATIAL_ENTRY_FILTERS,
    TASK_EVENT_FILTERS,
    TASK_EVENT_READONLY,
    _FileGetNameMixin,
    reprocess,
)
from rgd.utility import get_or_create_no_commit
from rgd_imagery.models import (
    BandMetaEntry,
    ConvertedImageFile,
    ImageEntry,
    ImageFile,
    ImageSet,
    ImageSetSpatial,
    RasterEntry,
)


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


def clean_empty_image_sets(modeladmin, request, queryset):
    """Delete empty `ImageSet`s."""
    for imset in queryset.all():
        if len(imset.images) < 1:
            imset.delete()


def convert_images(modeladmin, request, queryset):
    for image in queryset.all():
        entry, created = get_or_create_no_commit(ConvertedImageFile, source_image=image)
        entry.save()


@admin.register(ImageSet)
class ImageSetAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
        'count',
        'modified',
        'created',
    )
    actions = (
        make_raster_from_image_set,
        clean_empty_image_sets,
    )
    list_filter = MODIFIABLE_FILTERS


@admin.register(ImageSetSpatial)
class ImageSetSpatialAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
        'modified',
        'created',
    )
    list_filter = MODIFIABLE_FILTERS + SPATIAL_ENTRY_FILTERS


class BandMetaEntryInline(admin.StackedInline):
    model = BandMetaEntry
    fk_name = 'parent_image'

    list_display = (
        'id',
        'parent_image',
        'modified',
        'created',
    )
    readonly_fields = (
        'mean',
        'max',
        'min',
        'modified',
        'created',
        'parent_image',
        'std',
        'nodata_value',
        'dtype',
        'band_number',
    )

    def has_add_permission(self, request, obj=None):
        """Prevent user from adding more."""
        return False


@admin.register(ImageEntry)
class ImageEntryAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
        'image_file',
        'modified',
        'created',
    )
    readonly_fields = (
        'number_of_bands',
        'image_file',
        'height',
        'width',
        'driver',
        'modified',
        'created',
    )
    list_filter = MODIFIABLE_FILTERS + (
        'number_of_bands',
        'driver',
    )
    actions = (
        make_image_set_from_image_entries,
        make_raster_from_image_entries,
        make_raster_for_each_image_entry,
        convert_images,
    )
    inlines = (BandMetaEntryInline,)


@admin.register(ImageFile)
class ImageFileAdmin(OSMGeoAdmin, _FileGetNameMixin):
    list_display = (
        'id',
        'get_name',
        'status',
        'modified',
        'created',
        'image_data_link',
    )
    readonly_fields = (
        'modified',
        'created',
    ) + TASK_EVENT_READONLY
    actions = (reprocess,)
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS
