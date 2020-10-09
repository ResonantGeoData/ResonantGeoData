from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from rgd.utility import _link_url

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
    Thumbnail,
)
from .models.imagery.ifiles import BaseImageFile, ImageArchiveFile, ImageFile

SPATIAL_ENTRY_FILTERS = (
    'acquisition_date',
    'modified',
)


@admin.register(ArbitraryFile)
class ArbitraryFileAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
    )


@admin.register(KWCOCOArchive)
class KWCOCOArchiveAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
    )
    readonly_fields = ('image_set',)


@admin.register(ImageSet)
class ImageSetAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
        'count',
    )


@admin.register(ImageEntry)
class ImageEntryAdmin(OSMGeoAdmin):
    list_display = (
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
    )  # 'thumbnail')
    list_filter = ('instrumentation', 'number_of_bands', 'driver')


@admin.register(RasterEntry)
class RasterEntryAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
        'status',
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
        'failure_reason',
    )  # 'thumbnail')
    list_filter = SPATIAL_ENTRY_FILTERS + ('crs',)
    modifiable = False  # To still show the footprint and outline

    def status(self, obj):
        return not obj.failure_reason

    status.boolean = True


@admin.register(BandMetaEntry)
class BandMetaEntryAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'parent_image',
        'modified',
        # 'parent_image',  # TODO: this prevents the list view from working
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
    )
    list_filter = (
        'parent_image',
        'interpretation',
        'dtype',
    )


@admin.register(Segmentation)
class SegmentationAdmin(OSMGeoAdmin):
    list_display = ('id',)
    readonly_fields = ('outline',)


@admin.register(PolygonSegmentation)
class PolygonSegmentationAdmin(OSMGeoAdmin):
    list_display = ('id',)
    readonly_fields = (
        'outline',
        'feature',
    )


@admin.register(RLESegmentation)
class RLESegmentationAdmin(OSMGeoAdmin):
    list_display = ('id',)
    readonly_fields = ('outline', 'width', 'height', 'blob')


@admin.register(Annotation)
class AnnotationAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'caption',
    )


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
    readonly_fields = ('failure_reason', 'modified', 'created', 'checksum', 'last_validation')

    def status(self, obj):
        return not obj.failure_reason

    status.boolean = True


@admin.register(Thumbnail)
class ThumbnailAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'image_entry',
    )
    fields = ('image_tag',)
    readonly_fields = ('image_tag',)


@admin.register(ConvertedImageFile)
class ConvertedImageFileAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
        'source_image',
        'status',
        'modified',
    )
    readonly_fields = (
        'failure_reason',
        'file',
    )

    def status(self, obj):
        return not obj.failure_reason

    status.boolean = True


@admin.register(GeometryEntry)
class GeometryEntryAdmin(OSMGeoAdmin):
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
        'failure_reason',
        'modified',
        'created',
        'last_validation',
        'checksum',
    )

    def status(self, obj):
        return not obj.failure_reason

    status.boolean = True


@admin.register(FMVFile)
class FMVFileAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
        'status',
        'modified',
        'fmv_data_link',
    )
    readonly_fields = ('failure_reason', 'modified', 'created', 'checksum', 'last_validation')

    def status(self, obj):
        return not obj.failure_reason

    status.boolean = True


@admin.register(FMVEntry)
class FMVEntryAdmin(OSMGeoAdmin):
    list_display = ('id', 'name', 'klv_data_link')

    readonly_fields = ('modified', 'created', 'klv_file', 'fmv_file')
