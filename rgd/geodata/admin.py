from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from . import actions
from .models.common import ArbitraryFile
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
    ImageSet,
    KWCOCOArchive,
    RasterEntry,
    RasterMetaEntry,
    SubsampledImage,
    Thumbnail,
)
from .models.imagery.ifiles import BaseImageFile, ImageArchiveFile, ImageFile

SPATIAL_ENTRY_FILTERS = (
    'acquisition_date',
    'modified',
)

TASK_EVENT_READONLY = (
    'failure_reason',
    'status',
)


@admin.register(ArbitraryFile)
class ArbitraryFileAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
    )
    readonly_fields = ('checksum',)


@admin.register(KWCOCOArchive)
class KWCOCOArchiveAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
        'status',
    )
    readonly_fields = ('image_set',) + TASK_EVENT_READONLY


@admin.register(ImageSet)
class ImageSetAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
        'count',
    )
    actions = (actions.make_raster_from_image_set,)


class ThumbnailInline(admin.TabularInline):
    model = Thumbnail
    fk_name = 'image_entry'
    list_display = (
        'id',
        'image_entry',
    )
    fields = ('image_tag',)
    readonly_fields = ('image_tag',)

    def has_add_permission(self, request, obj=None):
        """Prevent user from adding more."""
        return False


class BandMetaEntryInline(admin.StackedInline):
    model = BandMetaEntry
    fk_name = 'parent_image'

    list_display = (
        'id',
        'parent_image',
        'modified',
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
        'icon_tag',
        'id',
        'name',
        'image_file',
        'modified',
    )
    readonly_fields = (
        'number_of_bands',
        'image_file',
        'height',
        'width',
        'driver',
        'metadata',
        'modified',
        'created',
    )
    list_filter = ('instrumentation', 'number_of_bands', 'driver')
    actions = (
        actions.make_image_set_from_image_entries,
        actions.make_raster_from_image_entries,
        actions.make_raster_for_each_image_entry,
    )
    inlines = (ThumbnailInline, BandMetaEntryInline)


class RasterMetaEntryInline(admin.StackedInline):
    model = RasterMetaEntry
    fk_name = 'parent_raster'
    list_display = (
        'id',
        'modified',
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
    )
    readonly_fields = (
        'modified',
        'created',
    ) + TASK_EVENT_READONLY
    inlines = (RasterMetaEntryInline,)
    actions = (actions.reprocess_raster_entries,)


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
    )
    readonly_fields = (
        'keypoints',
        'line',
    )
    inlines = (SegmentationInline, PolygonSegmentationInline, RLESegmentationInline)


@admin.register(BaseImageFile)
class BaseImageFileAdmin(OSMGeoAdmin):
    list_display = ('image_file_id',)


@admin.register(ImageArchiveFile)
class ImageArchiveFileAdmin(OSMGeoAdmin):
    list_display = ('image_file_id',)


@admin.register(ImageFile)
class ImageFileAdmin(OSMGeoAdmin):
    list_display = (
        'image_file_id',
        'name',
        'status',
        'modified',
        'image_data_link',
    )
    readonly_fields = ('modified', 'created', 'checksum', 'last_validation') + TASK_EVENT_READONLY
    actions = (actions.reprocess_image_files,)


@admin.register(ConvertedImageFile)
class ConvertedImageFileAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'source_image',
        'status',
        'modified',
    )
    readonly_fields = ('converted_file',) + TASK_EVENT_READONLY


@admin.register(SubsampledImage)
class SubsampledImageAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'source_image',
        'sample_type',
        'status',
        'modified',
    )
    readonly_fields = ('data',) + TASK_EVENT_READONLY


class GeometryEntryInline(admin.StackedInline):
    model = GeometryEntry
    fk_name = 'geometry_archive'
    list_display = (
        'id',
        'name',
        'geometry_archive',
        'modified',
    )
    list_filter = SPATIAL_ENTRY_FILTERS
    readonly_fields = (
        'modified',
        'created',
        'geometry_archive',
    )
    modifiable = False  # To still show the footprint and outline


@admin.register(GeometryArchive)
class GeometryArchiveAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
        'status',
        'modified',
        'archive_data_link',
    )
    readonly_fields = (
        'modified',
        'created',
        'last_validation',
        'checksum',
    ) + TASK_EVENT_READONLY
    inlines = (GeometryEntryInline,)


class FMVEntryInline(admin.StackedInline):
    model = FMVEntry
    fk_name = 'fmv_file'
    list_display = ('id', 'name', 'fmv_file')
    readonly_fields = (
        'modified',
        'created',
    )


@admin.register(FMVFile)
class FMVFileAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
        'status',
        'modified',
        'fmv_data_link',
        'klv_data_link',
    )
    readonly_fields = (
        'modified',
        'created',
        'checksum',
        'last_validation',
        'klv_file',
        'web_video_file',
        'frame_rate',
    ) + TASK_EVENT_READONLY
    inlines = (FMVEntryInline,)
