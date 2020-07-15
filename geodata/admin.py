from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from rgd.utility import _link_url
from .models.dataset import Dataset
from .models.geometry.base import GeometryArchive, GeometryEntry
from .models.raster.annotation import Annotation
from .models.raster.base import BandMetaEntry, ConvertedRasterFile, RasterEntry
from .models.raster.ifiles import RasterFile


SPATIAL_ENTRY_FILTERS = (
    'acquisition_date',
    'modified',
)


@admin.register(Dataset)
class DatasetAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
    )


@admin.register(RasterEntry)
class RasterEntryAdmin(OSMGeoAdmin):
    list_display = (
        '__str__',
        'modified',
    )
    readonly_fields = (
        'number_of_bands',
        'footprint',
        'raster_file',
        'crs',
        'origin',
        'extent',
        'resolution',
        'height',
        'width',
        'driver',
        'metadata',
        'transform',
        'modified',
        'created',
    )  # 'thumbnail')
    list_filter = SPATIAL_ENTRY_FILTERS + ('instrumentation', 'number_of_bands', 'driver', 'crs')


@admin.register(BandMetaEntry)
class BandMetaEntryAdmin(OSMGeoAdmin):
    list_display = (
        '__str__',
        'modified',
        # 'parent_raster',  # TODO: this prevents the list view from working
    )
    readonly_fields = (
        'mean',
        'max',
        'min',
        'modified',
        'created',
        'parent_raster',
        'std',
        'nodata_value',
        'dtype',
    )
    list_filter = (
        'parent_raster',
        'interpretation',
        'dtype',
    )


@admin.register(Annotation)
class AnnotationAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'caption',
    )


@admin.register(RasterFile)
class RasterFileAdmin(OSMGeoAdmin):
    list_display = (
        '__str__',
        'modified',
        'data_link',
    )
    readonly_fields = ('failure_reason', 'modified', 'created', 'checksum', 'last_validation')

    def data_link(self, obj):
        return _link_url('geodata', 'raster_file', obj, 'raster_file')

    data_link.allow_tags = True


@admin.register(ConvertedRasterFile)
class ConvertedRasterFileAdmin(OSMGeoAdmin):
    list_display = (
        '__str__',
        'modified',
        'source_raster',
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
