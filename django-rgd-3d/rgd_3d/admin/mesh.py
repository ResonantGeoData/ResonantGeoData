from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.admin.mixins import (
    MODIFIABLE_FILTERS,
    TASK_EVENT_FILTERS,
    TASK_EVENT_READONLY,
    _FileGetNameMixin,
    reprocess,
)
from rgd_3d.models import Mesh3D, Mesh3DMeta, Mesh3DSpatial


@admin.register(Mesh3D)
class Mesh3DAdmin(OSMGeoAdmin, _FileGetNameMixin):
    list_display = (
        'pk',
        'get_name',
        'status',
        'modified',
        'created',
        'data_link',
    )
    readonly_fields = (
        'modified',
        'created',
    ) + TASK_EVENT_READONLY
    actions = (reprocess,)
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS


@admin.register(Mesh3DSpatial)
class Mesh3DSpatialAdmin(OSMGeoAdmin):
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


@admin.register(Mesh3DMeta)
class Mesh3DMetaAdmin(OSMGeoAdmin):
    list_display = (
        'pk',
        'modified',
        'created',
        'data_link',
    )
    readonly_fields = (
        'source',
        'modified',
        'created',
    )
    list_filter = MODIFIABLE_FILTERS
