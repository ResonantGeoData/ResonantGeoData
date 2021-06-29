from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.admin.mixins import MODIFIABLE_FILTERS, TASK_EVENT_FILTERS, TASK_EVENT_READONLY, reprocess
from rgd_imagery.models import ConvertedImage, RegionImage


@admin.register(ConvertedImage)
class ConvertedImageAdmin(OSMGeoAdmin):
    list_display = (
        'pk',
        'source_image',
        'status',
        'modified',
        'created',
    )
    readonly_fields = ('processed_image',) + TASK_EVENT_READONLY
    actions = (reprocess,)
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS


@admin.register(RegionImage)
class RegionImageAdmin(OSMGeoAdmin):
    list_display = (
        'pk',
        'source_image',
        'sample_type',
        'status',
        'modified',
        'created',
    )
    readonly_fields = ('processed_image',) + TASK_EVENT_READONLY
    actions = (reprocess,)
    list_filter = ('sample_type',) + MODIFIABLE_FILTERS + TASK_EVENT_FILTERS
