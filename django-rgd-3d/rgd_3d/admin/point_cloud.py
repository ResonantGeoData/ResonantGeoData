from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.admin.mixins import (
    MODIFIABLE_FILTERS,
    TASK_EVENT_FILTERS,
    TASK_EVENT_READONLY,
    _FileGetNameMixin,
    reprocess,
)
from rgd_3d.models import PointCloudEntry, PointCloudFile, PointCloudMetaEntry


@admin.register(PointCloudFile)
class PointCloudFileAdmin(OSMGeoAdmin, _FileGetNameMixin):
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


class PointCloudMetaEntryInline(admin.StackedInline):
    model = PointCloudMetaEntry
    fk_name = 'parent_point_cloud'
    list_display = (
        'pk',
        'modified',
        'created',
        'crs',
    )
    readonly_fields = (
        'modified',
        'created',
        'parent_point_cloud',
    )
    modifiable = False  # To still show the footprint and outline


@admin.register(PointCloudEntry)
class PointCloudEntryAdmin(OSMGeoAdmin):
    list_display = (
        'pk',
        'modified',
        'created',
        'data_link',
    )
    readonly_fields = (
        'modified',
        'created',
    )
    inlines = (PointCloudMetaEntryInline,)
    list_filter = MODIFIABLE_FILTERS
