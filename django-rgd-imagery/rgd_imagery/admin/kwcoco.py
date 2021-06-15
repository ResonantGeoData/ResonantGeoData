from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.admin.mixins import MODIFIABLE_FILTERS, TASK_EVENT_FILTERS, TASK_EVENT_READONLY, reprocess
from rgd_imagery.models import KWCOCOArchive


@admin.register(KWCOCOArchive)
class KWCOCOArchiveAdmin(OSMGeoAdmin):
    list_display = (
        'pk',
        'name',
        'status',
        'modified',
        'created',
    )
    readonly_fields = ('image_set',) + TASK_EVENT_READONLY
    actions = (reprocess,)
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS
