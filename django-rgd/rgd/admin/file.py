from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.models import ChecksumFile

from .mixins import MODIFIABLE_FILTERS, TASK_EVENT_FILTERS, TASK_EVENT_READONLY, reprocess


def validate_checksum(modeladmin, request, queryset):
    for file in queryset.all():
        file.validate_checksum = True
        file.save()


@admin.register(ChecksumFile)
class ChecksumFileAdmin(OSMGeoAdmin):
    list_display = (
        'pk',
        'name',
        'type',
        'status',
        'created',
        'created_by',
        'modified',
        'collection',
        'data_link',
    )
    readonly_fields = (
        'checksum',
        'last_validation',
    ) + TASK_EVENT_READONLY
    actions = (
        reprocess,
        validate_checksum,
    )
    list_filter = (
        MODIFIABLE_FILTERS
        + TASK_EVENT_FILTERS
        + (
            'type',
            'collection',
            'created_by',
        )
    )
