from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.admin.mixins import (
    MODIFIABLE_FILTERS,
    TASK_EVENT_FILTERS,
    TASK_EVENT_READONLY,
    _FileGetNameMixin,
    reprocess,
)
from rgd_fmv.models import FMVEntry, FMVFile


class FMVEntryInline(admin.StackedInline):
    model = FMVEntry
    fk_name = 'fmv_file'
    list_display = (
        'pk',
        'name',
        'fmv_file',
        'modified',
        'created',
    )
    readonly_fields = (
        'modified',
        'created',
    )


@admin.register(FMVFile)
class FMVFileAdmin(OSMGeoAdmin, _FileGetNameMixin):
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
    inlines = (FMVEntryInline,)
    actions = (reprocess,)
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS
