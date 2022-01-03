from django.contrib import admin

# from django.contrib.admin import SimpleListFilter
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.admin.mixins import (
    MODIFIABLE_FILTERS,
    SPATIAL_ENTRY_FILTERS,
    TASK_EVENT_FILTERS,
    TASK_EVENT_READONLY,
    GeoAdminInline,
    _FileGetNameMixin,
    reprocess,
)
from rgd_imagery.models import BandMeta, Image, ImageMeta, ImageSet, ImageSetSpatial, Raster


def _make_image_set_from_images(images):
    """Images should be an iterable, not a queryset."""
    imset = ImageSet()
    imset.save()  # Have to save before adding to ManyToManyField?
    for image in images:
        imset.images.add(image)
    imset.save()
    return imset


def make_image_set_from_images(modeladmin, request, queryset):
    """Make an `ImageSet` of the selected `ImageMeta`s.

    This is an action on `ImageMeta`.
    """
    return _make_image_set_from_images(queryset.all())


def _make_raster_from_image_set(imset):
    raster = Raster()
    raster.image_set = imset
    raster.save()
    return raster


def make_raster_from_images(modeladmin, request, queryset):
    """Make a raster of the selected `ImageMeta`s.

    This is an action on `ImageMeta`
    """
    imset = make_image_set_from_images(modeladmin, request, queryset)
    return _make_raster_from_image_set(imset)


def make_raster_from_image_set(modeladmin, request, queryset):
    """Make a raster of the selected `ImageSet`.

    This is an action on `ImageSet`.
    """
    rasters = []
    for imset in queryset.all():
        rasters.append(_make_raster_from_image_set(imset))
    return rasters


def make_raster_for_each_image(modeladmin, request, queryset):
    """Make a raster for each of the selected `ImageMeta`s.

    This is an action on `ImageMeta`.

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
    q = queryset.filter(images=None)
    q.delete()


# class ImageSetSpatialFilter(SimpleListFilter):
#     title = 'Spatial'
#     parameter_name = 'imagesetspatial'
#
#     def lookups(self, request, model_admin):
#         return [True, False]
#
#     def queryset(self, request, queryset):
#         if not self.value():
#             return queryset.filter(imagesetspatial__isnull=True)
#         if self.value():
#             return queryset.filter(imagesetspatial__isnull=False)


class ImageSetSpatialInline(GeoAdminInline):
    model = ImageSetSpatial
    fk_name = 'image_set'
    list_display = (
        'pk',
        'modified',
        'created',
    )
    list_filter = MODIFIABLE_FILTERS + SPATIAL_ENTRY_FILTERS


@admin.register(ImageSet)
class ImageSetAdmin(OSMGeoAdmin):
    list_display = (
        'pk',
        'name',
        'count',
        'number_of_bands',
        'modified',
        'created',
    )
    actions = (
        make_raster_from_image_set,
        clean_empty_image_sets,
    )
    list_filter = MODIFIABLE_FILTERS  # (ImageSetSpatialFilter, )
    inlines = (ImageSetSpatialInline,)
    raw_id_fields = ('images',)


class BandMetaInline(admin.StackedInline):
    model = BandMeta
    fk_name = 'parent_image'

    list_display = (
        'pk',
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
        'band_number',
    )

    def has_add_permission(self, request, obj=None):
        """Prevent user from adding more."""
        return False


class ImageMetaInline(admin.StackedInline):
    model = ImageMeta
    fk_name = 'parent_image'
    list_display = (
        'pk',
        'modified',
        'created',
    )
    readonly_fields = (
        'parent_image',
        'height',
        'width',
        'driver',
        'modified',
        'created',
    )
    list_filter = MODIFIABLE_FILTERS + ('driver',)


@admin.register(Image)
class ImageAdmin(OSMGeoAdmin, _FileGetNameMixin):
    list_display = (
        'pk',
        'get_name',
        'number_of_bands',
        'status',
        'modified',
        'created',
        'image_data_link',
    )
    readonly_fields = (
        'modified',
        'created',
    ) + TASK_EVENT_READONLY
    actions = (
        reprocess,
        make_image_set_from_images,
        make_raster_from_images,
        make_raster_for_each_image,
    )
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS
    inlines = (
        ImageMetaInline,
        BandMetaInline,
    )
    raw_id_fields = ('file',)
