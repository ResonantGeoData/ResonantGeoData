from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from .models.dataset import Dataset
from .models.raster.base import RasterEntry, RasterFile
from .models.geometry.base import GeometryEntry, GeometryArchive

SPATIAL_ENTRY_FILTERS = ('acquisition_date', 'modified',)


@admin.register(Dataset)
class DatasetAdmin(OSMGeoAdmin):
    list_display = ('id', 'name',)


@admin.register(RasterEntry)
class RasterEntryAdmin(OSMGeoAdmin):
    list_display = ('__str__', 'modified',)
    readonly_fields = ('resolution', 'n_bands',)#'thumbnail')
    exclude = ('raster',)
    list_filter = SPATIAL_ENTRY_FILTERS + ('instrumentation',)


@admin.register(RasterFile)
class RasterFileAdmin(OSMGeoAdmin):
    list_display = ('__str__', 'modified',)
    readonly_fields = ('raster_entry',)


@admin.register(GeometryEntry)
class GeometryEntryAdmin(OSMGeoAdmin):
    list_display = ('__str__', 'modified',)
    list_filter = SPATIAL_ENTRY_FILTERS


@admin.register(GeometryArchive)
class GeometryArchiveAdmin(OSMGeoAdmin):
    list_display = ('__str__', 'modified',)
    readonly_fields = ('geometry_entry',)
