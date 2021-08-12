from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.admin.mixins import MODIFIABLE_FILTERS, TASK_EVENT_FILTERS, TASK_EVENT_READONLY, reprocess
from rgd_imagery.models import ProcessedImage


@admin.register(ProcessedImage)
class ProcessedImageAdmin(OSMGeoAdmin):
    list_display = (
        'pk',
        'source_image',
        'status',
        'modified',
        'created',
    )
    readonly_fields = TASK_EVENT_READONLY
    actions = (reprocess,)
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS
