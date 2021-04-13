from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from . import actions
from .models.collection import Collection, CollectionMembership
from .models.common import ChecksumFile
from .models.fmv.base import FMVEntry, FMVFile
from .models.geometry.base import GeometryArchive, GeometryEntry
from .models.imagery.annotation import (
    Annotation,
    PolygonSegmentation,
    RLESegmentation,
    Segmentation,
)
from .models.imagery.base import (
    BandMetaEntry,
    ConvertedImageFile,
    ImageEntry,
    ImageFile,
    ImageSet,
    KWCOCOArchive,
    RasterEntry,
    RasterMetaEntry,
    SubsampledImage,
)

SPATIAL_ENTRY_FILTERS = (
    'acquisition_date',
    'modified',
    'created',
)

TASK_EVENT_READONLY = (
    'failure_reason',
    'status',
)


class _FileGetNameMixin:
    def get_name(self, obj):
        return obj.file.name

    get_name.short_description = 'Name'
    get_name.admin_order_field = 'file__name'


@admin.register(ChecksumFile)
class ChecksumFileAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
        'status',
        'modified',
        'created',
        'type',
        'data_link',
        'collection',
    )
    readonly_fields = (
        'checksum',
        'last_validation',
    ) + TASK_EVENT_READONLY
    actions = (actions.reprocess, actions.make_image_files)


@admin.register(KWCOCOArchive)
class KWCOCOArchiveAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
        'status',
        'modified',
        'created',
    )
    readonly_fields = ('image_set',) + TASK_EVENT_READONLY
    actions = (actions.reprocess,)


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
        actions.make_raster_from_image_set,
        actions.clean_empty_image_sets,
    )


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
    list_filter = (
        'parent_image',
        'interpretation',
        'dtype',
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
    list_filter = ('instrumentation', 'number_of_bands', 'driver')
    actions = (
        actions.make_image_set_from_image_entries,
        actions.make_raster_from_image_entries,
        actions.make_raster_for_each_image_entry,
    )
    inlines = (BandMetaEntryInline,)


class RasterMetaEntryInline(admin.StackedInline):
    model = RasterMetaEntry
    fk_name = 'parent_raster'
    list_display = (
        'id',
        'modified',
        'created',
    )
    readonly_fields = (
        'crs',
        'origin',
        'extent',
        'resolution',
        'transform',
        'modified',
        'created',
        'parent_raster',
    )
    list_filter = SPATIAL_ENTRY_FILTERS + ('crs',)
    modifiable = False  # To still show the footprint and outline


@admin.register(RasterEntry)
class RasterEntryAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
        'status',
        'modified',
        'created',
    )
    readonly_fields = (
        'modified',
        'created',
    ) + TASK_EVENT_READONLY
    inlines = (RasterMetaEntryInline,)
    actions = (
        actions.reprocess,
        actions.generate_valid_data_footprint,
        actions.clean_empty_rasters,
    )


class SegmentationInline(admin.StackedInline):
    model = Segmentation
    fk_name = 'annotation'
    list_display = ('id',)
    readonly_fields = ('outline',)


class PolygonSegmentationInline(admin.StackedInline):
    model = PolygonSegmentation
    fk_name = 'annotation'
    list_display = ('id',)
    readonly_fields = (
        'outline',
        'feature',
    )


class RLESegmentationInline(admin.StackedInline):
    model = RLESegmentation
    fk_name = 'annotation'
    list_display = ('id',)
    readonly_fields = ('outline', 'width', 'height', 'blob')


@admin.register(Annotation)
class AnnotationAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'caption',
        'label',
        'annotator',
        'segmentation_type',
        'modified',
        'created',
    )
    readonly_fields = (
        'keypoints',
        'line',
    )
    inlines = (SegmentationInline, PolygonSegmentationInline, RLESegmentationInline)


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
    actions = (actions.reprocess,)


@admin.register(ConvertedImageFile)
class ConvertedImageFileAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'source_image',
        'status',
        'modified',
        'created',
    )
    readonly_fields = ('converted_file',) + TASK_EVENT_READONLY
    actions = (actions.reprocess,)


@admin.register(SubsampledImage)
class SubsampledImageAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'source_image',
        'sample_type',
        'status',
        'modified',
        'created',
    )
    readonly_fields = ('data',) + TASK_EVENT_READONLY
    actions = (actions.reprocess,)


class GeometryEntryInline(admin.StackedInline):
    model = GeometryEntry
    fk_name = 'geometry_archive'
    list_display = (
        'id',
        'name',
        'geometry_archive',
        'modified',
        'created',
    )
    list_filter = SPATIAL_ENTRY_FILTERS
    readonly_fields = (
        'modified',
        'created',
        'geometry_archive',
    )
    modifiable = False  # To still show the footprint and outline


@admin.register(GeometryArchive)
class GeometryArchiveAdmin(OSMGeoAdmin, _FileGetNameMixin):
    list_display = (
        'id',
        'get_name',
        'status',
        'modified',
        'created',
        'archive_data_link',
    )
    readonly_fields = (
        'modified',
        'created',
    ) + TASK_EVENT_READONLY
    inlines = (GeometryEntryInline,)
    actions = (actions.reprocess,)


class FMVEntryInline(admin.StackedInline):
    model = FMVEntry
    fk_name = 'fmv_file'
    list_display = (
        'id',
        'name',
        'fmv_file',
        'modified',
        'created',
    )
    readonly_fields = (
        'modified',
        'created',
    )


@admin.register(FMVFile)
class FMVFileAdmin(OSMGeoAdmin, _FileGetNameMixin):
    list_display = (
        'id',
        'get_name',
        'status',
        'modified',
        'created',
        'fmv_data_link',
        'klv_data_link',
    )
    readonly_fields = (
        'modified',
        'created',
        'klv_file',
        'web_video_file',
        'frame_rate',
    ) + TASK_EVENT_READONLY
    inlines = (FMVEntryInline,)
    actions = (actions.reprocess,)


class CollectionMembershipInline(admin.TabularInline):
    model = CollectionMembership
    fk_name = 'collection'
    fields = ('user', 'role')
    extra = 1


@admin.register(Collection)
class CollectionAdmin(OSMGeoAdmin):
    fields = ('name',)
    inlines = (CollectionMembershipInline,)
