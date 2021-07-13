from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.admin.mixins import (
    MODIFIABLE_FILTERS,
    SPATIAL_ENTRY_FILTERS,
    TASK_EVENT_FILTERS,
    TASK_EVENT_READONLY,
    reprocess,
)
from rgd_imagery.models import Raster, RasterMeta
from rgd_imagery.tasks import jobs


def reprocess_rastermeta(modeladmin, request, queryset):
    """Trigger the save event task for each entry."""
    for entry in queryset.all():
        entry.parent_raster.save()


def generate_valid_data_footprint(modeladmin, request, queryset):
    """Generate a valid data footprint for each raster."""
    for rast in queryset.all():
        jobs.task_populate_raster_footprint.delay(rast.id)


def generate_valid_data_footprint_rastermeta(modeladmin, request, queryset):
    """Generate a valid data footprint for each raster."""
    for entry in queryset.all():
        jobs.task_populate_raster_footprint.delay(entry.parent_raster.id)


def generate_outline(modeladmin, request, queryset):
    """Generate a the outline for each raster."""
    for rast in queryset.all():
        jobs.task_populate_raster_outline.delay(rast.id)


def clean_empty_rasters(modeladmin, request, queryset):
    """Delete if associated `ImageSet` is empty."""
    for raster in queryset.all():
        if len(raster.image_set.images) < 1:
            raster.image_set.delete()


@admin.register(RasterMeta)
class RasterMetaAdmin(OSMGeoAdmin):
    list_display = (
        'pk',
        'name',
        'acquisition_date',
        'modified',
        'created',
    )
    readonly_fields = (
        'crs',
        'origin',
        'extent',
        'resolution',
        'transform',
        'parent_raster',
        'modified',
        'created',
    )
    actions = (
        reprocess_rastermeta,
        generate_valid_data_footprint_rastermeta,
    )
    list_filter = SPATIAL_ENTRY_FILTERS + MODIFIABLE_FILTERS

    modifiable = False  # To still show the footprint and outline


@admin.register(Raster)
class RasterAdmin(OSMGeoAdmin):
    list_display = (
        'pk',
        'name',
        'status',
        'count',
        'modified',
        'created',
    )
    readonly_fields = (
        'modified',
        'created',
    ) + TASK_EVENT_READONLY
    actions = (
        reprocess,
        generate_valid_data_footprint,
        clean_empty_rasters,
    )
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS
