from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.admin.mixins import MODIFIABLE_FILTERS, TASK_EVENT_FILTERS, TASK_EVENT_READONLY, reprocess
from rgd_imagery.models import ProcessedImage, ProcessedImageGroup


class ProcessedImageAdmin(admin.StackedInline):
    model = ProcessedImage
    fk_name = 'group'
    extra = 0
    list_display = (
        'pk',
        'status',
        'modified',
        'created',
    )
    readonly_fields = MODIFIABLE_FILTERS + TASK_EVENT_READONLY
    actions = (reprocess,)
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS


@admin.register(ProcessedImageGroup)
class ProcessedImageGroupAdmin(OSMGeoAdmin):
    list_display = (
        'pk',
        'process_type',
        'modified',
        'created',
    )
    readonly_fields = MODIFIABLE_FILTERS
    actions = (reprocess,)
    list_filter = ('process_type',) + MODIFIABLE_FILTERS
    inlines = (ProcessedImageAdmin,)
