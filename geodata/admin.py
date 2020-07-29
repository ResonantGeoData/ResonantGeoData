from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from rgd.utility import _link_url
from .models.geometry.base import GeometryArchive, GeometryEntry
from .models.imagery.annotation import Annotation
from .models.imagery.base import (
    BandMetaEntry,
    ConvertedImageFile,
    ImageEntry,
    ImageSet,
    RasterEntry,
)
from .models.imagery.ifiles import ImageFile


SPATIAL_ENTRY_FILTERS = (
    'acquisition_date',
    'modified',
)


@admin.register(ImageSet)
class ImageSetAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
    )


@admin.register(ImageEntry)
class ImageEntryAdmin(OSMGeoAdmin):
    list_display = (
        '__str__',
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
        '__str__',
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


@admin.register(BandMetaEntry)
class BandMetaEntryAdmin(OSMGeoAdmin):
    list_display = (
        '__str__',
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


@admin.register(Annotation)
class AnnotationAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'caption',
    )


@admin.register(ImageFile)
class ImageFileAdmin(OSMGeoAdmin):
    list_display = (
        '__str__',
        'modified',
        'data_link',
    )
    readonly_fields = ('failure_reason', 'modified', 'created', 'checksum', 'last_validation')

    def data_link(self, obj):
        return _link_url('geodata', 'image_file', obj, 'image_file')

    data_link.allow_tags = True


@admin.register(ConvertedImageFile)
class ConvertedImageFileAdmin(OSMGeoAdmin):
    list_display = (
        '__str__',
        'modified',
        'source_image',
    )
    readonly_fields = (
        'failure_reason',
        'file',
    )


@admin.register(GeometryEntry)
class GeometryEntryAdmin(OSMGeoAdmin):
    list_display = (
        '__str__',
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
        '__str__',
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

    def data_link(self, obj):
        return _link_url('geodata', 'geometry_archive', obj, 'archive_file')

    data_link.allow_tags = True
