from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from .models.dataset import Dataset
from .models.geometry.base import GeometryArchive, GeometryEntry
from .models.raster.base import BandMetaEntry, ConvertedRasterFile, RasterEntry, RasterFile

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


@admin.register(RasterFile)
class RasterFileAdmin(OSMGeoAdmin):
    list_display = (
        '__str__',
        'modified',
    )
    readonly_fields = ('failure_reason', 'modified', 'created', 'checksum')


@admin.register(ConvertedRasterFile)
class ConvertedRasterFileAdmin(OSMGeoAdmin):
    list_display = (
        '__str__',
        'modified',
        'source_raster',
    )
    readonly_fields = (
        'failure_reason',
        'converted_file',
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
    )


@admin.register(GeometryArchive)
class GeometryArchiveAdmin(OSMGeoAdmin):
    list_display = (
        '__str__',
        'modified',
    )
    readonly_fields = (
        'geometry_entry',
        'failure_reason',
        'modified',
        'created',
    )
