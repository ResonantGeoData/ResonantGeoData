from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from .models.dataset import Dataset
from .models.geometry.base import GeometryArchive, GeometryEntry
from .models.raster.base import ConvertedRasterFile, RasterEntry, RasterFile

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
    )  # 'thumbnail')
    exclude = ('raster',)
    list_filter = SPATIAL_ENTRY_FILTERS + ('instrumentation',)


@admin.register(RasterFile)
class RasterFileAdmin(OSMGeoAdmin):
    list_display = (
        '__str__',
        'modified',
    )
    readonly_fields = ('failure_reason',)


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


@admin.register(GeometryArchive)
class GeometryArchiveAdmin(OSMGeoAdmin):
    list_display = (
        '__str__',
        'modified',
    )
    readonly_fields = (
        'geometry_entry',
        'failure_reason',
    )
