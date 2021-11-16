from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.admin.mixins import (
    MODIFIABLE_FILTERS,
    TASK_EVENT_FILTERS,
    TASK_EVENT_READONLY,
    GeoAdminInline,
    reprocess,
)
from rgd_3d.models import Mesh3D, Mesh3DSpatial


class Mesh3DSpatialInline(GeoAdminInline):
    model = Mesh3DSpatial
    fk_name = 'source'
    list_display = (
        'pk',
        'modified',
        'created',
        'crs',
    )
    readonly_fields = (
        'modified',
        'created',
    )
    modifiable = False  # To still show the footprint and outline


@admin.register(Mesh3D)
class Mesh3DAdmin(OSMGeoAdmin):
    list_display = (
        'pk',
        'name',
        'status',
        'modified',
        'created',
        # 'data_link',
        # 'data_link_vtp',
    )
    readonly_fields = (
        'modified',
        'created',
    ) + TASK_EVENT_READONLY
    actions = (reprocess,)
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS
    inlines = (Mesh3DSpatialInline,)
    extra = 0
