from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.admin.mixins import (
    MODIFIABLE_FILTERS,
    TASK_EVENT_FILTERS,
    TASK_EVENT_READONLY,
    GeoAdminInline,
    _FileGetNameMixin,
    reprocess,
)
from rgd_fmv.models import FMV, FMVMeta


class FMVMetaInline(GeoAdminInline):
    model = FMVMeta
    fk_name = 'fmv_file'
    list_display = (
        'pk',
        'fmv_file',
        'modified',
        'created',
    )
    readonly_fields = (
        'modified',
        'created',
        'fmv_file',
    )


@admin.register(FMV)
class FMVAdmin(OSMGeoAdmin, _FileGetNameMixin):
    list_display = (
        'pk',
        'get_name',
        'status',
        'modified',
        'created',
        'fmv_data_link',
        'klv_data_link',
    )
    readonly_fields = (
        'modified',
        'created',
        'klv_file',
        'web_video_file',
        'frame_rate',
    ) + TASK_EVENT_READONLY
    inlines = (FMVMetaInline,)
    actions = (reprocess,)
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS
    raw_id_fields = ('file',)
