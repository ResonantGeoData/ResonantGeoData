from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.admin.mixins import (
    MODIFIABLE_FILTERS,
    TASK_EVENT_FILTERS,
    TASK_EVENT_READONLY,
    GeoAdminInline,
    reprocess,
)
from rgd_3d.models import Tiles3D, Tiles3DMeta


class Tiles3DMetaInline(GeoAdminInline):
    model = Tiles3DMeta
    fk_name = 'source'
    readonly_fields = (
        'modified',
        'created',
    )
    modifiable = False  # To still show the footprint and outline


@admin.register(Tiles3D)
class Tiles3DAdmin(OSMGeoAdmin):
    list_display = (
        'pk',
        'name',
        'status',
        'modified',
        'created',
    )
    readonly_fields = (
        'modified',
        'created',
    ) + TASK_EVENT_READONLY
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS
    actions = (reprocess,)
    inlines = (Tiles3DMetaInline,)
    extra = 0
