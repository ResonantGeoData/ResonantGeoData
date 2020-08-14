from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from rgd.utility import _link_url
from .models.common import ArbitraryFile
from .models.geometry.base import GeometryArchive, GeometryEntry
from .models.imagery.annotation import Annotation, Segmentation
from .models.imagery.base import (
    BandMetaEntry,
    ConvertedImageFile,
    KWCOCODataset,
    ImageEntry,
    ImageSet,
    RasterEntry,
)
from .models.imagery.ifiles import ImageFile


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


@admin.register(KWCOCODataset)
class KWCOCODatasetAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
    )


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


@admin.register(Annotation)
class AnnotationAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'caption',
    )


@admin.register(ImageFile)
class ImageFileAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
        'status',
        'modified',
        'data_link',
    )
    readonly_fields = ('failure_reason', 'modified', 'created', 'checksum', 'last_validation')

    def data_link(self, obj):
        return _link_url('geodata', 'image_file', obj, 'file')

    data_link.allow_tags = True

    def status(self, obj):
        return not obj.failure_reason

    status.boolean = True


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
        'data_link',
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

    def data_link(self, obj):
        return _link_url('geodata', 'geometry_archive', obj, 'file')

    data_link.allow_tags = True
