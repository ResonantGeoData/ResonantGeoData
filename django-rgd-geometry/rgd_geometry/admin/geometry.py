from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.admin.mixins import (
    MODIFIABLE_FILTERS,
    SPATIAL_ENTRY_FILTERS,
    TASK_EVENT_FILTERS,
    TASK_EVENT_READONLY,
    _FileGetNameMixin,
    reprocess,
)
from rgd_geometry.models import GeometryArchive, GeometryEntry


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
    list_filter = MODIFIABLE_FILTERS + SPATIAL_ENTRY_FILTERS
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
    actions = (reprocess,)
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS
